"""
MADERA MCP - split_full_name
Core Tool - Splits full name into first/last name components

Execution time: ~2ms
Technique: Pattern matching + heuristics
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class NameSplitter(BaseTool):
    """Splits full names into components"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, full_name: str) -> ToolResult:
        """
        Split full name into first and last name

        Args:
            full_name: Full name string

        Returns:
            ToolResult with name components
        """
        # Clean and split
        parts = full_name.strip().split()

        if len(parts) == 0:
            return ToolResult(
                success=False,
                data={"error": "Empty name"},
                hints={"message": "Name is empty"},
                confidence=0.0
            )

        elif len(parts) == 1:
            # Only one word - could be first or last name
            # Assume it's the last name
            first_name = ""
            last_name = parts[0]

        elif len(parts) == 2:
            # Simple case: First Last
            first_name = parts[0]
            last_name = parts[1]

        else:
            # Multiple parts: Jean-François Marie Tremblay
            # Heuristic: Everything except last word is first name
            first_name = ' '.join(parts[:-1])
            last_name = parts[-1]

        logger.info(
            f"Split name: '{full_name}' -> "
            f"First: '{first_name}', Last: '{last_name}'"
        )

        return ToolResult(
            success=True,
            data={
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "parts_count": len(parts)
            },
            hints={
                "first_name": first_name,
                "last_name": last_name,
                "message": f"First: {first_name}, Last: {last_name}"
            },
            confidence=0.95  # Not 100% - name parsing is heuristic
        )


# Register tool with MCP server
def register(mcp_server):
    """Register split_full_name tool"""
    splitter = NameSplitter()

    @mcp_server.tool()
    async def split_full_name(full_name: str) -> Dict[str, Any]:
        """
        Splits full name into first and last name components.

        This tool uses heuristics to separate first and last names:
        - 1 word: Assume last name only
        - 2 words: First Last
        - 3+ words: Everything except last word is first name

        Note: This is a heuristic approach and may not be perfect for
        all cultural naming conventions.

        Args:
            full_name: Full name string

        Returns:
            {
                "success": true,
                "data": {
                    "full_name": "Jean-François Tremblay",
                    "first_name": "Jean-François",
                    "last_name": "Tremblay",
                    "parts_count": 2
                },
                "hints": {
                    "first_name": "Jean-François",
                    "last_name": "Tremblay",
                    "message": "First: Jean-François, Last: Tremblay"
                },
                "confidence": 0.95,
                "execution_time_ms": 2
            }

        Example usage:
            result = await split_full_name("Marie-Pierre O'Brien")
            first = result["hints"]["first_name"]  # "Marie-Pierre"
            last = result["hints"]["last_name"]  # "O'Brien"
        """
        result = await splitter.execute(full_name=full_name)
        return result.model_dump()
