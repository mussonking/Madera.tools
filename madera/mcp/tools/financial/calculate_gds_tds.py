"""
MADERA MCP - calculate_gds_tds
Financial Tool - Calculates GDS and TDS ratios for mortgage qualification

Execution time: ~1ms
Technique: Direct calculation (Canada mortgage standards)
"""
from typing import Dict, Any
from madera.mcp.tools.base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class GdsTdsCalculator(BaseTool):
    """Calculates GDS/TDS ratios for mortgage qualification"""

    def __init__(self):
        super().__init__()
        self.tool_class = "hypothecaire"

    async def _execute(
        self,
        annual_income: float,
        mortgage_payment: float,
        property_tax: float,
        heating: float,
        condo_fees: float = 0.0,
        other_debts: float = 0.0
    ) -> ToolResult:
        """
        Calculate GDS and TDS ratios

        Args:
            annual_income: Gross annual income
            mortgage_payment: Monthly mortgage payment (P+I)
            property_tax: Monthly property tax
            heating: Monthly heating cost
            condo_fees: Monthly condo fees (if applicable)
            other_debts: Monthly other debts

        Returns:
            ToolResult with GDS/TDS ratios
        """
        monthly_income = annual_income / 12

        # GDS = (Mortgage + Property Tax + Heating + 50% Condo) / Income
        housing_costs = mortgage_payment + property_tax + heating + (condo_fees * 0.5)
        gds_ratio = (housing_costs / monthly_income) * 100

        # TDS = GDS + Other Debts
        total_debts = housing_costs + other_debts
        tds_ratio = (total_debts / monthly_income) * 100

        # Canadian standards (CMHC guidelines)
        gds_qualified = gds_ratio <= 39
        tds_qualified = tds_ratio <= 44

        logger.info(
            f"GDS: {gds_ratio:.1f}% (max 39%), "
            f"TDS: {tds_ratio:.1f}% (max 44%)"
        )

        return ToolResult(
            success=True,
            data={
                "annual_income": annual_income,
                "monthly_income": monthly_income,
                "housing_costs": housing_costs,
                "total_debts": total_debts,
                "gds_ratio": round(gds_ratio, 2),
                "tds_ratio": round(tds_ratio, 2),
                "gds_qualified": gds_qualified,
                "tds_qualified": tds_qualified,
                "fully_qualified": gds_qualified and tds_qualified,
                "gds_max": 39,
                "tds_max": 44
            },
            hints={
                "gds_ratio": round(gds_ratio, 2),
                "tds_ratio": round(tds_ratio, 2),
                "qualified": gds_qualified and tds_qualified,
                "message": f"GDS: {gds_ratio:.1f}%, TDS: {tds_ratio:.1f}%"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register calculate_gds_tds tool"""
    calculator = GdsTdsCalculator()

    @mcp_server.tool()
    async def calculate_gds_tds(
        annual_income: float,
        mortgage_payment: float,
        property_tax: float,
        heating: float,
        condo_fees: float = 0.0,
        other_debts: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates GDS and TDS ratios for mortgage qualification.

        Canadian mortgage standards (CMHC):
        - GDS (Gross Debt Service): Housing costs / Income (max 39%)
        - TDS (Total Debt Service): Total debts / Income (max 44%)

        GDS = (Mortgage + Property Tax + Heating + 50% Condo) / Income
        TDS = GDS + Other Debts / Income

        Args:
            annual_income: Gross annual income
            mortgage_payment: Monthly mortgage payment (Principal + Interest)
            property_tax: Monthly property tax
            heating: Monthly heating cost
            condo_fees: Monthly condo fees (optional, default 0)
            other_debts: Monthly other debts (optional, default 0)

        Returns:
            {
                "success": true,
                "data": {
                    "annual_income": 80000.0,
                    "monthly_income": 6666.67,
                    "housing_costs": 2100.0,
                    "total_debts": 2400.0,
                    "gds_ratio": 31.5,
                    "tds_ratio": 36.0,
                    "gds_qualified": true,
                    "tds_qualified": true,
                    "fully_qualified": true,
                    "gds_max": 39,
                    "tds_max": 44
                },
                "hints": {
                    "gds_ratio": 31.5,
                    "tds_ratio": 36.0,
                    "qualified": true,
                    "message": "GDS: 31.5%, TDS: 36.0%"
                },
                "confidence": 1.0,
                "execution_time_ms": 1
            }

        Example usage:
            result = await calculate_gds_tds(
                annual_income=80000,
                mortgage_payment=1800,
                property_tax=250,
                heating=50,
                condo_fees=100,
                other_debts=300
            )
            qualified = result["hints"]["qualified"]  # true
        """
        result = await calculator.execute(
            annual_income=annual_income,
            mortgage_payment=mortgage_payment,
            property_tax=property_tax,
            heating=heating,
            condo_fees=condo_fees,
            other_debts=other_debts
        )
        return result.model_dump()
