"""
MADERA MCP - extract_text_by_page
Core Tool - Extracts text from each page separately

Execution time: ~50ms
Technique: Direct text extraction (pypdf)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class PageTextExtractor(BaseTool):
    """Extracts text page-by-page from PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Extract text from each page separately

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with text per page
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Extract text
        reader = PdfReader(local_pdf)
        total_pages = len(reader.pages)

        pages_text = {}
        total_chars = 0

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            pages_text[page_num] = text
            total_chars += len(text)

        logger.info(
            f"Extracted {total_chars} characters from {total_pages} pages"
        )

        return ToolResult(
            success=True,
            data={
                "pages": pages_text,
                "total_pages": total_pages,
                "total_characters": total_chars,
                "pages_with_text": sum(1 for t in pages_text.values() if len(t) > 0)
            },
            hints={
                "total_pages": total_pages,
                "pages_with_text": sum(1 for t in pages_text.values() if len(t) > 0),
                "message": f"{total_pages} pages extracted"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register extract_text_by_page tool"""
    extractor = PageTextExtractor()

    @mcp_server.tool()
    async def extract_text_by_page(presigned_url: str) -> Dict[str, Any]:
        """
        Extracts text from each page separately.

        This tool returns a dictionary with text for each page number.
        Useful when you need to analyze pages individually.

        Args:
            presigned_url: MinIO presigned URL for the PDF

        Returns:
            {
                "success": true,
                "data": {
                    "pages": {
                        1: "Text from page 1...",
                        2: "Text from page 2...",
                        3: "Text from page 3..."
                    },
                    "total_pages": 3,
                    "total_characters": 5000,
                    "pages_with_text": 3
                },
                "hints": {
                    "total_pages": 3,
                    "pages_with_text": 3,
                    "message": "3 pages extracted"
                },
                "confidence": 1.0,
                "execution_time_ms": 52
            }

        Example usage:
            result = await extract_text_by_page("https://minio/file.pdf?presigned=...")
            for page_num, text in result["data"]["pages"].items():
                print(f"Page {page_num}: {len(text)} chars")
        """
        result = await extractor.execute(presigned_url=presigned_url)
        return result.model_dump()
