"""
MADERA MCP - validate_date_range
Validation Tool - Validates date ranges for consistency

Execution time: ~1ms
Technique: Date parsing and comparison
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DateRangeValidator(BaseTool):
    """Validates date ranges"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string (ISO format)"""
        # Support ISO format YYYY-MM-DD
        try:
            return datetime.fromisoformat(date_str)
        except:
            # Try common formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%Y/%m/%d',
                '%d-%m-%Y',
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue

            raise ValueError(f"Cannot parse date: {date_str}")

    async def _execute(
        self,
        start_date: str,
        end_date: str,
        max_days: int = None
    ) -> ToolResult:
        """
        Validate date range

        Args:
            start_date: Start date (ISO format or common formats)
            end_date: End date (ISO format or common formats)
            max_days: Optional maximum allowed days in range

        Returns:
            ToolResult with validation result
        """
        try:
            # Parse dates
            start = self._parse_date(start_date)
            end = self._parse_date(end_date)

            # Calculate difference
            delta = end - start
            days_diff = delta.days

            # Validate chronological order
            is_chronological = end >= start

            # Validate max days if specified
            within_max = True
            if max_days is not None and days_diff > max_days:
                within_max = False

            # Overall validity
            is_valid = is_chronological and within_max

            # Check if in future
            today = datetime.now()
            start_in_future = start > today
            end_in_future = end > today

            logger.info(
                f"Date range validation: {start_date} to {end_date} -> "
                f"{days_diff} days, {'Valid' if is_valid else 'Invalid'}"
            )

            return ToolResult(
                success=True,
                data={
                    "start_date": start_date,
                    "end_date": end_date,
                    "parsed_start": start.isoformat(),
                    "parsed_end": end.isoformat(),
                    "days_difference": days_diff,
                    "is_chronological": is_chronological,
                    "within_max_days": within_max,
                    "is_valid": is_valid,
                    "start_in_future": start_in_future,
                    "end_in_future": end_in_future,
                    "error": None if is_valid else (
                        "End date before start date" if not is_chronological else
                        f"Range exceeds {max_days} days"
                    )
                },
                hints={
                    "is_valid": is_valid,
                    "days_difference": days_diff,
                    "message": (
                        f"Valid range: {days_diff} days" if is_valid else
                        "Invalid date range"
                    )
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"Date range validation error: {e}")

            return ToolResult(
                success=False,
                data={
                    "error": str(e),
                    "start_date": start_date,
                    "end_date": end_date
                },
                hints={
                    "is_valid": False,
                    "message": f"Error parsing dates: {e}"
                },
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register validate_date_range tool"""
    validator = DateRangeValidator()

    @mcp_server.tool()
    async def validate_date_range(
        start_date: str,
        end_date: str,
        max_days: int = None
    ) -> Dict[str, Any]:
        """
        Validates date ranges for consistency and logic.

        Checks:
        - Both dates are valid and parseable
        - End date is after or equal to start date
        - Optional: Range does not exceed max_days
        - Whether dates are in the future

        Supports multiple date formats:
        - ISO: YYYY-MM-DD (preferred)
        - DD/MM/YYYY, MM/DD/YYYY, etc.

        Args:
            start_date: Start date
            end_date: End date
            max_days: Optional maximum allowed days in range

        Returns:
            {
                "success": true,
                "data": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "parsed_start": "2024-01-01T00:00:00",
                    "parsed_end": "2024-12-31T00:00:00",
                    "days_difference": 365,
                    "is_chronological": true,
                    "within_max_days": true,
                    "is_valid": true,
                    "start_in_future": false,
                    "end_in_future": false,
                    "error": null
                },
                "hints": {
                    "is_valid": true,
                    "days_difference": 365,
                    "message": "Valid range: 365 days"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await validate_date_range("2024-01-01", "2024-12-31")
            if result["hints"]["is_valid"]:
                days = result["hints"]["days_difference"]
        """
        result = await validator.execute(
            start_date=start_date,
            end_date=end_date,
            max_days=max_days
        )
        return result.model_dump()
