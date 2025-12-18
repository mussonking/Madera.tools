"""
MADERA MCP - extract_page
Core Tool - Extracts a specific page from a PDF

Execution time: ~20ms
Technique: Direct PDF manipulation (pypdf)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader, PdfWriter
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


class PageExtractor(BaseTool):
    """Extracts a specific page from a PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_url: str, page_number: int) -> ToolResult:
        """
        Extract a specific page from a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF
            page_number: Page number to extract (1-indexed)

        Returns:
            ToolResult with extracted page as bytes
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Read PDF
        reader = PdfReader(local_pdf)
        total_pages = len(reader.pages)

        # Validate page number
        if page_number < 1 or page_number > total_pages:
            return ToolResult(
                success=False,
                data={
                    "error": f"Page {page_number} out of range (1-{total_pages})",
                    "total_pages": total_pages
                },
                hints={
                    "message": f"Invalid page number {page_number}"
                },
                confidence=0.0
            )

        # Extract page (convert to 0-indexed)
        writer = PdfWriter()
        writer.add_page(reader.pages[page_number - 1])

        # Write to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            writer.write(tmp)
            output_path = Path(tmp.name)

        logger.info(f"Extracted page {page_number} from PDF ({total_pages} pages)")

        return ToolResult(
            success=True,
            data={
                "page_number": page_number,
                "total_pages": total_pages,
                "output_path": str(output_path),
                "output_size": output_path.stat().st_size
            },
            hints={
                "page_number": page_number,
                "message": f"Extracted page {page_number} of {total_pages}"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register extract_page tool"""
    extractor = PageExtractor()

    @mcp_server.tool()
    async def extract_page(presigned_url: str, page_number: int) -> Dict[str, Any]:
        """
        Extracts a specific page from a PDF.

        This tool creates a new single-page PDF from any page in the original
        document. Useful for splitting documents or isolating specific pages.

        Args:
            presigned_url: MinIO presigned URL for the PDF
            page_number: Page to extract (1-indexed, e.g., 1 for first page)

        Returns:
            {
                "success": true,
                "data": {
                    "page_number": 3,
                    "total_pages": 15,
                    "output_path": "/tmp/extracted_page.pdf",
                    "output_size": 12345
                },
                "hints": {
                    "page_number": 3,
                    "message": "Extracted page 3 of 15"
                },
                "confidence": 1.0,
                "execution_time_ms": 18
            }

        Example usage:
            result = await extract_page(
                "https://minio/file.pdf?presigned=...",
                page_number=5
            )
            output_path = result["data"]["output_path"]
            # Use the extracted single-page PDF
        """
        result = await extractor.execute(
            presigned_url=presigned_url,
            page_number=page_number
        )
        return result.model_dump()
