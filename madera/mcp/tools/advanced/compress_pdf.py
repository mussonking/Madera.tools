"""
MADERA MCP - compress_pdf
Advanced Tool - Compresses PDF files

Execution time: ~500ms
Technique: pypdf compression
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader, PdfWriter
import logging

logger = logging.getLogger(__name__)


class PDFCompressor(BaseTool):
    """Compresses PDF files"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(
        self,
        presigned_url: str,
        compression_level: str = "medium"
    ) -> ToolResult:
        """
        Compress PDF

        Args:
            presigned_url: URL to PDF file
            compression_level: Compression level (low, medium, high)

        Returns:
            ToolResult with compressed PDF info
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)
            original_size = local_pdf.stat().st_size

            # Read PDF
            reader = PdfReader(local_pdf)
            writer = PdfWriter()

            # Add all pages
            for page in reader.pages:
                writer.add_page(page)

            # Apply compression
            if compression_level == "high":
                for page in writer.pages:
                    page.compress_content_streams()
                writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
            elif compression_level == "medium":
                for page in writer.pages:
                    page.compress_content_streams()
            # Low = no additional compression

            # Write compressed PDF
            compressed_path = local_pdf.parent / f"compressed_{local_pdf.name}"
            with open(compressed_path, 'wb') as f:
                writer.write(f)

            compressed_size = compressed_path.stat().st_size
            compression_ratio = ((original_size - compressed_size) / original_size) * 100

            logger.info(
                f"PDF compression: {original_size} → {compressed_size} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )

            # Read compressed PDF as bytes for return (optional)
            with open(compressed_path, 'rb') as f:
                compressed_bytes = f.read()

            return ToolResult(
                success=True,
                data={
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": round(compression_ratio, 2),
                    "compression_level": compression_level,
                    # Note: In production, upload to MinIO and return presigned URL
                    # For now, we just return stats
                    "message": "Compressed PDF ready (upload to MinIO in production)"
                },
                hints={
                    "compression_ratio": round(compression_ratio, 2),
                    "message": f"Compressed by {compression_ratio:.1f}%"
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"PDF compression error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Compression failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register compress_pdf tool"""
    compressor = PDFCompressor()

    @mcp_server.tool()
    async def compress_pdf(
        presigned_url: str,
        compression_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Compresses PDF files using pypdf compression.

        Compression levels:
        - low: Basic compression
        - medium: Content stream compression (default)
        - high: Content stream + object deduplication

        Note: In production, uploads compressed PDF to MinIO and returns
        new presigned URL. Current implementation returns stats only.

        Args:
            presigned_url: Presigned URL to PDF file
            compression_level: Compression level (low, medium, high)

        Returns:
            {
                "success": true,
                "data": {
                    "original_size": 1048576,
                    "compressed_size": 524288,
                    "compression_ratio": 50.0,
                    "compression_level": "medium",
                    "message": "Compressed PDF ready (upload to MinIO in production)"
                },
                "hints": {
                    "compression_ratio": 50.0,
                    "message": "Compressed by 50.0%"
                },
                "confidence": 1.0,
                "execution_time_ms": 478
            }

        Example usage:
            result = await compress_pdf(
                "https://minio.../large.pdf",
                compression_level="high"
            )
            saved = result["hints"]["compression_ratio"]
        """
        result = await compressor.execute(
            presigned_url=presigned_url,
            compression_level=compression_level
        )
        return result.model_dump()
