"""
MADERA MCP - merge_pdfs
Core Tool - Merges multiple PDFs into a single file

Execution time: ~30ms per file
Technique: Direct PDF manipulation (pypdf)
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfWriter
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


class PdfMerger(BaseTool):
    """Merges multiple PDFs into one"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_urls: List[str]) -> ToolResult:
        """
        Merge multiple PDFs into one

        Args:
            presigned_urls: List of MinIO presigned URLs for PDFs to merge

        Returns:
            ToolResult with merged PDF path
        """
        if not presigned_urls:
            return ToolResult(
                success=False,
                data={"error": "No PDFs provided"},
                hints={"message": "At least one PDF is required"},
                confidence=0.0
            )

        if len(presigned_urls) == 1:
            return ToolResult(
                success=False,
                data={"error": "Only one PDF provided (nothing to merge)"},
                hints={"message": "Need at least 2 PDFs to merge"},
                confidence=0.0
            )

        # Download all PDFs
        local_pdfs = []
        for url in presigned_urls:
            local_pdf = await self.fetch_file(url)
            local_pdfs.append(local_pdf)

        # Merge PDFs
        writer = PdfWriter()
        total_pages = 0
        file_info = []

        for i, pdf_path in enumerate(local_pdfs, 1):
            # Read each PDF
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)

            # Add all pages
            for page in reader.pages:
                writer.add_page(page)

            total_pages += page_count

            file_info.append({
                "file_number": i,
                "page_count": page_count,
                "file_size": pdf_path.stat().st_size
            })

        # Write merged PDF
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='_merged.pdf'
        ) as tmp:
            writer.write(tmp)
            output_path = Path(tmp.name)

        logger.info(
            f"Merged {len(local_pdfs)} PDFs into 1 "
            f"({total_pages} total pages)"
        )

        return ToolResult(
            success=True,
            data={
                "files_merged": len(local_pdfs),
                "total_pages": total_pages,
                "output_path": str(output_path),
                "output_size": output_path.stat().st_size,
                "source_files": file_info
            },
            hints={
                "files_merged": len(local_pdfs),
                "total_pages": total_pages,
                "message": f"Merged {len(local_pdfs)} PDFs ({total_pages} pages)"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register merge_pdfs tool"""
    merger = PdfMerger()

    @mcp_server.tool()
    async def merge_pdfs(presigned_urls: List[str]) -> Dict[str, Any]:
        """
        Merges multiple PDFs into a single file.

        This tool combines multiple PDF files into one, preserving page order.
        All pages from file 1, then all pages from file 2, etc.

        Args:
            presigned_urls: List of MinIO presigned URLs for PDFs (min 2)

        Returns:
            {
                "success": true,
                "data": {
                    "files_merged": 3,
                    "total_pages": 45,
                    "output_path": "/tmp/merged.pdf",
                    "output_size": 123456,
                    "source_files": [
                        {"file_number": 1, "page_count": 15, "file_size": 45000},
                        {"file_number": 2, "page_count": 20, "file_size": 60000},
                        {"file_number": 3, "page_count": 10, "file_size": 30000}
                    ]
                },
                "hints": {
                    "files_merged": 3,
                    "total_pages": 45,
                    "message": "Merged 3 PDFs (45 pages)"
                },
                "confidence": 1.0,
                "execution_time_ms": 89
            }

        Example usage:
            result = await merge_pdfs([
                "https://minio/file1.pdf?presigned=...",
                "https://minio/file2.pdf?presigned=...",
                "https://minio/file3.pdf?presigned=..."
            ])
            merged_path = result["data"]["output_path"]
        """
        result = await merger.execute(presigned_urls=presigned_urls)
        return result.model_dump()
