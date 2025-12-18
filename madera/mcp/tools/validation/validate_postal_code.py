"""
MADERA MCP - validate_postal_code
Validation Tool - Validates postal codes (Canadian, US, etc.)

Execution time: ~1ms
Technique: Regex pattern matching
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class PostalCodeValidator(BaseTool):
    """Validates postal codes"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

        # Postal code patterns
        self.patterns = {
            "CA": r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$',  # Canadian: K1A 0B1
            "US": r'^\d{5}(-\d{4})?$',             # US: 12345 or 12345-6789
        }

    def _clean_postal_code(self, postal_code: str) -> str:
        """Clean and uppercase"""
        return postal_code.strip().upper()

    def _detect_country(self, postal_code: str) -> str:
        """Detect country from format"""
        for country, pattern in self.patterns.items():
            if re.match(pattern, postal_code):
                return country
        return "UNKNOWN"

    def _format_postal_code(self, postal_code: str, country: str) -> str:
        """Format according to country standards"""
        if country == "CA":
            # Canadian: K1A 0B1
            cleaned = re.sub(r'\s', '', postal_code)
            if len(cleaned) == 6:
                return f"{cleaned[0:3]} {cleaned[3:6]}"
        elif country == "US":
            # US: 12345 or 12345-6789
            cleaned = re.sub(r'[\s\-]', '', postal_code)
            if len(cleaned) == 5:
                return cleaned
            elif len(cleaned) == 9:
                return f"{cleaned[0:5]}-{cleaned[5:9]}"

        return postal_code

    async def _execute(self, postal_code: str, country: str = None) -> ToolResult:
        """
        Validate postal code

        Args:
            postal_code: Postal code to validate
            country: Country code (CA, US) - auto-detected if not provided

        Returns:
            ToolResult with validation result
        """
        # Clean input
        cleaned = self._clean_postal_code(postal_code)

        # Detect or validate country
        if country is None:
            country = self._detect_country(cleaned)
        else:
            country = country.upper()

        # Validate
        is_valid = False
        if country in self.patterns:
            is_valid = bool(re.match(self.patterns[country], cleaned))

        # Format
        formatted = self._format_postal_code(cleaned, country) if is_valid else None

        logger.info(
            f"Postal code validation: '{postal_code}' -> "
            f"{country} {'Valid' if is_valid else 'Invalid'}"
        )

        return ToolResult(
            success=True,
            data={
                "original_postal_code": postal_code,
                "cleaned_postal_code": cleaned,
                "formatted_postal_code": formatted,
                "country": country,
                "is_valid": is_valid,
                "error": None if is_valid else f"Invalid {country} postal code format"
            },
            hints={
                "is_valid": is_valid,
                "formatted_postal_code": formatted,
                "country": country,
                "message": f"Valid {country} postal code" if is_valid else "Invalid postal code"
            },
            confidence=1.0 if country != "UNKNOWN" else 0.5
        )


# Register tool with MCP server
def register(mcp_server):
    """Register validate_postal_code tool"""
    validator = PostalCodeValidator()

    @mcp_server.tool()
    async def validate_postal_code(
        postal_code: str,
        country: str = None
    ) -> Dict[str, Any]:
        """
        Validates postal codes for Canada and United States.

        Supports:
        - Canadian: K1A 0B1 (letter-digit-letter digit-letter-digit)
        - US: 12345 or 12345-6789 (ZIP or ZIP+4)

        Auto-detects country if not provided.

        Args:
            postal_code: Postal code to validate
            country: Optional country code (CA or US)

        Returns:
            {
                "success": true,
                "data": {
                    "original_postal_code": "K1A0B1",
                    "cleaned_postal_code": "K1A0B1",
                    "formatted_postal_code": "K1A 0B1",
                    "country": "CA",
                    "is_valid": true,
                    "error": null
                },
                "hints": {
                    "is_valid": true,
                    "formatted_postal_code": "K1A 0B1",
                    "country": "CA",
                    "message": "Valid CA postal code"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await validate_postal_code("K1A 0B1")
            if result["hints"]["is_valid"]:
                formatted = result["hints"]["formatted_postal_code"]
        """
        result = await validator.execute(
            postal_code=postal_code,
            country=country
        )
        return result.model_dump()
