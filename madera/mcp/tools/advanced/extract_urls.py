"""
MADERA MCP - extract_urls
Advanced Tool - Extracts URLs from PDF

Execution time: ~10ms
Technique: Text extraction + regex + PDF annotations
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import re
import logging

logger = logging.getLogger(__name__)


class URLExtractor(BaseTool):
    """Extracts URLs from PDFs"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

        # URL regex pattern
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Extract URLs from PDF

        Args:
            presigned_url: URL to PDF file

        Returns:
            ToolResult with extracted URLs
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)

            # Read PDF
            reader = PdfReader(local_pdf)

            # Extract URLs from text
            urls_from_text = set()
            for page in reader.pages:
                text = page.extract_text()
                matches = self.url_pattern.findall(text)
                urls_from_text.update(matches)

            # Extract URLs from annotations (links)
            urls_from_annotations = set()
            for page in reader.pages:
                if '/Annots' in page:
                    annotations = page['/Annots']

                    for annot in annotations:
                        annot_obj = annot.get_object()

                        # Check for URI action
                        if '/A' in annot_obj:
                            action = annot_obj['/A']
                            if '/URI' in action:
                                url = action['/URI']
                                urls_from_annotations.add(str(url))

            # Combine all URLs
            all_urls = list(urls_from_text | urls_from_annotations)
            all_urls.sort()

            logger.info(
                f"URL extraction: {len(all_urls)} unique URLs found "
                f"({len(urls_from_text)} from text, {len(urls_from_annotations)} from links)"
            )

            return ToolResult(
                success=True,
                data={
                    "url_count": len(all_urls),
                    "urls": all_urls,
                    "urls_from_text": list(urls_from_text),
                    "urls_from_annotations": list(urls_from_annotations)
                },
                hints={
                    "url_count": len(all_urls),
                    "message": f"Found {len(all_urls)} URLs"
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"URL extraction error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Extraction failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register extract_urls tool"""
    extractor = URLExtractor()

    @mcp_server.tool()
    async def extract_urls(presigned_url: str) -> Dict[str, Any]:
        """
        Extracts URLs from PDF text and link annotations.

        Finds URLs in two ways:
        1. Pattern matching in extracted text
        2. Link annotations (clickable links)

        Args:
            presigned_url: Presigned URL to PDF file

        Returns:
            {
                "success": true,
                "data": {
                    "url_count": 5,
                    "urls": [
                        "https://example.com",
                        "https://example.com/page",
                        "http://test.com"
                    ],
                    "urls_from_text": ["https://example.com"],
                    "urls_from_annotations": ["https://example.com/page", "http://test.com"]
                },
                "hints": {
                    "url_count": 5,
                    "message": "Found 5 URLs"
                },
                "confidence": 1.0,
                "execution_time_ms": 8
            }

        Example usage:
            result = await extract_urls("https://minio.../document.pdf")
            urls = result["data"]["urls"]
        """
        result = await extractor.execute(presigned_url=presigned_url)
        return result.model_dump()
