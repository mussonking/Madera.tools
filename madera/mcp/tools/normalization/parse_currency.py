"""
MADERA MCP - parse_currency
Core Tool - Parses currency amounts from strings

Execution time: ~2ms
Technique: Regex extraction + normalization
"""
from typing import Dict, Any, Optional
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class CurrencyParser(BaseTool):
    """Parses currency amounts from text"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _parse_amount(self, amount_string: str) -> Optional[float]:
        """
        Parse amount from string

        Examples:
            "$15,000.50" -> 15000.50
            "15 000,50 $" -> 15000.50
            "(1,234.56)" -> -1234.56 (accounting notation)
        """
        # Remove currency symbols
        cleaned = amount_string.strip()
        cleaned = re.sub(r'[$€£¥CAD]', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        # Check for negative (accounting notation with parentheses)
        is_negative = cleaned.startswith('(') and cleaned.endswith(')')
        if is_negative:
            cleaned = cleaned[1:-1]

        # Remove spaces
        cleaned = cleaned.replace(' ', '')

        # Determine decimal separator
        # Common patterns:
        # - "1,234.56" (North American)
        # - "1.234,56" (European)
        # - "1 234,56" (French Canadian)

        # Count dots and commas
        dot_count = cleaned.count('.')
        comma_count = cleaned.count(',')

        if dot_count == 0 and comma_count == 0:
            # Simple integer
            try:
                value = float(cleaned)
            except ValueError:
                return None
        elif dot_count == 1 and comma_count == 0:
            # Likely "1234.56" format
            try:
                value = float(cleaned)
            except ValueError:
                return None
        elif comma_count == 1 and dot_count == 0:
            # Could be "1234,56" or "1,234"
            # If comma is followed by exactly 2 digits, it's a decimal separator
            if re.search(r',\d{2}$', cleaned):
                # "1234,56" -> "1234.56"
                cleaned = cleaned.replace(',', '.')
            else:
                # "1,234" -> "1234"
                cleaned = cleaned.replace(',', '')

            try:
                value = float(cleaned)
            except ValueError:
                return None
        else:
            # Multiple separators: "1,234.56" or "1.234,56"
            # Last separator is decimal, others are thousands
            if cleaned.rfind('.') > cleaned.rfind(','):
                # "1,234.56" format
                cleaned = cleaned.replace(',', '')
            else:
                # "1.234,56" format
                cleaned = cleaned.replace('.', '').replace(',', '.')

            try:
                value = float(cleaned)
            except ValueError:
                return None

        if is_negative:
            value = -value

        return value

    async def _execute(self, amount_string: str, currency: str = "CAD") -> ToolResult:
        """
        Parse currency amount from string

        Args:
            amount_string: String containing amount (e.g., "$15,000.50")
            currency: Currency code (default: CAD)

        Returns:
            ToolResult with parsed amount
        """
        parsed_amount = self._parse_amount(amount_string)

        if parsed_amount is None:
            return ToolResult(
                success=False,
                data={
                    "error": f"Could not parse amount: {amount_string}",
                    "original": amount_string
                },
                hints={
                    "message": f"Invalid amount format: {amount_string}"
                },
                confidence=0.0
            )

        logger.info(
            f"Parsed currency: '{amount_string}' -> {parsed_amount} {currency}"
        )

        return ToolResult(
            success=True,
            data={
                "original": amount_string,
                "amount": parsed_amount,
                "currency": currency,
                "formatted": f"{parsed_amount:,.2f}"
            },
            hints={
                "amount": parsed_amount,
                "currency": currency,
                "message": f"{parsed_amount:,.2f} {currency}"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register parse_currency tool"""
    parser = CurrencyParser()

    @mcp_server.tool()
    async def parse_currency(amount_string: str, currency: str = "CAD") -> Dict[str, Any]:
        """
        Parses currency amounts from strings.

        This tool handles various currency formats:
        - North American: $1,234.56
        - European: 1.234,56 €
        - French Canadian: 1 234,50 $
        - Accounting negatives: ($1,234.56) or (1,234.56)

        Provides exact numerical value for calculations.

        Args:
            amount_string: String containing amount
            currency: Currency code (default: "CAD")

        Returns:
            {
                "success": true,
                "data": {
                    "original": "$15,000.50",
                    "amount": 15000.50,
                    "currency": "CAD",
                    "formatted": "15,000.50"
                },
                "hints": {
                    "amount": 15000.50,
                    "currency": "CAD",
                    "message": "15,000.50 CAD"
                },
                "confidence": 1.0,
                "execution_time_ms": 2
            }

        Example usage:
            result = await parse_currency("15 000,50 $")
            amount = result["hints"]["amount"]  # 15000.50
            # Use exact number instead of AI approximation
        """
        result = await parser.execute(
            amount_string=amount_string,
            currency=currency
        )
        return result.model_dump()
