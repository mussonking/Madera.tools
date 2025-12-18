"""
MADERA MCP - validate_sin
Validation Tool - Validates Canadian Social Insurance Number

Execution time: ~1ms
Technique: Luhn algorithm (modulus 10)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class SINValidator(BaseTool):
    """Validates Canadian SIN numbers"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _clean_sin(self, sin: str) -> str:
        """Remove spaces and dashes"""
        return re.sub(r'[\s\-]', '', sin)

    def _validate_sin(self, sin: str) -> bool:
        """
        Validate SIN using Luhn algorithm

        Canadian SIN format: XXX-XXX-XXX (9 digits)
        """
        # Must be exactly 9 digits
        if len(sin) != 9 or not sin.isdigit():
            return False

        # Cannot start with 0 or 8
        if sin[0] in ['0', '8']:
            return False

        # Luhn algorithm (modulus 10)
        total = 0
        for i, digit in enumerate(sin):
            num = int(digit)

            # Double every second digit
            if i % 2 == 1:
                num *= 2
                # If result is > 9, add digits together
                if num > 9:
                    num = num // 10 + num % 10

            total += num

        # Valid if total is divisible by 10
        return total % 10 == 0

    async def _execute(self, sin: str) -> ToolResult:
        """
        Validate Canadian SIN

        Args:
            sin: SIN number (with or without formatting)

        Returns:
            ToolResult with validation result
        """
        # Clean input
        cleaned_sin = self._clean_sin(sin)

        # Validate
        is_valid = self._validate_sin(cleaned_sin)

        # Format nicely
        if len(cleaned_sin) == 9:
            formatted_sin = f"{cleaned_sin[0:3]}-{cleaned_sin[3:6]}-{cleaned_sin[6:9]}"
        else:
            formatted_sin = sin

        logger.info(f"SIN validation: '{sin}' -> {'Valid' if is_valid else 'Invalid'}")

        return ToolResult(
            success=True,
            data={
                "original_sin": sin,
                "cleaned_sin": cleaned_sin,
                "formatted_sin": formatted_sin if is_valid else None,
                "is_valid": is_valid,
                "error": None if is_valid else "Invalid SIN format or checksum"
            },
            hints={
                "is_valid": is_valid,
                "formatted_sin": formatted_sin if is_valid else None,
                "message": "Valid Canadian SIN" if is_valid else "Invalid SIN"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register validate_sin tool"""
    validator = SINValidator()

    @mcp_server.tool()
    async def validate_sin(sin: str) -> Dict[str, Any]:
        """
        Validates Canadian Social Insurance Number using Luhn algorithm.

        Checks:
        - Exactly 9 digits
        - Does not start with 0 or 8
        - Passes Luhn checksum validation

        Args:
            sin: SIN number (e.g., "123-456-782" or "123456782")

        Returns:
            {
                "success": true,
                "data": {
                    "original_sin": "123456782",
                    "cleaned_sin": "123456782",
                    "formatted_sin": "123-456-782",
                    "is_valid": true,
                    "error": null
                },
                "hints": {
                    "is_valid": true,
                    "formatted_sin": "123-456-782",
                    "message": "Valid Canadian SIN"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await validate_sin("123 456 782")
            if result["hints"]["is_valid"]:
                formatted = result["hints"]["formatted_sin"]
        """
        result = await validator.execute(sin=sin)
        return result.model_dump()
