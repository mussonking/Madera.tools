"""
MADERA MCP - extract_text
Core Tool - Extracts all text from a PDF

Execution time: ~50ms
Technique: Direct text extraction (pypdf)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class TextExtractor(BaseTool):
    """Extracts text from PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Extract all text from a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with extracted text
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Extract text
        reader = PdfReader(local_pdf)
        total_pages = len(reader.pages)

        full_text = []
        char_count = 0

        for page in reader.pages:
            text = page.extract_text()
            full_text.append(text)
            char_count += len(text)

        combined_text = "\n\n".join(full_text)

        logger.info(
            f"Extracted {char_count} characters from {total_pages} pages"
        )

        return ToolResult(
            success=True,
            data={
                "text": combined_text,
                "total_pages": total_pages,
                "character_count": char_count,
                "word_count": len(combined_text.split()),
                "has_text": char_count > 0
            },
            hints={
                "has_text": char_count > 0,
                "character_count": char_count,
                "message": f"Extracted {char_count} characters from {total_pages} pages"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register extract_text tool"""
    extractor = TextExtractor()

    @mcp_server.tool()
    async def extract_text(presigned_url: str) -> Dict[str, Any]:
        """
        Extracts all text from a PDF.

        This tool extracts readable text from all pages and combines them.
        Much faster and cheaper than using AI to read text.

        Benefits:
            - Free (no AI tokens)
            - Fast (~50ms)
            - 100% accurate for readable PDFs

        Note: Scanned PDFs (images) will return empty text. Use OCR tools instead.

        Args:
            presigned_url: MinIO presigned URL for the PDF

        Returns:
            {
                "success": true,
                "data": {
                    "text": "Full extracted text...",
                    "total_pages": 15,
                    "character_count": 12345,
                    "word_count": 2000,
                    "has_text": true
                },
                "hints": {
                    "has_text": true,
                    "character_count": 12345,
                    "message": "Extracted 12345 characters from 15 pages"
                },
                "confidence": 1.0,
                "execution_time_ms": 48
            }

        Example usage:
            result = await extract_text("https://minio/file.pdf?presigned=...")
            if result["hints"]["has_text"]:
                text = result["data"]["text"]
                # Use extracted text instead of AI vision
        """
        result = await extractor.execute(presigned_url=presigned_url)
        return result.model_dump()
