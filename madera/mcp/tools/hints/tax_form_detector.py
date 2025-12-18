"""
MADERA MCP - detect_tax_form_type
HINTS Tool - Detects Canadian tax form types (T4, T1, T5, etc.)

Execution time: ~100ms per page
Technique: OCR on top-right corner + layout pattern matching
"""
from typing import Dict, Any, List, Tuple, Optional
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images
from PIL import Image
import pytesseract
import re
import logging

logger = logging.getLogger(__name__)


class TaxFormDetector(BaseTool):
    """Detects Canadian tax form types"""

    # Tax form patterns and their characteristics
    TAX_FORMS = {
        'T4': {
            'patterns': [r'\bT4\b', r'Statement of Remuneration Paid'],
            'keywords': ['employment income', 'income tax deducted', 'cpp', 'ei'],
            'issuer': 'employer',
        },
        'T4A': {
            'patterns': [r'\bT4A\b', r'Statement of Pension'],
            'keywords': ['pension', 'other income', 'annuities'],
            'issuer': 'various',
        },
        'T4E': {
            'patterns': [r'\bT4E\b', r'Statement of Employment Insurance'],
            'keywords': ['employment insurance', 'benefits paid', 'ei'],
            'issuer': 'service_canada',
        },
        'T5': {
            'patterns': [r'\bT5\b', r'Statement of Investment Income'],
            'keywords': ['interest', 'dividends', 'investment income'],
            'issuer': 'financial_institution',
        },
        'T5007': {
            'patterns': [r'\bT5007\b', r'Statement of Benefits'],
            'keywords': ['social assistance', 'benefits', "workers' compensation"],
            'issuer': 'government',
        },
        'T1': {
            'patterns': [r'\bT1\s+General\b', r'Income Tax and Benefit Return'],
            'keywords': ['tax return', 'total income', 'taxable income', 'federal tax'],
            'issuer': 'taxpayer',
        },
        'T2202': {
            'patterns': [r'\bT2202A?\b', r'Tuition and Enrolment Certificate'],
            'keywords': ['tuition', 'education', 'eligible fees'],
            'issuer': 'educational_institution',
        },
        'T3': {
            'patterns': [r'\bT3\b', r'Statement of Trust Income'],
            'keywords': ['trust', 'allocations', 'capital gains'],
            'issuer': 'trust',
        },
        'RL-1': {
            'patterns': [r'\bRL-?1\b', r'Relev[ée]\s+1'],
            'keywords': ['revenu', 'emploi', 'quebec'],
            'issuer': 'employer_quebec',
        },
        'RL-2': {
            'patterns': [r'\bRL-?2\b', r'Relev[ée]\s+2'],
            'keywords': ['revenus de placements', 'int[ée]r[êe]ts', 'quebec'],
            'issuer': 'financial_institution_quebec',
        },
    }

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"  # Mortgage-specific

    def _extract_form_code(self, image: Image.Image) -> Optional[str]:
        """
        Extract form code from top-right corner (standard location)

        Returns:
            Form code (e.g., "T4", "T5") or None
        """
        width, height = image.size

        # Form code is typically in top-right corner
        # Check 30% width, 15% height
        zone = (int(width * 0.7), 0, int(width * 0.3), int(height * 0.15))

        x, y, w, h = zone
        cropped = image.crop((x, y, x + w, y + h))

        try:
            # Use OCR with single block mode
            text = pytesseract.image_to_string(
                cropped,
                lang='eng+fra',
                config='--psm 6 --oem 3'
            )
            text = text.upper().strip()

            # Look for form codes
            for form_code in self.TAX_FORMS.keys():
                # Flexible pattern matching
                pattern = form_code.replace('-', r'-?')  # Allow with/without hyphen
                if re.search(rf'\b{pattern}\b', text):
                    return form_code

            return None

        except Exception as e:
            logger.warning(f"OCR failed for form code extraction: {e}")
            return None

    def _detect_form_by_content(self, image: Image.Image) -> Tuple[Optional[str], float, List[str]]:
        """
        Detect form type by analyzing content patterns

        Returns:
            (form_type, confidence, matched_keywords)
        """
        width, height = image.size

        # Check top third of document (header + main content area)
        content_zone = (0, 0, width, int(height * 0.4))

        x, y, w, h = content_zone
        cropped = image.crop((x, y, x + w, y + h))

        try:
            text = pytesseract.image_to_string(
                cropped,
                lang='eng+fra',
                config='--psm 6'
            ).lower()

            best_match = None
            best_score = 0
            matched_keywords = []

            # Score each form type
            for form_type, form_info in self.TAX_FORMS.items():
                score = 0
                keywords_found = []

                # Check patterns
                for pattern in form_info['patterns']:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 2
                        keywords_found.append(pattern)

                # Check keywords
                for keyword in form_info['keywords']:
                    if keyword.lower() in text:
                        score += 1
                        keywords_found.append(keyword)

                if score > best_score:
                    best_score = score
                    best_match = form_type
                    matched_keywords = keywords_found

            if best_match and best_score > 0:
                # Confidence based on score
                confidence = min(0.3 + (best_score * 0.15), 0.92)
                return best_match, confidence, matched_keywords
            else:
                return None, 0.0, []

        except Exception as e:
            logger.warning(f"Content analysis failed: {e}")
            return None, 0.0, []

    def _extract_year(self, image: Image.Image) -> Optional[int]:
        """
        Extract tax year from document

        Returns:
            Year (e.g., 2024) or None
        """
        width, height = image.size

        # Year is typically in header or near form code
        zones = [
            (int(width * 0.7), 0, int(width * 0.3), int(height * 0.15)),  # Top-right
            (0, 0, width, int(height * 0.1)),  # Top header
        ]

        for zone in zones:
            x, y, w, h = zone
            cropped = image.crop((x, y, x + w, y + h))

            try:
                text = pytesseract.image_to_string(cropped, config='--psm 6')

                # Look for 4-digit years (2020-2030)
                year_pattern = r'\b(202[0-9]|203[0])\b'
                match = re.search(year_pattern, text)

                if match:
                    return int(match.group(1))

            except Exception as e:
                logger.warning(f"Year extraction failed for zone {zone}: {e}")
                continue

        return None

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect tax form types in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "tax_forms": [
                    {
                        "page": 1,
                        "form_type": "T4",
                        "year": 2024,
                        "confidence": 0.94,
                        "issuer": "employer"
                    }
                ],
                "total_pages": 3
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images
        images = convert_pdf_to_images(local_pdf, dpi=200)  # Higher DPI for text clarity
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for tax form detection")

        # Analyze each page
        tax_forms = []

        for page_num, image in enumerate(images, start=1):
            # Method 1: Extract form code from top-right
            form_code = self._extract_form_code(image)

            # Method 2: Detect by content if form code not found
            if not form_code:
                form_code, content_confidence, keywords = self._detect_form_by_content(image)
                code_confidence = 0.0
            else:
                content_confidence = 0.0
                keywords = []
                code_confidence = 0.90  # High confidence for direct code match

            if not form_code:
                logger.debug(f"Page {page_num}: No tax form detected")
                continue

            # Extract year
            year = self._extract_year(image)

            # Calculate overall confidence
            # Form code detection is more reliable than content analysis
            if code_confidence > 0:
                overall_confidence = code_confidence
            else:
                overall_confidence = content_confidence

            # Boost confidence if year is detected
            if year:
                overall_confidence = min(overall_confidence + 0.05, 0.95)

            form_info = {
                "page": page_num,
                "form_type": form_code,
                "year": year,
                "confidence": round(overall_confidence, 2),
                "issuer": self.TAX_FORMS.get(form_code, {}).get('issuer', 'unknown'),
                "matched_keywords": keywords
            }

            tax_forms.append(form_info)

            logger.info(
                f"Page {page_num}: Tax form detected - "
                f"{form_code} "
                f"({year or 'year unknown'}) "
                f"confidence: {overall_confidence:.2f}"
            )

        # Calculate overall confidence
        if tax_forms:
            overall_confidence = sum(f["confidence"] for f in tax_forms) / len(tax_forms)
        else:
            overall_confidence = 0.80  # High confidence that there are NO tax forms

        # Create hints message
        if tax_forms:
            form_summary = {}
            for form in tax_forms:
                form_type = form["form_type"]
                form_summary[form_type] = form_summary.get(form_type, [])
                form_summary[form_type].append(form["page"])

            hints_message = "Tax forms detected: " + ", ".join([
                f"{form_type} (pages {pages})" for form_type, pages in form_summary.items()
            ])
        else:
            hints_message = "No tax forms detected"

        logger.info(
            f"Detected {len(tax_forms)} tax forms out of {total_pages} pages "
            f"(confidence: {overall_confidence:.2f})"
        )

        return ToolResult(
            success=True,
            data={
                "tax_forms": tax_forms,
                "total_pages": total_pages
            },
            hints={
                "tax_forms": tax_forms,
                "message": hints_message
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_tax_form_type tool"""
    detector = TaxFormDetector()

    @mcp_server.tool()
    async def detect_tax_form_type(presigned_url: str) -> Dict[str, Any]:
        """
        Detects Canadian tax form types (T4, T1, T5, RL-1, etc.) using OCR.

        This tool performs OCR on the top-right corner (standard form code location)
        and content analysis to identify tax forms. Supports both federal (T-series)
        and Quebec (RL-series) forms.

        Helps AI classify documents faster by providing hints about tax form types
        and years BEFORE full AI analysis.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "tax_forms": [
                        {
                            "page": 1,
                            "form_type": "T4",
                            "year": 2024,
                            "confidence": 0.94,
                            "issuer": "employer",
                            "matched_keywords": ["T4", "employment income"]
                        }
                    ],
                    "total_pages": 3
                },
                "hints": {
                    "tax_forms": [...],
                    "message": "Tax forms detected: T4 (pages [1]), T5 (pages [2])"
                },
                "confidence": 0.92,
                "execution_time_ms": 105
            }

        Supported forms:
            - T4: Employment income statement
            - T4A: Pension/other income
            - T4E: Employment insurance
            - T5: Investment income
            - T5007: Social assistance benefits
            - T1: Income tax return
            - T2202: Tuition certificate
            - T3: Trust income
            - RL-1: Quebec employment income
            - RL-2: Quebec investment income

        Example usage:
            result = await detect_tax_form_type("https://minio/file.pdf?presigned=...")
            if result["hints"]["tax_forms"]:
                for form in result["hints"]["tax_forms"]:
                    prompt += f"Page {form['page']} is {form['form_type']} for year {form['year']}"
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
