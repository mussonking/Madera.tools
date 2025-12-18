"""
MADERA MCP - identify_cra_document_type
HINTS Tool - Identifies CRA document types without full AI

Execution time: ~200ms per page
Technique: Limited OCR on specific zones + pattern matching
"""
from typing import Dict, Any, List, Tuple, Optional
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images
from PIL import Image
import pytesseract
import re
import logging

logger = logging.getLogger(__name__)


class CRADocumentDetector(BaseTool):
    """Identifies CRA (Canada Revenue Agency) document types"""

    # CRA document patterns
    DOCUMENT_PATTERNS = {
        'notice_of_assessment': [
            r'notice\s+of\s+assessment',
            r'avis\s+de\s+cotisation',
            r'noa\b',
            r'\bT1\s+General',
        ],
        'family_allowance': [
            r'canada\s+child\s+benefit',
            r'allocation\s+canadienne\s+pour\s+enfants',
            r'\bRC151\b',
            r'CCB',
        ],
        'gst_hst_credit': [
            r'GST/HST\s+credit',
            r'cr[ée]dit\s+(?:pour\s+la\s+)?TPS/TVH',
            r'\bRC151\b',
        ],
        'statement_of_account': [
            r'statement\s+of\s+account',
            r'[ée]tat\s+de\s+compte',
            r'balance\s+owing',
            r'solde\s+(?:[àa]\s+payer|d[ûu])',
        ],
        'tax_return': [
            r'income\s+tax\s+(?:and\s+benefit\s+)?return',
            r'd[ée]claration\s+de\s+revenus?',
            r'T1\s+General',
        ],
        'proof_of_income': [
            r'option\s+C\s+print',
            r'proof\s+of\s+income',
            r'revenue\s+statement',
        ],
    }

    # Keywords that strongly indicate CRA
    CRA_KEYWORDS = [
        'canada revenue agency',
        'agence du revenu du canada',
        'revenue canada',
        'revenu canada',
        'cra-arc',
    ]

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _extract_text_from_zone(self, image: Image.Image, zone: Tuple[int, int, int, int]) -> str:
        """
        Extract text from specific zone using OCR

        Args:
            image: PIL Image
            zone: (x, y, width, height) in pixels

        Returns:
            Extracted text
        """
        x, y, w, h = zone

        # Crop zone
        cropped = image.crop((x, y, x + w, y + h))

        # OCR with Tesseract
        try:
            text = pytesseract.image_to_string(cropped, lang='eng+fra', config='--psm 6')
            return text.lower().strip()
        except Exception as e:
            logger.warning(f"OCR failed for zone {zone}: {e}")
            return ""

    def _detect_cra_issuer(self, image: Image.Image) -> Tuple[bool, float]:
        """
        Detect if document is issued by CRA

        Returns:
            (is_cra, confidence)
        """
        width, height = image.size

        # Check top header (top 15% of page)
        header_zone = (0, 0, width, int(height * 0.15))
        header_text = self._extract_text_from_zone(image, header_zone)

        # Check for CRA keywords
        cra_matches = 0
        for keyword in self.CRA_KEYWORDS:
            if keyword in header_text:
                cra_matches += 1

        is_cra = cra_matches > 0
        confidence = min(cra_matches / 2.0, 0.95)

        return is_cra, confidence

    def _identify_document_type(self, image: Image.Image) -> Tuple[Optional[str], float, List[str]]:
        """
        Identify specific CRA document type

        Returns:
            (document_type, confidence, matched_patterns)
        """
        width, height = image.size

        # Define zones to check
        zones = {
            'header': (0, 0, width, int(height * 0.15)),
            'top_left': (0, 0, int(width * 0.4), int(height * 0.25)),
            'top_right': (int(width * 0.6), 0, int(width * 0.4), int(height * 0.25)),
            'center': (int(width * 0.25), int(height * 0.3), int(width * 0.5), int(height * 0.4)),
        }

        # Extract text from all zones
        zone_texts = {}
        for zone_name, zone_coords in zones.items():
            zone_texts[zone_name] = self._extract_text_from_zone(image, zone_coords)

        # Combine all text
        combined_text = ' '.join(zone_texts.values())

        # Match against document patterns
        best_match = None
        best_score = 0
        matched_patterns = []

        for doc_type, patterns in self.DOCUMENT_PATTERNS.items():
            score = 0
            type_matches = []

            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    score += 1
                    type_matches.append(pattern)

            if score > best_score:
                best_score = score
                best_match = doc_type
                matched_patterns = type_matches

        # Calculate confidence based on number of matches
        if best_match and best_score > 0:
            # Confidence increases with more pattern matches
            confidence = min(0.5 + (best_score * 0.15), 0.95)
            return best_match, confidence, matched_patterns
        else:
            return None, 0.0, []

    def _detect_form_number(self, image: Image.Image) -> Optional[str]:
        """
        Detect CRA form number (e.g., T1, RC151, T4)

        Returns:
            Form number or None
        """
        width, height = image.size

        # Form numbers are typically in top-right corner
        top_right = (int(width * 0.7), 0, int(width * 0.3), int(height * 0.15))
        text = self._extract_text_from_zone(image, top_right)

        # Common CRA form patterns
        form_patterns = [
            r'\b(T1)\b',
            r'\b(T4[A-Z]?)\b',
            r'\b(T5[A-Z]?)\b',
            r'\b(RC\d{3})\b',
            r'\b(T2202A?)\b',
            r'\b(RRSP)\b',
        ]

        for pattern in form_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return None

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Identify CRA document types in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "documents": [
                    {
                        "page": 1,
                        "type": "notice_of_assessment",
                        "issuer": "cra",
                        "form_number": "T1",
                        "confidence": 0.87
                    }
                ],
                "total_pages": 3
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images (lower DPI for speed, OCR doesn't need high res)
        images = convert_pdf_to_images(local_pdf, dpi=150)
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for CRA document detection")

        # Analyze each page
        documents = []

        for page_num, image in enumerate(images, start=1):
            # Check if CRA document
            is_cra, cra_confidence = self._detect_cra_issuer(image)

            if not is_cra:
                logger.debug(f"Page {page_num}: Not a CRA document")
                continue

            # Identify document type
            doc_type, type_confidence, patterns = self._identify_document_type(image)

            # Detect form number
            form_number = self._detect_form_number(image)

            # Overall confidence is combination of CRA detection and type detection
            overall_confidence = (cra_confidence * 0.4) + (type_confidence * 0.6)

            doc_info = {
                "page": page_num,
                "type": doc_type or "unknown_cra_document",
                "issuer": "cra",
                "form_number": form_number,
                "confidence": round(overall_confidence, 2),
                "matched_patterns": patterns
            }

            documents.append(doc_info)

            logger.info(
                f"Page {page_num}: CRA document detected - "
                f"{doc_type or 'unknown'} "
                f"(form: {form_number or 'N/A'}) "
                f"confidence: {overall_confidence:.2f}"
            )

        # Calculate overall confidence
        if documents:
            overall_confidence = sum(d["confidence"] for d in documents) / len(documents)
        else:
            overall_confidence = 0.85  # High confidence that there are NO CRA documents

        # Create hints message
        if documents:
            type_summary = {}
            for doc in documents:
                doc_type = doc["type"]
                type_summary[doc_type] = type_summary.get(doc_type, 0) + 1

            hints_message = "CRA documents detected: " + ", ".join([
                f"{count}x {doc_type}" for doc_type, count in type_summary.items()
            ])
        else:
            hints_message = "No CRA documents detected"

        logger.info(
            f"Detected {len(documents)} CRA documents out of {total_pages} pages "
            f"(confidence: {overall_confidence:.2f})"
        )

        return ToolResult(
            success=True,
            data={
                "documents": documents,
                "total_pages": total_pages
            },
            hints={
                "cra_documents": documents,
                "message": hints_message
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register identify_cra_document_type tool"""
    detector = CRADocumentDetector()

    @mcp_server.tool()
    async def identify_cra_document_type(presigned_url: str) -> Dict[str, Any]:
        """
        Identifies Canada Revenue Agency (CRA) document types using limited OCR.

        This tool uses OCR on specific zones (header, top corners) to detect
        CRA document types like Notice of Assessment, Family Allowance, GST/HST
        credit, Statement of Account, etc.

        Helps AI classify documents faster by providing hints about document type
        BEFORE full AI analysis.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "documents": [
                        {
                            "page": 1,
                            "type": "notice_of_assessment",
                            "issuer": "cra",
                            "form_number": "T1",
                            "confidence": 0.87,
                            "matched_patterns": ["notice of assessment", "T1 General"]
                        }
                    ],
                    "total_pages": 3
                },
                "hints": {
                    "cra_documents": [...],
                    "message": "CRA documents detected: 1x notice_of_assessment"
                },
                "confidence": 0.87,
                "execution_time_ms": 203
            }

        Detected types:
            - notice_of_assessment: Tax assessment from CRA
            - family_allowance: Canada Child Benefit (CCB)
            - gst_hst_credit: GST/HST credit notice
            - statement_of_account: Account balance statement
            - tax_return: T1 General tax return
            - proof_of_income: Option C print / proof of income

        Example usage:
            result = await identify_cra_document_type("https://minio/file.pdf?presigned=...")
            if result["hints"]["cra_documents"]:
                for doc in result["hints"]["cra_documents"]:
                    prompt += f"Page {doc['page']} is {doc['type']} from CRA"
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
