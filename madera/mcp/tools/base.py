"""
MADERA MCP - Base Tool Class
Provides common infrastructure for all MCP tools
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from madera.storage.minio_client import MinioClient
from madera.database import async_session_maker, ToolExecution
from madera.config import settings
import logging
import time

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """Standardized tool result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    execution_time_ms: Optional[int] = None
    hints: Optional[Dict[str, Any]] = None  # For HINTS tools


class BaseTool:
    """Base class for all MADERA tools"""

    def __init__(self):
        self.minio = MinioClient()
        self.name = self.__class__.__name__
        self.tool_class = "all_around"  # Override in subclass

    async def fetch_file(self, presigned_url: str) -> str:
        """
        Download file from presigned URL to temp location

        Args:
            presigned_url: MinIO presigned URL

        Returns:
            Local file path
        """
        try:
            local_path = await self.minio.download_from_presigned(presigned_url)
            logger.info(f"Downloaded file from {presigned_url} to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Failed to fetch file from {presigned_url}: {e}")
            raise

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute tool with error handling and metrics

        This method handles:
        - Timing execution
        - Error catching (graceful degradation)
        - Logging to database (if enabled)

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success/error/data
        """
        start_time = time.time()

        try:
            # Call implementation
            result = await self._execute(**kwargs)

            # Add execution time
            result.execution_time_ms = int((time.time() - start_time) * 1000)

            # Log execution to DB (async, don't await to not block)
            if settings.LOG_TOOL_EXECUTIONS:
                await self._log_execution(result, kwargs)

            logger.info(
                f"Tool {self.name} executed successfully in {result.execution_time_ms}ms "
                f"(confidence: {result.confidence})"
            )

            return result

        except Exception as e:
            logger.exception(f"Tool {self.name} failed: {e}")

            # Graceful degradation - return error in result, don't crash
            return ToolResult(
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    async def _execute(self, **kwargs) -> ToolResult:
        """
        Override in subclass - actual tool logic

        Must return ToolResult with:
        - success: bool
        - data: Optional[Dict]
        - confidence: Optional[float] (0.0-1.0)
        - hints: Optional[Dict] (for HINTS tools)
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _execute()")

    async def _log_execution(self, result: ToolResult, inputs: Dict):
        """Log execution to database for analytics/training"""
        try:
            async with async_session_maker() as session:
                execution = ToolExecution(
                    tool_name=self.name,
                    tool_class=self.tool_class,
                    success=result.success,
                    confidence=result.confidence,
                    execution_time_ms=result.execution_time_ms,
                    inputs=inputs,
                    outputs=result.data or {}
                )
                session.add(execution)
                await session.commit()
        except Exception as e:
            # Don't fail the tool if logging fails
            logger.warning(f"Failed to log execution for {self.name}: {e}")
