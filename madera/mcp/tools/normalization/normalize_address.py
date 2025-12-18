"""
MADERA MCP - normalize_address
Core Tool - Normalizes Canadian addresses for matching

Execution time: ~5ms
Technique: String normalization + standardization
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class AddressNormalizer(BaseTool):
    """Normalizes Canadian addresses"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

        # Street type abbreviations (Canadian standard)
        self.street_types = {
            'AVENUE': 'AVE',
            'BOULEVARD': 'BLVD',
            'CHEMIN': 'CH',
            'CIRCLE': 'CIR',
            'COURT': 'CRT',
            'CRESCENT': 'CRES',
            'DRIVE': 'DR',
            'LANE': 'LANE',
            'PLACE': 'PL',
            'ROAD': 'RD',
            'ROUTE': 'RTE',
            'STREET': 'ST',
            'TERRACE': 'TERR',
            'WAY': 'WAY',
            # French
            'RUE': 'RUE',
            'RANG': 'RG',
            'MONTEE': 'MTEE',
        }

        # Direction abbreviations
        self.directions = {
            'NORTH': 'N',
            'SOUTH': 'S',
            'EAST': 'E',
            'WEST': 'W',
            'NORD': 'N',
            'SUD': 'S',
            'EST': 'E',
            'OUEST': 'O',
        }

    def _remove_accents(self, text: str) -> str:
        """Remove French accents"""
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

    async def _execute(self, raw_address: str) -> ToolResult:
        """
        Normalize a Canadian address

        Args:
            raw_address: Raw address string

        Returns:
            ToolResult with normalized address
        """
        # Step 1: Remove extra whitespace
        address = ' '.join(raw_address.split())

        # Step 2: Uppercase
        address = address.upper()

        # Step 3: Remove accents
        address = self._remove_accents(address)

        # Step 4: Remove punctuation except #, -
        address = re.sub(r'[^\w\s#-]', ' ', address)

        # Step 5: Normalize street types
        for full_type, abbrev in self.street_types.items():
            # Word boundary matching
            pattern = r'\b' + full_type + r'\b'
            address = re.sub(pattern, abbrev, address)

        # Step 6: Normalize directions
        for full_dir, abbrev in self.directions.items():
            pattern = r'\b' + full_dir + r'\b'
            address = re.sub(pattern, abbrev, address)

        # Step 7: Remove extra spaces
        address = ' '.join(address.split())

        logger.info(f"Normalized address: '{raw_address}' -> '{address}'")

        return ToolResult(
            success=True,
            data={
                "original": raw_address,
                "normalized": address
            },
            hints={
                "normalized": address,
                "message": f"Normalized: {address}"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register normalize_address tool"""
    normalizer = AddressNormalizer()

    @mcp_server.tool()
    async def normalize_address(raw_address: str) -> Dict[str, Any]:
        """
        Normalizes Canadian addresses for consistent matching.

        This tool standardizes addresses by:
        - Removing accents (é -> e)
        - Converting to uppercase
        - Abbreviating street types (Avenue -> AVE)
        - Abbreviating directions (North -> N)
        - Removing extra whitespace and punctuation

        Benefits:
            - Consistent format for address matching
            - Reduces false negatives when comparing addresses
            - Handles French/English variations

        Args:
            raw_address: Raw address string

        Returns:
            {
                "success": true,
                "data": {
                    "original": "123 rue de l'Église, Montréal",
                    "normalized": "123 RUE DE L EGLISE MONTREAL"
                },
                "hints": {
                    "normalized": "123 RUE DE L EGLISE MONTREAL",
                    "message": "Normalized: 123 RUE DE L EGLISE MONTREAL"
                },
                "confidence": 1.0,
                "execution_time_ms": 3
            }

        Example usage:
            result = await normalize_address("123 Avenue North, Montreal")
            normalized = result["hints"]["normalized"]
            # "123 AVE N MONTREAL"
        """
        result = await normalizer.execute(raw_address=raw_address)
        return result.model_dump()
