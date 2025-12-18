"""
MADERA MCP - pdf_to_images
Advanced Tool - Converts PDF pages to PNG images

Execution time: ~300ms per page
Technique: pdf2image conversion
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pdf2image import convert_from_path
import base64
import io
import logging

logger = logging.getLogger(__name__)


class PDFToImagesConverter(BaseTool):
    """Converts PDF to images"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(
        self,
        presigned_url: str,
        dpi: int = 200,
        max_pages: int = None
    ) -> ToolResult:
        """
        Convert PDF pages to PNG images

        Args:
            presigned_url: URL to PDF file
            dpi: Image resolution (default 200)
            max_pages: Maximum pages to convert (None = all)

        Returns:
            ToolResult with base64-encoded PNG images
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)

            # Determine page range
            if max_pages:
                last_page = max_pages
            else:
                last_page = None

            # Convert to images
            images = convert_from_path(
                str(local_pdf),
                dpi=dpi,
                last_page=last_page
            )

            # Convert to base64 PNGs
            image_data = []
            for i, image in enumerate(images, start=1):
                # Convert to PNG bytes
                png_buffer = io.BytesIO()
                image.save(png_buffer, format='PNG')
                png_bytes = png_buffer.getvalue()

                # Base64 encode
                base64_png = base64.b64encode(png_bytes).decode('utf-8')

                width, height = image.size

                image_data.append({
                    "page_number": i,
                    "width": width,
                    "height": height,
                    "file_size_bytes": len(png_bytes),
                    "image_base64": base64_png
                })

            logger.info(
                f"PDF to images: Converted {len(images)} pages at {dpi} DPI"
            )

            return ToolResult(
                success=True,
                data={
                    "page_count": len(images),
                    "dpi": dpi,
                    "images": image_data
                },
                hints={
                    "page_count": len(images),
                    "message": f"Converted {len(images)} pages to PNG"
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"PDF to images conversion error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Conversion failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register pdf_to_images tool"""
    converter = PDFToImagesConverter()

    @mcp_server.tool()
    async def pdf_to_images(
        presigned_url: str,
        dpi: int = 200,
        max_pages: int = None
    ) -> Dict[str, Any]:
        """
        Converts each PDF page to a PNG image.

        Useful for image-based AI analysis or creating previews.
        Returns base64-encoded PNGs for each page.

        Args:
            presigned_url: Presigned URL to PDF file
            dpi: Image resolution (default 200, higher = better quality)
            max_pages: Maximum pages to convert (None = all pages)

        Returns:
            {
                "success": true,
                "data": {
                    "page_count": 3,
                    "dpi": 200,
                    "images": [
                        {
                            "page_number": 1,
                            "width": 1654,
                            "height": 2339,
                            "file_size_bytes": 234567,
                            "image_base64": "iVBORw0KGgoAAAANS..."
                        },
                        ...
                    ]
                },
                "hints": {
                    "page_count": 3,
                    "message": "Converted 3 pages to PNG"
                },
                "confidence": 1.0,
                "execution_time_ms": 856
            }

        Example usage:
            result = await pdf_to_images(
                "https://minio.../doc.pdf",
                dpi=300
            )
            images = result["data"]["images"]
        """
        result = await converter.execute(
            presigned_url=presigned_url,
            dpi=dpi,
            max_pages=max_pages
        )
        return result.model_dump()
