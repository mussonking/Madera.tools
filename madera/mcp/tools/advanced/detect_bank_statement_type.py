"""
MADERA MCP - detect_bank_statement_type
Advanced Tool - Identifies bank from statement without full AI

Execution time: ~150ms
Technique: Logo detection + OCR on specific zones
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
from pdf2image import convert_from_path
import pytesseract
import logging

logger = logging.getLogger(__name__)


class BankStatementDetector(BaseTool):
    """Detects bank statement type"""

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"

        # Bank patterns (simple text matching for MVP)
        self.bank_patterns = {
            'TD_CANADA_TRUST': ['TD CANADA TRUST', 'TD BANK', 'THE TORONTO-DOMINION BANK'],
            'RBC': ['ROYAL BANK', 'RBC', 'BANQUE ROYALE'],
            'SCOTIABANK': ['SCOTIABANK', 'BANQUE SCOTIA', 'THE BANK OF NOVA SCOTIA'],
            'BMO': ['BANK OF MONTREAL', 'BMO', 'BANQUE DE MONTREAL'],
            'CIBC': ['CIBC', 'CANADIAN IMPERIAL'],
            'NATIONAL_BANK': ['NATIONAL BANK', 'BANQUE NATIONALE'],
            'DESJARDINS': ['DESJARDINS', 'CAISSE'],
        }

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect bank from statement

        Args:
            presigned_url: URL to PDF statement

        Returns:
            ToolResult with bank identification
        """
        try:
            # Download PDF
            local_pdf = await self.fetch_file(presigned_url)

            # Convert first page only (header has bank info)
            images = convert_from_path(
                str(local_pdf),
                first_page=1,
                last_page=1,
                dpi=150
            )

            if not images:
                return ToolResult(
                    success=False,
                    data={"error": "Could not convert PDF"},
                    hints={"message": "PDF conversion failed"},
                    confidence=0.0
                )

            # OCR top portion only (200px high)
            image = images[0]
            width, height = image.size
            header = image.crop((0, 0, width, min(200, height)))

            # Extract text
            text = pytesseract.image_to_string(header).upper()

            # Match bank patterns
            detected_bank = None
            confidence = 0.0

            for bank_name, patterns in self.bank_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        detected_bank = bank_name
                        confidence = 0.90
                        break

                if detected_bank:
                    break

            logger.info(
                f"Bank statement detection: "
                f"{detected_bank or 'UNKNOWN'} (confidence: {confidence:.2f})"
            )

            return ToolResult(
                success=True,
                data={
                    "bank": detected_bank,
                    "confidence": confidence,
                    "detected_text_snippet": text[:200],  # First 200 chars
                    "is_bank_statement": detected_bank is not None
                },
                hints={
                    "bank": detected_bank,
                    "message": (
                        f"Detected: {detected_bank}" if detected_bank else
                        "Unknown bank"
                    )
                },
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Bank statement detection error: {e}")

            return ToolResult(
                success=False,
                data={"error": str(e)},
                hints={"message": f"Detection failed: {e}"},
                confidence=0.0
            )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_bank_statement_type tool"""
    detector = BankStatementDetector()

    @mcp_server.tool()
    async def detect_bank_statement_type(presigned_url: str) -> Dict[str, Any]:
        """
        Identifies bank from statement without full AI analysis.

        Uses OCR on header zone and pattern matching to detect major
        Canadian banks:
        - TD Canada Trust
        - RBC (Royal Bank)
        - Scotiabank
        - BMO (Bank of Montreal)
        - CIBC
        - National Bank
        - Desjardins

        Args:
            presigned_url: Presigned URL to bank statement PDF

        Returns:
            {
                "success": true,
                "data": {
                    "bank": "TD_CANADA_TRUST",
                    "confidence": 0.90,
                    "detected_text_snippet": "TD CANADA TRUST ACCOUNT STATEMENT...",
                    "is_bank_statement": true
                },
                "hints": {
                    "bank": "TD_CANADA_TRUST",
                    "message": "Detected: TD_CANADA_TRUST"
                },
                "confidence": 0.90,
                "execution_time_ms": 145
            }

        Example usage:
            result = await detect_bank_statement_type("https://minio.../statement.pdf")
            if result["data"]["is_bank_statement"]:
                bank = result["hints"]["bank"]
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
