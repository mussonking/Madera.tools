"""
MADERA MCP - parse_date
Core Tool - Parses dates from various formats

Execution time: ~3ms
Technique: dateutil parsing + custom patterns
"""
from typing import Dict, Any, Optional
from madera.mcp.tools.base import BaseTool, ToolResult
from dateutil import parser
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class DateParser(BaseTool):
    """Parses dates from text"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

        # French month names
        self.french_months = {
            'janvier': '01', 'février': '02', 'fevrier': '02',
            'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06',
            'juillet': '07', 'août': '08', 'aout': '08',
            'septembre': '09', 'octobre': '10',
            'novembre': '11', 'décembre': '12', 'decembre': '12'
        }

    def _normalize_french_date(self, date_string: str) -> str:
        """Convert French month names to English"""
        date_lower = date_string.lower()

        for french, month_num in self.french_months.items():
            if french in date_lower:
                # Replace with English month name
                english_months = [
                    'January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'
                ]
                month_idx = int(month_num) - 1
                date_string = re.sub(
                    french,
                    english_months[month_idx],
                    date_string,
                    flags=re.IGNORECASE
                )
                break

        return date_string

    async def _execute(self, date_string: str) -> ToolResult:
        """
        Parse date from string

        Args:
            date_string: String containing date

        Returns:
            ToolResult with parsed date
        """
        # Normalize French dates
        normalized = self._normalize_french_date(date_string)

        try:
            # Try parsing with dateutil
            parsed_date = parser.parse(normalized, fuzzy=True)

            iso_format = parsed_date.strftime('%Y-%m-%d')
            human_format = parsed_date.strftime('%B %d, %Y')

            logger.info(
                f"Parsed date: '{date_string}' -> {iso_format}"
            )

            return ToolResult(
                success=True,
                data={
                    "original": date_string,
                    "iso_format": iso_format,
                    "human_format": human_format,
                    "year": parsed_date.year,
                    "month": parsed_date.month,
                    "day": parsed_date.day,
                    "timestamp": int(parsed_date.timestamp())
                },
                hints={
                    "iso_format": iso_format,
                    "year": parsed_date.year,
                    "message": f"Parsed: {iso_format}"
                },
                confidence=1.0
            )

        except (ValueError, TypeError) as e:
            return ToolResult(
                success=False,
                data={
                    "error": f"Could not parse date: {e}",
                    "original": date_string
                },
                hints={
                    "message": f"Invalid date format: {date_string}"
                },
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register parse_date tool"""
    parser_tool = DateParser()

    @mcp_server.tool()
    async def parse_date(date_string: str) -> Dict[str, Any]:
        """
        Parses dates from various formats.

        This tool handles multiple date formats:
        - ISO: 2024-12-16
        - North American: 12/16/2024, December 16, 2024
        - European: 16/12/2024, 16 December 2024
        - French: 16 décembre 2024

        Returns standardized ISO format (YYYY-MM-DD).

        Args:
            date_string: String containing date

        Returns:
            {
                "success": true,
                "data": {
                    "original": "16 décembre 2024",
                    "iso_format": "2024-12-16",
                    "human_format": "December 16, 2024",
                    "year": 2024,
                    "month": 12,
                    "day": 16,
                    "timestamp": 1734307200
                },
                "hints": {
                    "iso_format": "2024-12-16",
                    "year": 2024,
                    "message": "Parsed: 2024-12-16"
                },
                "confidence": 1.0,
                "execution_time_ms": 3
            }

        Example usage:
            result = await parse_date("15 janvier 2025")
            iso_date = result["hints"]["iso_format"]  # "2025-01-15"
            year = result["hints"]["year"]  # 2025
        """
        result = await parser_tool.execute(date_string=date_string)
        return result.model_dump()
