"""
MADERA MCP - generate_thumbnail
Advanced Tool - Generates PNG thumbnails from PDF pages

Execution time: ~200ms per page
Technique: pdf2image conversion
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pdf2image import convert_from_path
from PIL import Image
import io
import base64
import logging

logger = logging.getLogger(__name__)


class ThumbnailGenerator(BaseTool):
    """Generates thumbnails from PDFs"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(
        self,
        presigned_url: str,
        page_number: int = 1,
        size: int = 300
    ) -> ToolResult:
        """
        Generate thumbnail from PDF page

        Args:
            presigned_url: URL to PDF file
            page_number: Page number (1-indexed)
            size: Thumbnail width in pixels (height scaled proportionally)

        Returns:
            ToolResult with base64-encoded PNG
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)

            # Convert specific page to image
            images = convert_from_path(
                str(local_pdf),
                first_page=page_number,
                last_page=page_number,
                dpi=150
            )

            if not images:
                return ToolResult(
                    success=False,
                    data={"error": f"Could not convert page {page_number}"},
                    hints={"message": "Page conversion failed"},
                    confidence=0.0
                )

            # Get first (and only) image
            image = images[0]

            # Resize to thumbnail
            original_width, original_height = image.size
            aspect_ratio = original_height / original_width
            thumbnail_height = int(size * aspect_ratio)

            thumbnail = image.resize((size, thumbnail_height), Image.Resampling.LANCZOS)

            # Convert to PNG bytes
            png_buffer = io.BytesIO()
            thumbnail.save(png_buffer, format='PNG')
            png_bytes = png_buffer.getvalue()

            # Base64 encode for transport
            base64_png = base64.b64encode(png_bytes).decode('utf-8')

            logger.info(
                f"Generated thumbnail for page {page_number}: "
                f"{size}x{thumbnail_height}px ({len(png_bytes)} bytes)"
            )

            return ToolResult(
                success=True,
                data={
                    "page_number": page_number,
                    "thumbnail_width": size,
                    "thumbnail_height": thumbnail_height,
                    "original_width": original_width,
                    "original_height": original_height,
                    "file_size_bytes": len(png_bytes),
                    "thumbnail_base64": base64_png
                },
                hints={
                    "thumbnail_width": size,
                    "thumbnail_height": thumbnail_height,
                    "message": f"Thumbnail generated: {size}x{thumbnail_height}px"
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"Thumbnail generation error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Thumbnail generation failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register generate_thumbnail tool"""
    generator = ThumbnailGenerator()

    @mcp_server.tool()
    async def generate_thumbnail(
        presigned_url: str,
        page_number: int = 1,
        size: int = 300
    ) -> Dict[str, Any]:
        """
        Generates PNG thumbnail from a PDF page.

        Converts the specified page to an image and resizes it to thumbnail size.
        Returns base64-encoded PNG for easy transport.

        Args:
            presigned_url: Presigned URL to PDF file
            page_number: Page number (1-indexed, default 1)
            size: Thumbnail width in pixels (default 300)

        Returns:
            {
                "success": true,
                "data": {
                    "page_number": 1,
                    "thumbnail_width": 300,
                    "thumbnail_height": 388,
                    "original_width": 612,
                    "original_height": 792,
                    "file_size_bytes": 45678,
                    "thumbnail_base64": "iVBORw0KGgoAAAANS..."
                },
                "hints": {
                    "thumbnail_width": 300,
                    "thumbnail_height": 388,
                    "message": "Thumbnail generated: 300x388px"
                },
                "confidence": 1.0,
                "execution_time_ms": 195
            }

        Example usage:
            result = await generate_thumbnail(
                "https://minio.../doc.pdf",
                page_number=1,
                size=300
            )
            base64_png = result["data"]["thumbnail_base64"]
        """
        result = await generator.execute(
            presigned_url=presigned_url,
            page_number=page_number,
            size=size
        )
        return result.model_dump()
