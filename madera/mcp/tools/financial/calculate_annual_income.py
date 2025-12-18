"""
MADERA MCP - calculate_annual_income
Financial Tool - Calculates annual income from paystub/pay period

Execution time: ~1ms
Technique: Direct calculation (deterministic)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class AnnualIncomeCalculator(BaseTool):
    """Calculates annual income from pay period"""

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"

        # Pay periods per year
        self.periods_per_year = {
            'weekly': 52,
            'biweekly': 26,
            'semi-monthly': 24,
            'monthly': 12,
            'quarterly': 4,
            'annual': 1,
        }

    async def _execute(
        self,
        pay_amount: float,
        pay_period: str
    ) -> ToolResult:
        """
        Calculate annual income from pay period

        Args:
            pay_amount: Pay amount for the period
            pay_period: Period type (weekly, biweekly, etc.)

        Returns:
            ToolResult with annual income
        """
        period_key = pay_period.lower().strip()

        if period_key not in self.periods_per_year:
            return ToolResult(
                success=False,
                data={
                    "error": f"Unknown pay period: {pay_period}",
                    "valid_periods": list(self.periods_per_year.keys())
                },
                hints={
                    "message": f"Invalid period: {pay_period}"
                },
                confidence=0.0
            )

        # Calculate annual income
        multiplier = self.periods_per_year[period_key]
        annual_income = pay_amount * multiplier

        logger.info(
            f"Annual income: ${pay_amount} {pay_period} "
            f"= ${annual_income:,.2f} annually"
        )

        return ToolResult(
            success=True,
            data={
                "pay_amount": pay_amount,
                "pay_period": period_key,
                "periods_per_year": multiplier,
                "annual_income": annual_income,
                "monthly_income": annual_income / 12,
                "weekly_income": annual_income / 52
            },
            hints={
                "annual_income": annual_income,
                "monthly_income": annual_income / 12,
                "message": f"${annual_income:,.2f} annually"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register calculate_annual_income tool"""
    calculator = AnnualIncomeCalculator()

    @mcp_server.tool()
    async def calculate_annual_income(
        pay_amount: float,
        pay_period: str
    ) -> Dict[str, Any]:
        """
        Calculates annual income from paystub pay period.

        Provides EXACT calculation instead of AI estimation.

        Supported periods:
            - weekly: 52 periods/year
            - biweekly: 26 periods/year
            - semi-monthly: 24 periods/year
            - monthly: 12 periods/year
            - quarterly: 4 periods/year
            - annual: 1 period/year

        Args:
            pay_amount: Pay amount for the period
            pay_period: Period type (e.g., "biweekly")

        Returns:
            {
                "success": true,
                "data": {
                    "pay_amount": 2500.0,
                    "pay_period": "biweekly",
                    "periods_per_year": 26,
                    "annual_income": 65000.0,
                    "monthly_income": 5416.67,
                    "weekly_income": 1250.0
                },
                "hints": {
                    "annual_income": 65000.0,
                    "monthly_income": 5416.67,
                    "message": "$65,000.00 annually"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await calculate_annual_income(2500.0, "biweekly")
            annual = result["hints"]["annual_income"]  # 65000.0
            # Exact calculation vs AI approximation
        """
        result = await calculator.execute(
            pay_amount=pay_amount,
            pay_period=pay_period
        )
        return result.model_dump()
