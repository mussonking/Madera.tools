"""
MADERA MCP - detect_blank_pages
HINTS Tool - Identifies blank/useless pages in PDFs

Execution time: ~50ms per page
Technique: Pixel variance + text density analysis
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images, is_image_blank
import logging

logger = logging.getLogger(__name__)


class BlankPageDetector(BaseTool):
    """Detects blank or near-blank pages in PDFs"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"  # Generic tool

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect blank pages in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "blank_pages": [3, 7, 12],
                "confidence_per_page": {3: 0.99, 7: 0.87, 12: 0.95},
                "total_pages": 15
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images (low DPI for speed)
        images = convert_pdf_to_images(local_pdf, dpi=150)
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for blank detection")

        # Detect blank pages
        blank_pages = []
        confidence_per_page = {}

        for page_num, image in enumerate(images, start=1):
            is_blank, confidence = is_image_blank(image)

            if is_blank:
                blank_pages.append(page_num)
                confidence_per_page[page_num] = round(confidence, 2)
                logger.debug(f"Page {page_num} detected as blank (confidence: {confidence:.2f})")

        # Calculate overall confidence
        if blank_pages:
            overall_confidence = sum(confidence_per_page.values()) / len(confidence_per_page)
        else:
            # High confidence that there are NO blank pages
            overall_confidence = 0.95

        logger.info(
            f"Detected {len(blank_pages)} blank pages out of {total_pages} "
            f"(confidence: {overall_confidence:.2f})"
        )

        return ToolResult(
            success=True,
            data={
                "blank_pages": blank_pages,
                "confidence_per_page": confidence_per_page,
                "total_pages": total_pages
            },
            hints={
                "blank_pages": blank_pages,
                "total_pages": total_pages,
                "message": f"Skip pages {blank_pages}" if blank_pages else "No blank pages detected"
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_blank_pages tool"""
    detector = BlankPageDetector()

    @mcp_server.tool()
    async def detect_blank_pages(presigned_url: str) -> Dict[str, Any]:
        """
        Detects blank or near-blank pages in a PDF to skip during AI analysis.

        This tool uses pixel variance and text density analysis to identify
        pages that contain no meaningful content. Helps AI save tokens by
        skipping useless pages.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "blank_pages": [3, 7, 12],
                    "confidence_per_page": {3: 0.99, 7: 0.87, 12: 0.95},
                    "total_pages": 15
                },
                "hints": {
                    "blank_pages": [3, 7, 12],
                    "message": "Skip pages [3, 7, 12]"
                },
                "confidence": 0.94,
                "execution_time_ms": 47
            }

        Example usage:
            result = await detect_blank_pages("https://minio/file.pdf?presigned=...")
            if result["hints"]["blank_pages"]:
                # Tell Gemini Flash to skip these pages
                prompt += f"Skip pages {result['hints']['blank_pages']} (blank)"
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
