"""
MADERA MCP - calculate_ltv
Financial Tool - Calculates Loan-to-Value ratio

Execution time: ~1ms
Technique: Direct calculation
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class LtvCalculator(BaseTool):
    """Calculates Loan-to-Value ratio"""

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"

    async def _execute(
        self,
        loan_amount: float,
        property_value: float
    ) -> ToolResult:
        """
        Calculate LTV ratio

        Args:
            loan_amount: Mortgage loan amount
            property_value: Property appraisal value

        Returns:
            ToolResult with LTV ratio
        """
        if property_value <= 0:
            return ToolResult(
                success=False,
                data={"error": "Property value must be > 0"},
                hints={"message": "Invalid property value"},
                confidence=0.0
            )

        # LTV = (Loan / Property Value) * 100
        ltv_ratio = (loan_amount / property_value) * 100

        # Canadian CMHC insurance thresholds
        needs_cmhc = ltv_ratio > 80
        cmhc_premium_rate = 0.0

        if ltv_ratio > 95:
            cmhc_premium_rate = 4.00
        elif ltv_ratio > 90:
            cmhc_premium_rate = 3.10
        elif ltv_ratio > 85:
            cmhc_premium_rate = 2.80
        elif ltv_ratio > 80:
            cmhc_premium_rate = 2.40

        cmhc_premium = loan_amount * (cmhc_premium_rate / 100)

        logger.info(
            f"LTV: {ltv_ratio:.2f}% "
            f"(CMHC: {'Yes' if needs_cmhc else 'No'})"
        )

        return ToolResult(
            success=True,
            data={
                "loan_amount": loan_amount,
                "property_value": property_value,
                "ltv_ratio": round(ltv_ratio, 2),
                "down_payment": property_value - loan_amount,
                "down_payment_percent": round((1 - (loan_amount / property_value)) * 100, 2),
                "needs_cmhc_insurance": needs_cmhc,
                "cmhc_premium_rate": cmhc_premium_rate,
                "cmhc_premium": cmhc_premium
            },
            hints={
                "ltv_ratio": round(ltv_ratio, 2),
                "needs_cmhc": needs_cmhc,
                "message": f"LTV: {ltv_ratio:.2f}%"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register calculate_ltv tool"""
    calculator = LtvCalculator()

    @mcp_server.tool()
    async def calculate_ltv(
        loan_amount: float,
        property_value: float
    ) -> Dict[str, Any]:
        """
        Calculates Loan-to-Value (LTV) ratio.

        LTV = (Loan Amount / Property Value) * 100

        Canadian CMHC insurance requirements:
        - LTV <= 80%: No insurance required
        - LTV 80-85%: 2.40% premium
        - LTV 85-90%: 2.80% premium
        - LTV 90-95%: 3.10% premium
        - LTV > 95%: 4.00% premium

        Args:
            loan_amount: Mortgage loan amount
            property_value: Property appraisal value

        Returns:
            {
                "success": true,
                "data": {
                    "loan_amount": 400000.0,
                    "property_value": 500000.0,
                    "ltv_ratio": 80.0,
                    "down_payment": 100000.0,
                    "down_payment_percent": 20.0,
                    "needs_cmhc_insurance": false,
                    "cmhc_premium_rate": 0.0,
                    "cmhc_premium": 0.0
                },
                "hints": {
                    "ltv_ratio": 80.0,
                    "needs_cmhc": false,
                    "message": "LTV: 80.00%"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await calculate_ltv(
                loan_amount=450000,
                property_value=500000
            )
            ltv = result["hints"]["ltv_ratio"]  # 90.0
            needs_cmhc = result["hints"]["needs_cmhc"]  # true
        """
        result = await calculator.execute(
            loan_amount=loan_amount,
            property_value=property_value
        )
        return result.model_dump()
