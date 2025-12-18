"""
MADERA MCP - validate_email
Validation Tool - Validates email addresses

Execution time: ~1ms
Technique: Regex pattern matching
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import re
import logging

logger = logging.getLogger(__name__)


class EmailValidator(BaseTool):
    """Validates email addresses"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

        # RFC 5322 simplified pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_pattern.match(email))

    def _extract_parts(self, email: str) -> Dict[str, str]:
        """Extract local and domain parts"""
        if '@' in email:
            local, domain = email.split('@', 1)
            return {
                "local": local,
                "domain": domain,
                "tld": domain.split('.')[-1] if '.' in domain else None
            }
        return {"local": None, "domain": None, "tld": None}

    async def _execute(self, email: str) -> ToolResult:
        """
        Validate email address

        Args:
            email: Email address to validate

        Returns:
            ToolResult with validation result
        """
        # Clean input
        cleaned_email = email.strip().lower()

        # Validate
        is_valid = self._validate_email(cleaned_email)

        # Extract parts
        parts = self._extract_parts(cleaned_email) if is_valid else {}

        logger.info(
            f"Email validation: '{email}' -> "
            f"{'Valid' if is_valid else 'Invalid'}"
        )

        return ToolResult(
            success=True,
            data={
                "original_email": email,
                "normalized_email": cleaned_email,
                "is_valid": is_valid,
                "local_part": parts.get("local"),
                "domain": parts.get("domain"),
                "tld": parts.get("tld"),
                "error": None if is_valid else "Invalid email format"
            },
            hints={
                "is_valid": is_valid,
                "normalized_email": cleaned_email if is_valid else None,
                "message": "Valid email address" if is_valid else "Invalid email format"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register validate_email tool"""
    validator = EmailValidator()

    @mcp_server.tool()
    async def validate_email(email: str) -> Dict[str, Any]:
        """
        Validates email address format using RFC 5322 simplified pattern.

        Checks:
        - Valid characters in local part (before @)
        - Valid domain format
        - Valid TLD (top-level domain)

        Normalizes to lowercase.

        Args:
            email: Email address to validate

        Returns:
            {
                "success": true,
                "data": {
                    "original_email": "John.Doe@Example.COM",
                    "normalized_email": "john.doe@example.com",
                    "is_valid": true,
                    "local_part": "john.doe",
                    "domain": "example.com",
                    "tld": "com",
                    "error": null
                },
                "hints": {
                    "is_valid": true,
                    "normalized_email": "john.doe@example.com",
                    "message": "Valid email address"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await validate_email("user@example.com")
            if result["hints"]["is_valid"]:
                email = result["hints"]["normalized_email"]
        """
        result = await validator.execute(email=email)
        return result.model_dump()
