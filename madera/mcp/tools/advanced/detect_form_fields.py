"""
MADERA MCP - detect_form_fields
Advanced Tool - Detects PDF form fields

Execution time: ~5ms
Technique: pypdf form field extraction
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class FormFieldDetector(BaseTool):
    """Detects PDF form fields"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect PDF form fields

        Args:
            presigned_url: URL to PDF file

        Returns:
            ToolResult with form fields
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)

            # Read PDF
            reader = PdfReader(local_pdf)

            # Extract form fields
            fields = []
            has_form = False

            if reader.get_fields():
                has_form = True

                for field_name, field_info in reader.get_fields().items():
                    field_type = field_info.get('/FT', 'Unknown')
                    field_value = field_info.get('/V', None)

                    # Convert field type to readable format
                    type_map = {
                        '/Tx': 'text',
                        '/Btn': 'button',
                        '/Ch': 'choice',
                        '/Sig': 'signature'
                    }

                    readable_type = type_map.get(field_type, str(field_type))

                    fields.append({
                        "name": field_name,
                        "type": readable_type,
                        "value": str(field_value) if field_value else None
                    })

            logger.info(
                f"Form field detection: "
                f"{len(fields)} fields found, is_form={has_form}"
            )

            return ToolResult(
                success=True,
                data={
                    "has_form": has_form,
                    "field_count": len(fields),
                    "fields": fields
                },
                hints={
                    "has_form": has_form,
                    "field_count": len(fields),
                    "message": (
                        f"Found {len(fields)} form fields" if has_form else
                        "No form fields detected"
                    )
                },
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"Form field detection error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Detection failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_form_fields tool"""
    detector = FormFieldDetector()

    @mcp_server.tool()
    async def detect_form_fields(presigned_url: str) -> Dict[str, Any]:
        """
        Detects PDF form fields (fillable forms).

        Extracts interactive form fields including:
        - Text fields
        - Buttons/checkboxes
        - Choice fields (dropdowns)
        - Signature fields

        Args:
            presigned_url: Presigned URL to PDF file

        Returns:
            {
                "success": true,
                "data": {
                    "has_form": true,
                    "field_count": 15,
                    "fields": [
                        {
                            "name": "applicant_name",
                            "type": "text",
                            "value": "John Doe"
                        },
                        {
                            "name": "signature_1",
                            "type": "signature",
                            "value": null
                        }
                    ]
                },
                "hints": {
                    "has_form": true,
                    "field_count": 15,
                    "message": "Found 15 form fields"
                },
                "confidence": 1.0,
                "execution_time_ms": 4
            }

        Example usage:
            result = await detect_form_fields("https://minio.../form.pdf")
            if result["data"]["has_form"]:
                fields = result["data"]["fields"]
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
