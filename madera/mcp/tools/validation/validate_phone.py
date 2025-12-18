"""
MADERA MCP - validate_phone
Validation Tool - Validates phone numbers

Execution time: ~1ms
Technique: Regex pattern matching (North American format)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class PhoneValidator(BaseTool):
    """Validates phone numbers"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _clean_phone(self, phone: str) -> str:
        """Remove all non-digit characters"""
        return re.sub(r'\D', '', phone)

    def _validate_nanp(self, digits: str) -> bool:
        """
        Validate North American Numbering Plan (NANP)

        Format: NXX-NXX-XXXX
        - N = 2-9 (first digit of area code and exchange)
        - X = 0-9
        """
        if len(digits) != 10:
            return False

        # Area code: First digit must be 2-9
        if digits[0] not in '23456789':
            return False

        # Exchange: First digit must be 2-9
        if digits[3] not in '23456789':
            return False

        return True

    def _format_phone(self, digits: str) -> str:
        """Format as (XXX) XXX-XXXX"""
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':
            # With country code
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        else:
            return digits

    async def _execute(self, phone: str, country: str = "CA") -> ToolResult:
        """
        Validate phone number

        Args:
            phone: Phone number to validate
            country: Country code (CA or US for NANP)

        Returns:
            ToolResult with validation result
        """
        # Clean input
        digits = self._clean_phone(phone)

        # Remove country code if present
        if len(digits) == 11 and digits[0] == '1':
            digits_without_country = digits[1:]
        else:
            digits_without_country = digits

        # Validate (NANP only for now)
        is_valid = False
        if country.upper() in ['CA', 'US']:
            is_valid = self._validate_nanp(digits_without_country)

        # Format
        formatted = self._format_phone(digits) if is_valid else None

        logger.info(
            f"Phone validation: '{phone}' -> "
            f"{'Valid' if is_valid else 'Invalid'}"
        )

        return ToolResult(
            success=True,
            data={
                "original_phone": phone,
                "cleaned_digits": digits,
                "formatted_phone": formatted,
                "country": country.upper(),
                "is_valid": is_valid,
                "error": None if is_valid else "Invalid phone number format"
            },
            hints={
                "is_valid": is_valid,
                "formatted_phone": formatted,
                "message": "Valid phone number" if is_valid else "Invalid phone number"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register validate_phone tool"""
    validator = PhoneValidator()

    @mcp_server.tool()
    async def validate_phone(
        phone: str,
        country: str = "CA"
    ) -> Dict[str, Any]:
        """
        Validates phone numbers for North American Numbering Plan (NANP).

        Supports Canadian and US phone numbers:
        - 10 digits: (XXX) XXX-XXXX
        - With country code: +1 (XXX) XXX-XXXX

        Validates NANP rules:
        - Area code first digit: 2-9
        - Exchange first digit: 2-9

        Args:
            phone: Phone number to validate (any format)
            country: Country code (CA or US)

        Returns:
            {
                "success": true,
                "data": {
                    "original_phone": "514-555-1234",
                    "cleaned_digits": "5145551234",
                    "formatted_phone": "(514) 555-1234",
                    "country": "CA",
                    "is_valid": true,
                    "error": null
                },
                "hints": {
                    "is_valid": true,
                    "formatted_phone": "(514) 555-1234",
                    "message": "Valid phone number"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await validate_phone("514-555-1234")
            if result["hints"]["is_valid"]:
                formatted = result["hints"]["formatted_phone"]
        """
        result = await validator.execute(
            phone=phone,
            country=country
        )
        return result.model_dump()
