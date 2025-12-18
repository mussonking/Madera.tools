"""
MADERA MCP - MinIO Client
Handles presigned URL downloads and temp file management
"""
import httpx
import tempfile
import os
from pathlib import Path
from madera.config import settings
import logging

logger = logging.getLogger(__name__)


class MinioClient:
    """Client for downloading files from MinIO presigned URLs"""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "madera_mcp"
        self.temp_dir.mkdir(exist_ok=True)

    async def download_from_presigned(self, presigned_url: str) -> str:
        """
        Download file from presigned URL to temp location

        Args:
            presigned_url: MinIO presigned URL (expires in 1 hour typically)

        Returns:
            Local file path

        Raises:
            httpx.HTTPError: If download fails
        """
        # Extract filename from URL (before query params)
        filename = presigned_url.split("?")[0].split("/")[-1]
        local_path = self.temp_dir / filename

        logger.debug(f"Downloading {presigned_url} to {local_path}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(presigned_url)
            response.raise_for_status()

            # Write to temp file
            with open(local_path, "wb") as f:
                f.write(response.content)

        logger.info(f"Downloaded {len(response.content)} bytes to {local_path}")
        return str(local_path)

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Cleanup temp files older than specified hours

        Args:
            older_than_hours: Delete files older than this many hours
        """
        import time
        cutoff_time = time.time() - (older_than_hours * 3600)

        for file in self.temp_dir.iterdir():
            if file.is_file() and file.stat().st_mtime < cutoff_time:
                try:
                    file.unlink()
                    logger.debug(f"Deleted old temp file: {file}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {file}: {e}")
