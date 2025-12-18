"""
MADERA MCP - detect_fiscal_year
HINTS Tool - Detects fiscal year in tax/financial documents

Execution time: ~80ms per page
Technique: Limited OCR on probable zones + date pattern matching
"""
from typing import Dict, Any, List, Tuple, Optional
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images
from PIL import Image
import pytesseract
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FiscalYearDetector(BaseTool):
    """Detects fiscal year in documents"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _extract_years_from_text(self, text: str) -> List[Tuple[int, str, float]]:
        """
        Extract years from text with context and confidence

        Returns:
            List of (year, context, confidence)
        """
        findings = []

        # Pattern 1: "Tax Year 2024" / "Année d'imposition 2024"
        pattern1 = r'(?:tax\s+year|ann[ée]e\s+d.imposition|fiscal\s+year|taxation\s+year)\s*:?\s*(\d{4})'
        matches = re.finditer(pattern1, text, re.IGNORECASE)
        for match in matches:
            year = int(match.group(1))
            findings.append((year, "tax_year_label", 0.95))

        # Pattern 2: "For the year 2024" / "Pour l'année 2024"
        pattern2 = r'(?:for\s+the\s+year|pour\s+l.ann[ée]e)\s+(\d{4})'
        matches = re.finditer(pattern2, text, re.IGNORECASE)
        for match in matches:
            year = int(match.group(1))
            findings.append((year, "for_the_year", 0.90))

        # Pattern 3: "2024 Tax Return" / "Déclaration de revenus 2024"
        pattern3 = r'(\d{4})\s+(?:tax\s+return|income\s+tax|d[ée]claration|notice|avis)'
        matches = re.finditer(pattern3, text, re.IGNORECASE)
        for match in matches:
            year = int(match.group(1))
            findings.append((year, "year_before_label", 0.85))

        # Pattern 4: Date ranges "January 1, 2024 to December 31, 2024"
        pattern4 = r'(?:january|janvier)\s+\d+,?\s+(\d{4})\s+(?:to|[àa])\s+(?:december|d[ée]cembre)\s+\d+,?\s+\d{4}'
        matches = re.finditer(pattern4, text, re.IGNORECASE)
        for match in matches:
            year = int(match.group(1))
            findings.append((year, "date_range", 0.92))

        # Pattern 5: "As of December 31, 2024"
        pattern5 = r'as\s+of\s+(?:december|d[ée]cembre)\s+\d+,?\s+(\d{4})'
        matches = re.finditer(pattern5, text, re.IGNORECASE)
        for match in matches:
            year = int(match.group(1))
            findings.append((year, "as_of_date", 0.88))

        # Pattern 6: Just a 4-digit year (2020-2030)
        pattern6 = r'\b(202[0-9]|203[0])\b'
        matches = re.finditer(pattern6, text)
        for match in matches:
            year = int(match.group(1))
            findings.append((year, "standalone_year", 0.60))

        return findings

    def _detect_fiscal_year_in_zone(self, image: Image.Image, zone: Tuple[int, int, int, int], zone_name: str) -> List[Tuple[int, str, float]]:
        """
        Detect fiscal year in specific zone

        Args:
            image: PIL Image
            zone: (x, y, width, height)
            zone_name: Name of zone for logging

        Returns:
            List of (year, context, confidence)
        """
        x, y, w, h = zone

        # Crop zone
        cropped = image.crop((x, y, x + w, y + h))

        try:
            # OCR
            text = pytesseract.image_to_string(
                cropped,
                lang='eng+fra',
                config='--psm 6'
            )

            # Extract years
            findings = self._extract_years_from_text(text)

            # Boost confidence for findings in specific zones
            if zone_name == "header":
                findings = [(y, ctx, min(conf + 0.05, 0.98)) for y, ctx, conf in findings]
            elif zone_name == "top_right":
                findings = [(y, ctx, min(conf + 0.03, 0.98)) for y, ctx, conf in findings]

            return findings

        except Exception as e:
            logger.warning(f"OCR failed for zone {zone_name}: {e}")
            return []

    def _validate_year(self, year: int) -> bool:
        """
        Validate if year is reasonable for fiscal year

        Returns:
            True if year is in reasonable range
        """
        current_year = datetime.now().year

        # Accept years from 10 years ago to 2 years in the future
        return (current_year - 10) <= year <= (current_year + 2)

    def _aggregate_year_findings(self, all_findings: List[Tuple[int, str, float]]) -> Tuple[Optional[int], float]:
        """
        Aggregate all findings and determine most likely fiscal year

        Returns:
            (year, confidence)
        """
        if not all_findings:
            return None, 0.0

        # Group by year
        year_scores = {}

        for year, context, confidence in all_findings:
            # Validate year
            if not self._validate_year(year):
                continue

            if year not in year_scores:
                year_scores[year] = []

            year_scores[year].append((context, confidence))

        if not year_scores:
            return None, 0.0

        # Find year with highest combined confidence
        best_year = None
        best_score = 0

        for year, scores in year_scores.items():
            # Calculate weighted score (more detections = higher confidence)
            # But cap the benefit of multiple detections
            avg_confidence = sum(s[1] for s in scores) / len(scores)
            detection_count_bonus = min(len(scores) * 0.05, 0.15)
            total_score = min(avg_confidence + detection_count_bonus, 0.98)

            if total_score > best_score:
                best_score = total_score
                best_year = year

        return best_year, best_score

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect fiscal year in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "fiscal_years": {
                    1: {"year": 2024, "confidence": 0.94},
                    2: {"year": 2023, "confidence": 0.88}
                },
                "most_common_year": 2024,
                "total_pages": 3
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images (lower DPI for speed)
        images = convert_pdf_to_images(local_pdf, dpi=150)
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for fiscal year detection")

        # Analyze each page
        fiscal_years = {}

        for page_num, image in enumerate(images, start=1):
            width, height = image.size

            # Define zones to check (prioritize areas where years are commonly found)
            zones = {
                'header': (0, 0, width, int(height * 0.12)),
                'top_right': (int(width * 0.65), 0, int(width * 0.35), int(height * 0.15)),
                'top_left': (0, 0, int(width * 0.35), int(height * 0.15)),
                'center_top': (int(width * 0.25), int(height * 0.1), int(width * 0.5), int(height * 0.15)),
            }

            # Collect findings from all zones
            page_findings = []

            for zone_name, zone_coords in zones.items():
                findings = self._detect_fiscal_year_in_zone(image, zone_coords, zone_name)
                page_findings.extend(findings)

            # Aggregate findings for this page
            year, confidence = self._aggregate_year_findings(page_findings)

            if year:
                fiscal_years[page_num] = {
                    "year": year,
                    "confidence": round(confidence, 2)
                }

                logger.info(
                    f"Page {page_num}: Fiscal year {year} detected "
                    f"(confidence: {confidence:.2f})"
                )
            else:
                logger.debug(f"Page {page_num}: No fiscal year detected")

        # Find most common year
        if fiscal_years:
            year_counts = {}
            for page_info in fiscal_years.values():
                year = page_info["year"]
                year_counts[year] = year_counts.get(year, 0) + 1

            most_common_year = max(year_counts.keys(), key=lambda y: year_counts[y])

            # Calculate overall confidence
            overall_confidence = sum(
                info["confidence"] for info in fiscal_years.values()
            ) / len(fiscal_years)
        else:
            most_common_year = None
            overall_confidence = 0.70  # Moderate confidence that there are NO fiscal years

        # Create hints message
        if fiscal_years:
            if most_common_year:
                hints_message = f"Fiscal year {most_common_year} detected across {len(fiscal_years)} pages"
            else:
                hints_message = f"Fiscal years detected on {len(fiscal_years)} pages"
        else:
            hints_message = "No fiscal years detected"

        logger.info(
            f"Detected fiscal years on {len(fiscal_years)}/{total_pages} pages. "
            f"Most common: {most_common_year} "
            f"(confidence: {overall_confidence:.2f})"
        )

        return ToolResult(
            success=True,
            data={
                "fiscal_years": fiscal_years,
                "most_common_year": most_common_year,
                "total_pages": total_pages
            },
            hints={
                "fiscal_years": fiscal_years,
                "most_common_year": most_common_year,
                "message": hints_message
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_fiscal_year tool"""
    detector = FiscalYearDetector()

    @mcp_server.tool()
    async def detect_fiscal_year(presigned_url: str) -> Dict[str, Any]:
        """
        Detects fiscal year in tax and financial documents using limited OCR.

        This tool performs OCR on specific zones (header, top corners) to detect
        fiscal years from patterns like "Tax Year 2024", "For the year 2024",
        date ranges, etc.

        Helps AI classify documents faster by providing year context BEFORE
        full AI analysis.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "fiscal_years": {
                        1: {"year": 2024, "confidence": 0.94},
                        2: {"year": 2023, "confidence": 0.88}
                    },
                    "most_common_year": 2024,
                    "total_pages": 3
                },
                "hints": {
                    "fiscal_years": {...},
                    "most_common_year": 2024,
                    "message": "Fiscal year 2024 detected across 2 pages"
                },
                "confidence": 0.91,
                "execution_time_ms": 82
            }

        Detection patterns:
            - "Tax Year 2024" / "Année d'imposition 2024"
            - "For the year 2024" / "Pour l'année 2024"
            - "2024 Tax Return"
            - Date ranges: "January 1, 2024 to December 31, 2024"
            - "As of December 31, 2024"
            - Standalone years in header/title areas

        Example usage:
            result = await detect_fiscal_year("https://minio/file.pdf?presigned=...")
            if result["hints"]["most_common_year"]:
                year = result["hints"]["most_common_year"]
                prompt += f"Documents are for fiscal year {year}"
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
