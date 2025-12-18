"""
MADERA MCP - rotate_page
Core Tool - Rotates a specific page in a PDF

Execution time: ~25ms
Technique: Direct PDF manipulation (pypdf)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader, PdfWriter
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


class PageRotator(BaseTool):
    """Rotates pages in a PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(
        self,
        presigned_url: str,
        page_number: int,
        degrees: int
    ) -> ToolResult:
        """
        Rotate a specific page in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF
            page_number: Page number to rotate (1-indexed)
            degrees: Rotation angle (90, 180, 270, or -90)

        Returns:
            ToolResult with rotated PDF path
        """
        # Validate rotation
        valid_rotations = [90, 180, 270, -90, -180, -270]
        if degrees not in valid_rotations:
            return ToolResult(
                success=False,
                data={
                    "error": f"Invalid rotation {degrees}°",
                    "valid_rotations": valid_rotations
                },
                hints={
                    "message": f"Rotation must be one of: {valid_rotations}"
                },
                confidence=0.0
            )

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

        # Create new PDF with rotated page
        writer = PdfWriter()

        for i, page in enumerate(reader.pages, 1):
            if i == page_number:
                # Rotate this page
                page.rotate(degrees)
            writer.add_page(page)

        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='_rotated.pdf'
        ) as tmp:
            writer.write(tmp)
            output_path = Path(tmp.name)

        logger.info(
            f"Rotated page {page_number} by {degrees}° "
            f"({total_pages} total pages)"
        )

        return ToolResult(
            success=True,
            data={
                "page_number": page_number,
                "rotation_degrees": degrees,
                "total_pages": total_pages,
                "output_path": str(output_path),
                "output_size": output_path.stat().st_size
            },
            hints={
                "page_number": page_number,
                "rotation": degrees,
                "message": f"Rotated page {page_number} by {degrees}°"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register rotate_page tool"""
    rotator = PageRotator()

    @mcp_server.tool()
    async def rotate_page(
        presigned_url: str,
        page_number: int,
        degrees: int
    ) -> Dict[str, Any]:
        """
        Rotates a specific page in a PDF.

        This tool rotates a page clockwise by the specified angle.
        Common rotations: 90° (quarter turn), 180° (upside down), 270° (three quarters).

        Args:
            presigned_url: MinIO presigned URL for the PDF
            page_number: Page to rotate (1-indexed)
            degrees: Rotation angle (90, 180, 270, -90, -180, -270)

        Returns:
            {
                "success": true,
                "data": {
                    "page_number": 3,
                    "rotation_degrees": 90,
                    "total_pages": 15,
                    "output_path": "/tmp/rotated.pdf",
                    "output_size": 123456
                },
                "hints": {
                    "page_number": 3,
                    "rotation": 90,
                    "message": "Rotated page 3 by 90°"
                },
                "confidence": 1.0,
                "execution_time_ms": 23
            }

        Example usage:
            result = await rotate_page(
                "https://minio/file.pdf?presigned=...",
                page_number=5,
                degrees=90
            )
            rotated_path = result["data"]["output_path"]
        """
        result = await rotator.execute(
            presigned_url=presigned_url,
            page_number=page_number,
            degrees=degrees
        )
        return result.model_dump()
