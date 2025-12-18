"""
MADERA MCP - average_t4_income
Financial Tool - Averages T4 income over multiple years

Execution time: ~1ms
Technique: Direct calculation
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class T4IncomeAverager(BaseTool):
    """Averages T4 income over years"""

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"

    async def _execute(
        self,
        t4_amounts: List[float],
        years: List[int] = None
    ) -> ToolResult:
        """
        Average T4 income over multiple years

        Args:
            t4_amounts: List of T4 amounts (2-3 years typically)
            years: Optional list of years (for documentation)

        Returns:
            ToolResult with average income
        """
        if not t4_amounts:
            return ToolResult(
                success=False,
                data={"error": "No T4 amounts provided"},
                hints={"message": "Need at least one T4 amount"},
                confidence=0.0
            )

        # Calculate average
        average_income = sum(t4_amounts) / len(t4_amounts)
        total_income = sum(t4_amounts)
        min_income = min(t4_amounts)
        max_income = max(t4_amounts)

        # Calculate trend
        if len(t4_amounts) >= 2:
            latest = t4_amounts[-1]
            previous = t4_amounts[-2]
            trend_percent = ((latest - previous) / previous) * 100
            trend = "increasing" if trend_percent > 0 else ("decreasing" if trend_percent < 0 else "stable")
        else:
            trend_percent = 0
            trend = "single_year"

        logger.info(
            f"Averaged {len(t4_amounts)} T4s: ${average_income:,.2f} "
            f"(trend: {trend})"
        )

        return ToolResult(
            success=True,
            data={
                "t4_amounts": t4_amounts,
                "years": years if years else list(range(2024 - len(t4_amounts) + 1, 2025)),
                "average_income": round(average_income, 2),
                "total_income": round(total_income, 2),
                "min_income": round(min_income, 2),
                "max_income": round(max_income, 2),
                "count": len(t4_amounts),
                "trend": trend,
                "trend_percent": round(trend_percent, 2)
            },
            hints={
                "average_income": round(average_income, 2),
                "trend": trend,
                "message": f"${average_income:,.2f} average over {len(t4_amounts)} years"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register average_t4_income tool"""
    averager = T4IncomeAverager()

    @mcp_server.tool()
    async def average_t4_income(
        t4_amounts: List[float],
        years: List[int] = None
    ) -> Dict[str, Any]:
        """
        Averages T4 employment income over multiple years.

        Used for mortgage qualification when applicant has varying income.
        Lenders typically require 2-year average for self-employed or
        commission-based workers.

        Args:
            t4_amounts: List of T4 amounts (typically 2-3 years)
            years: Optional list of years (for documentation)

        Returns:
            {
                "success": true,
                "data": {
                    "t4_amounts": [65000.0, 70000.0, 72000.0],
                    "years": [2022, 2023, 2024],
                    "average_income": 69000.0,
                    "total_income": 207000.0,
                    "min_income": 65000.0,
                    "max_income": 72000.0,
                    "count": 3,
                    "trend": "increasing",
                    "trend_percent": 2.86
                },
                "hints": {
                    "average_income": 69000.0,
                    "trend": "increasing",
                    "message": "$69,000.00 average over 3 years"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await average_t4_income(
                t4_amounts=[65000, 70000, 72000],
                years=[2022, 2023, 2024]
            )
            avg_income = result["hints"]["average_income"]  # 69000.0
        """
        result = await averager.execute(
            t4_amounts=t4_amounts,
            years=years
        )
        return result.model_dump()
