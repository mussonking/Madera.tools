"""
MADERA MCP - split_pdf
Core Tool - Splits a PDF into multiple files at specified points

Execution time: ~50ms
Technique: Direct PDF manipulation (pypdf)
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader, PdfWriter
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


class PdfSplitter(BaseTool):
    """Splits PDF at specified page ranges"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _parse_page_ranges(self, page_ranges: str, total_pages: int) -> List[tuple]:
        """
        Parse page range string like "1-3,5,7-9"

        Args:
            page_ranges: String describing ranges
            total_pages: Total pages in PDF

        Returns:
            List of (start, end) tuples (1-indexed)
        """
        ranges = []

        for part in page_ranges.split(','):
            part = part.strip()

            if '-' in part:
                # Range like "1-3"
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
            else:
                # Single page like "5"
                start = end = int(part)

            # Validate
            if start < 1 or end > total_pages or start > end:
                raise ValueError(
                    f"Invalid range {part} (total pages: {total_pages})"
                )

            ranges.append((start, end))

        return ranges

    async def _execute(self, presigned_url: str, page_ranges: str) -> ToolResult:
        """
        Split PDF into multiple files

        Args:
            presigned_url: MinIO presigned URL for PDF
            page_ranges: Page ranges like "1-3,5,7-9"

        Returns:
            ToolResult with output file paths
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Read PDF
        reader = PdfReader(local_pdf)
        total_pages = len(reader.pages)

        try:
            # Parse ranges
            ranges = self._parse_page_ranges(page_ranges, total_pages)
        except ValueError as e:
            return ToolResult(
                success=False,
                data={
                    "error": str(e),
                    "total_pages": total_pages
                },
                hints={
                    "message": f"Invalid page ranges: {e}"
                },
                confidence=0.0
            )

        # Create output files
        output_files = []

        for i, (start, end) in enumerate(ranges, 1):
            writer = PdfWriter()

            # Add pages (convert to 0-indexed)
            for page_num in range(start - 1, end):
                writer.add_page(reader.pages[page_num])

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'_part{i}.pdf'
            ) as tmp:
                writer.write(tmp)
                output_path = Path(tmp.name)

            output_files.append({
                "part": i,
                "pages": f"{start}-{end}",
                "path": str(output_path),
                "size": output_path.stat().st_size,
                "page_count": end - start + 1
            })

        logger.info(
            f"Split PDF into {len(output_files)} parts: {page_ranges}"
        )

        return ToolResult(
            success=True,
            data={
                "total_pages": total_pages,
                "parts_created": len(output_files),
                "output_files": output_files
            },
            hints={
                "parts_created": len(output_files),
                "message": f"Split into {len(output_files)} parts: {page_ranges}"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register split_pdf tool"""
    splitter = PdfSplitter()

    @mcp_server.tool()
    async def split_pdf(presigned_url: str, page_ranges: str) -> Dict[str, Any]:
        """
        Splits a PDF into multiple files at specified page ranges.

        This tool divides a PDF into separate files based on page ranges.
        Supports complex range syntax like "1-3,5,7-9".

        Args:
            presigned_url: MinIO presigned URL for the PDF
            page_ranges: Comma-separated page ranges (e.g., "1-3,5,7-9")
                        - "1-3" extracts pages 1 to 3
                        - "5" extracts only page 5
                        - "7-9" extracts pages 7 to 9

        Returns:
            {
                "success": true,
                "data": {
                    "total_pages": 15,
                    "parts_created": 3,
                    "output_files": [
                        {
                            "part": 1,
                            "pages": "1-3",
                            "path": "/tmp/file_part1.pdf",
                            "size": 12345,
                            "page_count": 3
                        },
                        ...
                    ]
                },
                "hints": {
                    "parts_created": 3,
                    "message": "Split into 3 parts: 1-3,5,7-9"
                },
                "confidence": 1.0,
                "execution_time_ms": 47
            }

        Example usage:
            result = await split_pdf(
                "https://minio/file.pdf?presigned=...",
                page_ranges="1-5,10,15-20"
            )
            for file in result["data"]["output_files"]:
                print(f"Part {file['part']}: {file['path']}")
        """
        result = await splitter.execute(
            presigned_url=presigned_url,
            page_ranges=page_ranges
        )
        return result.model_dump()
