"""
MADERA MCP - count_pages
Core Tool - Counts exact number of pages in a PDF

Execution time: ~10ms
Technique: Direct PDF parsing (pypdf)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class PageCounter(BaseTool):
    """Counts pages in a PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Count pages in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with exact page count
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Count pages
        reader = PdfReader(local_pdf)
        page_count = len(reader.pages)

        logger.info(f"PDF has {page_count} pages")

        return ToolResult(
            success=True,
            data={
                "page_count": page_count,
                "file_size": local_pdf.stat().st_size,
            },
            hints={
                "page_count": page_count,
                "message": f"Document has {page_count} page{'s' if page_count != 1 else ''}"
            },
            confidence=1.0  # Always exact
        )


# Register tool with MCP server
def register(mcp_server):
    """Register count_pages tool"""
    counter = PageCounter()

    @mcp_server.tool()
    async def count_pages(presigned_url: str) -> Dict[str, Any]:
        """
        Counts exact number of pages in a PDF.

        This tool provides the EXACT page count instantly, replacing
        AI approximations with deterministic calculation.

        Benefits:
            - Free (no AI tokens)
            - Instant (~10ms)
            - 100% accurate

        Args:
            presigned_url: MinIO presigned URL for the PDF

        Returns:
            {
                "success": true,
                "data": {
                    "page_count": 15,
                    "file_size": 1234567
                },
                "hints": {
                    "page_count": 15,
                    "message": "Document has 15 pages"
                },
                "confidence": 1.0,
                "execution_time_ms": 8
            }

        Example usage:
            result = await count_pages("https://minio/file.pdf?presigned=...")
            page_count = result["hints"]["page_count"]
            # Use exact count instead of asking AI to count
        """
        result = await counter.execute(presigned_url=presigned_url)
        return result.model_dump()
