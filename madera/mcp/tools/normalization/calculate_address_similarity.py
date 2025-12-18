"""
MADERA MCP - calculate_address_similarity
Core Tool - Calculates similarity score between two addresses

Execution time: ~5ms
Technique: Normalized string comparison + Levenshtein distance
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class AddressSimilarityCalculator(BaseTool):
    """Calculates address similarity scores"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _normalize_for_comparison(self, address: str) -> str:
        """Normalize address for comparison"""
        import re

        # Uppercase
        addr = address.upper()

        # Remove accents (simplified)
        accent_map = {'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E'}
        for accent, replacement in accent_map.items():
            addr = addr.replace(accent, replacement)

        # Remove punctuation except #
        addr = re.sub(r'[^\w\s#]', ' ', addr)

        # Remove extra spaces
        addr = ' '.join(addr.split())

        return addr

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio (0-1)"""
        return SequenceMatcher(None, str1, str2).ratio()

    async def _execute(self, address1: str, address2: str) -> ToolResult:
        """
        Calculate similarity between two addresses

        Args:
            address1: First address
            address2: Second address

        Returns:
            ToolResult with similarity score
        """
        # Normalize both addresses
        norm1 = self._normalize_for_comparison(address1)
        norm2 = self._normalize_for_comparison(address2)

        # Calculate similarity
        similarity_ratio = self._calculate_similarity(norm1, norm2)
        similarity_percent = round(similarity_ratio * 100, 1)

        # Determine if match
        is_match = similarity_percent >= 80  # 80% threshold
        is_likely_match = similarity_percent >= 60  # 60% threshold

        logger.info(
            f"Address similarity: {similarity_percent}%\n"
            f"  Addr1: '{address1}'\n"
            f"  Addr2: '{address2}'"
        )

        return ToolResult(
            success=True,
            data={
                "address1": address1,
                "address2": address2,
                "normalized1": norm1,
                "normalized2": norm2,
                "similarity_ratio": similarity_ratio,
                "similarity_percent": similarity_percent,
                "is_match": is_match,
                "is_likely_match": is_likely_match
            },
            hints={
                "similarity_percent": similarity_percent,
                "is_match": is_match,
                "message": f"{similarity_percent}% similar"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register calculate_address_similarity tool"""
    calculator = AddressSimilarityCalculator()

    @mcp_server.tool()
    async def calculate_address_similarity(
        address1: str,
        address2: str
    ) -> Dict[str, Any]:
        """
        Calculates similarity score between two addresses.

        This tool compares addresses after normalization and returns
        a similarity percentage (0-100%). Useful for detecting duplicates
        or fuzzy matching.

        Thresholds:
            - >= 80%: Considered a match
            - 60-79%: Likely match (review recommended)
            - < 60%: Different addresses

        Args:
            address1: First address to compare
            address2: Second address to compare

        Returns:
            {
                "success": true,
                "data": {
                    "address1": "123 Rue de l'Église, Montreal",
                    "address2": "123 rue Eglise Montreal",
                    "normalized1": "123 RUE DE L EGLISE MONTREAL",
                    "normalized2": "123 RUE EGLISE MONTREAL",
                    "similarity_ratio": 0.92,
                    "similarity_percent": 92.0,
                    "is_match": true,
                    "is_likely_match": true
                },
                "hints": {
                    "similarity_percent": 92.0,
                    "is_match": true,
                    "message": "92.0% similar"
                },
                "confidence": 1.0,
                "execution_time_ms": 4
            }

        Example usage:
            result = await calculate_address_similarity(
                "123 Main Street, Montreal",
                "123 Main St Montreal"
            )
            if result["hints"]["is_match"]:
                print("Addresses match!")
        """
        result = await calculator.execute(
            address1=address1,
            address2=address2
        )
        return result.model_dump()
