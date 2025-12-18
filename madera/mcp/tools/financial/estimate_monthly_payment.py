"""
MADERA MCP - estimate_monthly_payment
Financial Tool - Estimates monthly mortgage payment

Execution time: ~1ms
Technique: Canadian mortgage calculation formula
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class MonthlyPaymentEstimator(BaseTool):
    """Estimates monthly mortgage payment"""

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"

    async def _execute(
        self,
        principal: float,
        annual_rate: float,
        amortization_years: int = 25,
        payment_frequency: str = "monthly"
    ) -> ToolResult:
        """
        Estimate monthly mortgage payment using Canadian formula

        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (e.g., 5.25 for 5.25%)
            amortization_years: Total amortization period (default 25)
            payment_frequency: Payment frequency (monthly, biweekly, weekly)

        Returns:
            ToolResult with payment estimates
        """
        if principal <= 0:
            return ToolResult(
                success=False,
                data={"error": "Principal must be > 0"},
                hints={"message": "Invalid principal amount"},
                confidence=0.0
            )

        if annual_rate < 0 or annual_rate > 30:
            return ToolResult(
                success=False,
                data={"error": "Interest rate must be between 0-30%"},
                hints={"message": "Invalid interest rate"},
                confidence=0.0
            )

        # Canadian mortgage formula (semi-annual compounding)
        # Monthly rate = (1 + annual_rate/2)^(1/6) - 1
        semi_annual_rate = annual_rate / 100 / 2
        monthly_rate = ((1 + semi_annual_rate) ** (1/6)) - 1

        # Number of payments
        frequency_map = {
            "monthly": 12,
            "biweekly": 26,
            "weekly": 52
        }

        if payment_frequency not in frequency_map:
            payment_frequency = "monthly"

        payments_per_year = frequency_map[payment_frequency]
        total_payments = amortization_years * payments_per_year

        # Calculate payment per frequency
        if payment_frequency == "monthly":
            rate_per_period = monthly_rate
        elif payment_frequency == "biweekly":
            rate_per_period = monthly_rate / 2.16667  # Approximate biweekly
        else:  # weekly
            rate_per_period = monthly_rate / 4.33333  # Approximate weekly

        # Payment formula: P * [r(1+r)^n] / [(1+r)^n - 1]
        if rate_per_period == 0:
            payment = principal / total_payments
        else:
            payment = principal * (rate_per_period * ((1 + rate_per_period) ** total_payments)) / \
                     (((1 + rate_per_period) ** total_payments) - 1)

        # Calculate all frequencies for comparison
        monthly_payment = payment if payment_frequency == "monthly" else payment * payments_per_year / 12
        biweekly_payment = payment if payment_frequency == "biweekly" else monthly_payment * 12 / 26
        weekly_payment = payment if payment_frequency == "weekly" else monthly_payment * 12 / 52

        # Total interest over life of loan
        total_paid = payment * total_payments
        total_interest = total_paid - principal

        logger.info(
            f"Mortgage payment estimate: ${monthly_payment:,.2f}/month "
            f"(${principal:,.0f} @ {annual_rate}% over {amortization_years} years)"
        )

        return ToolResult(
            success=True,
            data={
                "principal": round(principal, 2),
                "annual_rate": annual_rate,
                "amortization_years": amortization_years,
                "payment_frequency": payment_frequency,
                "payment": round(payment, 2),
                "monthly_payment": round(monthly_payment, 2),
                "biweekly_payment": round(biweekly_payment, 2),
                "weekly_payment": round(weekly_payment, 2),
                "total_payments": total_payments,
                "total_paid": round(total_paid, 2),
                "total_interest": round(total_interest, 2),
                "interest_percent": round((total_interest / principal) * 100, 2)
            },
            hints={
                "monthly_payment": round(monthly_payment, 2),
                "total_interest": round(total_interest, 2),
                "message": f"${monthly_payment:,.2f}/month (${total_interest:,.0f} total interest)"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register estimate_monthly_payment tool"""
    estimator = MonthlyPaymentEstimator()

    @mcp_server.tool()
    async def estimate_monthly_payment(
        principal: float,
        annual_rate: float,
        amortization_years: int = 25,
        payment_frequency: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Estimates monthly mortgage payment using Canadian mortgage formula.

        Uses Canadian semi-annual compounding method. Calculates payment
        for different frequencies (monthly, biweekly, weekly) and total
        interest over the life of the loan.

        Args:
            principal: Loan amount (e.g., 400000 for $400k)
            annual_rate: Annual interest rate (e.g., 5.25 for 5.25%)
            amortization_years: Total amortization period (default 25)
            payment_frequency: Payment frequency (monthly, biweekly, weekly)

        Returns:
            {
                "success": true,
                "data": {
                    "principal": 400000.0,
                    "annual_rate": 5.25,
                    "amortization_years": 25,
                    "payment_frequency": "monthly",
                    "payment": 2389.13,
                    "monthly_payment": 2389.13,
                    "biweekly_payment": 1102.21,
                    "weekly_payment": 551.11,
                    "total_payments": 300,
                    "total_paid": 716739.0,
                    "total_interest": 316739.0,
                    "interest_percent": 79.18
                },
                "hints": {
                    "monthly_payment": 2389.13,
                    "total_interest": 316739.0,
                    "message": "$2,389.13/month ($316,739 total interest)"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await estimate_monthly_payment(
                principal=400000,
                annual_rate=5.25,
                amortization_years=25
            )
            payment = result["hints"]["monthly_payment"]  # 2389.13
        """
        result = await estimator.execute(
            principal=principal,
            annual_rate=annual_rate,
            amortization_years=amortization_years,
            payment_frequency=payment_frequency
        )
        return result.model_dump()
