"""
MADERA MCP - images_to_pdf
Advanced Tool - Combines images into a single PDF

Execution time: ~100ms per image
Technique: PIL + pypdf
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from PIL import Image
from pypdf import PdfWriter
import base64
import io
import tempfile
import logging

logger = logging.getLogger(__name__)


class ImagesToPDFConverter(BaseTool):
    """Combines images into PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(
        self,
        image_urls: List[str]
    ) -> ToolResult:
        """
        Combine images into PDF

        Args:
            image_urls: List of presigned URLs to image files

        Returns:
            ToolResult with PDF info
        """
        try:
            if not image_urls:
                return ToolResult(
                    success=False,
                    data={"error": "No images provided"},
                    hints={"message": "No images to convert"},
                    confidence=0.0
                )

            # Download all images
            image_files = []
            for url in image_urls:
                img_path = await self.fetch_file(url)
                image_files.append(img_path)

            # Convert images to PDF
            writer = PdfWriter()

            for img_path in image_files:
                # Open image
                image = Image.open(img_path)

                # Convert to RGB if needed
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

                # Save as temporary PDF page
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    image.save(tmp.name, 'PDF', resolution=100.0)
                    writer.append(tmp.name)

            # Write final PDF
            output_path = image_files[0].parent / 'combined.pdf'
            with open(output_path, 'wb') as f:
                writer.write(f)

            pdf_size = output_path.stat().st_size
            page_count = len(image_urls)

            logger.info(
                f"Images to PDF: Combined {page_count} images "
                f"into {pdf_size} byte PDF"
            )

            # Read PDF bytes for return (optional)
            with open(output_path, 'rb') as f:
                pdf_bytes = f.read()

            return ToolResult(
                success=True,
                data={
                    "page_count": page_count,
                    "pdf_size": pdf_size,
                    "image_count": len(image_urls),
                    # Note: In production, upload to MinIO and return presigned URL
                    "message": "Combined PDF ready (upload to MinIO in production)"
                },
                hints={
                    "page_count": page_count,
                    "message": f"Combined {page_count} images into PDF"
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"Images to PDF conversion error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Conversion failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register images_to_pdf tool"""
    converter = ImagesToPDFConverter()

    @mcp_server.tool()
    async def images_to_pdf(image_urls: List[str]) -> Dict[str, Any]:
        """
        Combines multiple images into a single PDF file.

        Converts each image to a PDF page and merges them.
        Handles various image formats (PNG, JPG, etc.) and
        converts RGBA to RGB automatically.

        Note: In production, uploads combined PDF to MinIO and returns
        presigned URL. Current implementation returns stats only.

        Args:
            image_urls: List of presigned URLs to image files

        Returns:
            {
                "success": true,
                "data": {
                    "page_count": 5,
                    "pdf_size": 1234567,
                    "image_count": 5,
                    "message": "Combined PDF ready (upload to MinIO in production)"
                },
                "hints": {
                    "page_count": 5,
                    "message": "Combined 5 images into PDF"
                },
                "confidence": 1.0,
                "execution_time_ms": 456
            }

        Example usage:
            result = await images_to_pdf([
                "https://minio.../image1.png",
                "https://minio.../image2.jpg"
            ])
            pages = result["hints"]["page_count"]
        """
        result = await converter.execute(image_urls=image_urls)
        return result.model_dump()
