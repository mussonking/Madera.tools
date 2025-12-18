"""
MADERA MCP - count_signatures
Advanced Tool - Counts signature fields/zones in PDF

Execution time: ~5ms
Technique: Form field detection + heuristics
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class SignatureCounter(BaseTool):
    """Counts signature zones in PDF"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Count signature fields/zones

        Args:
            presigned_url: URL to PDF file

        Returns:
            ToolResult with signature count
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)

            # Read PDF
            reader = PdfReader(local_pdf)

            # Count signature fields
            signature_fields = []

            if reader.get_fields():
                for field_name, field_info in reader.get_fields().items():
                    field_type = field_info.get('/FT', '')

                    # Signature field type
                    if field_type == '/Sig':
                        signature_fields.append({
                            "name": field_name,
                            "signed": field_info.get('/V') is not None
                        })

                    # Also check field name for signature indicators
                    elif 'signature' in field_name.lower() or 'sign' in field_name.lower():
                        signature_fields.append({
                            "name": field_name,
                            "signed": field_info.get('/V') is not None
                        })

            signature_count = len(signature_fields)
            signed_count = sum(1 for f in signature_fields if f['signed'])
            unsigned_count = signature_count - signed_count

            logger.info(
                f"Signature count: {signature_count} total "
                f"({signed_count} signed, {unsigned_count} unsigned)"
            )

            return ToolResult(
                success=True,
                data={
                    "signature_count": signature_count,
                    "signed_count": signed_count,
                    "unsigned_count": unsigned_count,
                    "signature_fields": signature_fields,
                    "all_signed": signature_count > 0 and unsigned_count == 0
                },
                hints={
                    "signature_count": signature_count,
                    "all_signed": signature_count > 0 and unsigned_count == 0,
                    "message": (
                        f"{signature_count} signature zones "
                        f"({signed_count} signed, {unsigned_count} unsigned)"
                    )
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"Signature counting error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Counting failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register count_signatures tool"""
    counter = SignatureCounter()

    @mcp_server.tool()
    async def count_signatures(presigned_url: str) -> Dict[str, Any]:
        """
        Counts signature fields/zones in a PDF.

        Detects both:
        - Explicit signature form fields (/Sig type)
        - Fields with "signature" or "sign" in the name

        Indicates which signatures are filled vs empty.

        Args:
            presigned_url: Presigned URL to PDF file

        Returns:
            {
                "success": true,
                "data": {
                    "signature_count": 3,
                    "signed_count": 2,
                    "unsigned_count": 1,
                    "signature_fields": [
                        {"name": "applicant_signature", "signed": true},
                        {"name": "co_applicant_signature", "signed": true},
                        {"name": "witness_signature", "signed": false}
                    ],
                    "all_signed": false
                },
                "hints": {
                    "signature_count": 3,
                    "all_signed": false,
                    "message": "3 signature zones (2 signed, 1 unsigned)"
                },
                "confidence": 1.0,
                "execution_time_ms": 3
            }

        Example usage:
            result = await count_signatures("https://minio.../contract.pdf")
            if result["data"]["all_signed"]:
                print("Document fully signed!")
        """
        result = await counter.execute(presigned_url=presigned_url)
        return result.model_dump()
