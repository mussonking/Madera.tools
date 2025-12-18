"""
MADERA MCP - normalize_name
Core Tool - Normalizes person names for matching

Execution time: ~2ms
Technique: String normalization + title case
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class NameNormalizer(BaseTool):
    """Normalizes person names"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _remove_accents(self, text: str) -> str:
        """Remove accents from text"""
        accent_map = {
            'À': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Î': 'I', 'Ï': 'I',
            'Ô': 'O', 'Ö': 'O',
            'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c',
        }

        for accent, replacement in accent_map.items():
            text = text.replace(accent, replacement)

        return text

    async def _execute(self, raw_name: str, remove_accents: bool = True) -> ToolResult:
        """
        Normalize a person name

        Args:
            raw_name: Raw name string
            remove_accents: Remove accents (default: True)

        Returns:
            ToolResult with normalized name
        """
        # Remove extra whitespace
        name = ' '.join(raw_name.split())

        # Remove special characters except hyphens and apostrophes
        name = re.sub(r'[^\w\s\'-]', '', name)

        # Title case (capitalize first letter of each word)
        name = name.title()

        # Handle special cases:
        # - "Mc" prefix: McDonald -> McDonald (not Mcdonald)
        name = re.sub(r'\bMc([a-z])', lambda m: 'Mc' + m.group(1).upper(), name)

        # - "O'" prefix: O'Brien -> O'Brien (not O'brien)
        name = re.sub(r"\bO'([a-z])", lambda m: "O'" + m.group(1).upper(), name)

        # Remove accents if requested
        if remove_accents:
            name = self._remove_accents(name)

        logger.info(f"Normalized name: '{raw_name}' -> '{name}'")

        return ToolResult(
            success=True,
            data={
                "original": raw_name,
                "normalized": name,
                "without_accents": self._remove_accents(name)
            },
            hints={
                "normalized": name,
                "message": f"Normalized: {name}"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register normalize_name tool"""
    normalizer = NameNormalizer()

    @mcp_server.tool()
    async def normalize_name(raw_name: str, remove_accents: bool = True) -> Dict[str, Any]:
        """
        Normalizes person names for consistent matching.

        This tool standardizes names by:
        - Converting to title case (proper capitalization)
        - Removing extra whitespace
        - Optionally removing accents
        - Handling special cases (Mc, O', etc.)

        Args:
            raw_name: Raw name string
            remove_accents: Remove accents (default: True)

        Returns:
            {
                "success": true,
                "data": {
                    "original": "JEAN-FRANÇOIS TREMBLAY",
                    "normalized": "Jean-Francois Tremblay",
                    "without_accents": "Jean-Francois Tremblay"
                },
                "hints": {
                    "normalized": "Jean-Francois Tremblay",
                    "message": "Normalized: Jean-Francois Tremblay"
                },
                "confidence": 1.0,
                "execution_time_ms": 2
            }

        Example usage:
            result = await normalize_name("MARIE-PIERRE O'BRIEN")
            normalized = result["hints"]["normalized"]  # "Marie-Pierre O'Brien"
        """
        result = await normalizer.execute(
            raw_name=raw_name,
            remove_accents=remove_accents
        )
        return result.model_dump()
