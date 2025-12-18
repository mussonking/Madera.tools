"""
Test Phase 3 Tools
Tests all 18 Phase 3 tools (Financial + Validation + Advanced)
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add madera to path
sys.path.insert(0, str(Path(__file__).parent))

from madera.mcp.server import mcp_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_financial_tools():
    """Test 5 Financial Calculation tools"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING FINANCIAL CALCULATION TOOLS (5 tools)")
    logger.info("=" * 60)

    # 1. calculate_annual_income
    logger.info("\n1. Testing calculate_annual_income...")
    result = await mcp_server.call_tool(
        "calculate_annual_income",
        {"pay_amount": 2500.0, "pay_period": "biweekly"}
    )
    assert result["success"]
    assert result["data"]["annual_income"] == 65000.0
    logger.info(f"✅ calculate_annual_income: ${result['data']['annual_income']}/year")

    # 2. calculate_gds_tds
    logger.info("\n2. Testing calculate_gds_tds...")
    result = await mcp_server.call_tool(
        "calculate_gds_tds",
        {
            "annual_income": 80000.0,
            "mortgage_payment": 2000.0,
            "property_tax": 300.0,
            "heating": 100.0,
            "condo_fees": 200.0,
            "other_debts": 500.0
        }
    )
    assert result["success"]
    logger.info(f"✅ calculate_gds_tds: GDS={result['data']['gds_ratio']}%, TDS={result['data']['tds_ratio']}%")

    # 3. calculate_ltv
    logger.info("\n3. Testing calculate_ltv...")
    result = await mcp_server.call_tool(
        "calculate_ltv",
        {"property_value": 500000.0, "loan_amount": 450000.0}
    )
    assert result["success"]
    logger.info(f"✅ calculate_ltv: {result['data']['ltv_ratio']}% (CMHC: ${result['data']['cmhc_insurance']})")

    # 4. average_t4_income
    logger.info("\n4. Testing average_t4_income...")
    result = await mcp_server.call_tool(
        "average_t4_income",
        {"t4_amounts": [65000.0, 70000.0, 72000.0], "years": [2022, 2023, 2024]}
    )
    assert result["success"]
    logger.info(f"✅ average_t4_income: ${result['data']['average_income']} ({result['data']['trend']})")

    # 5. estimate_monthly_payment
    logger.info("\n5. Testing estimate_monthly_payment...")
    result = await mcp_server.call_tool(
        "estimate_monthly_payment",
        {"principal": 400000.0, "annual_rate": 5.25, "amortization_years": 25}
    )
    assert result["success"]
    logger.info(f"✅ estimate_monthly_payment: ${result['data']['monthly_payment']}/month")


async def test_validation_tools():
    """Test 5 Data Validation tools"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING DATA VALIDATION TOOLS (5 tools)")
    logger.info("=" * 60)

    # 1. validate_sin
    logger.info("\n1. Testing validate_sin...")
    result = await mcp_server.call_tool(
        "validate_sin",
        {"sin": "123 456 782"}
    )
    assert result["success"]
    logger.info(f"✅ validate_sin: {result['data']['is_valid']} ({result['data']['formatted_sin']})")

    # 2. validate_postal_code
    logger.info("\n2. Testing validate_postal_code...")
    result = await mcp_server.call_tool(
        "validate_postal_code",
        {"postal_code": "K1A0B1"}
    )
    assert result["success"]
    logger.info(f"✅ validate_postal_code: {result['data']['is_valid']} ({result['data']['formatted_postal_code']})")

    # 3. validate_phone
    logger.info("\n3. Testing validate_phone...")
    result = await mcp_server.call_tool(
        "validate_phone",
        {"phone": "514-555-1234"}
    )
    assert result["success"]
    logger.info(f"✅ validate_phone: {result['data']['is_valid']} ({result['data']['formatted_phone']})")

    # 4. validate_email
    logger.info("\n4. Testing validate_email...")
    result = await mcp_server.call_tool(
        "validate_email",
        {"email": "John.Doe@Example.COM"}
    )
    assert result["success"]
    logger.info(f"✅ validate_email: {result['data']['is_valid']} ({result['data']['normalized_email']})")

    # 5. validate_date_range
    logger.info("\n5. Testing validate_date_range...")
    result = await mcp_server.call_tool(
        "validate_date_range",
        {"start_date": "2024-01-01", "end_date": "2024-12-31"}
    )
    assert result["success"]
    logger.info(f"✅ validate_date_range: {result['data']['is_valid']} ({result['data']['days_difference']} days)")


async def test_advanced_tools():
    """Test 8 Advanced tools (simplified tests - no real files)"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING ADVANCED TOOLS (8 tools)")
    logger.info("=" * 60)

    # Note: Advanced tools require real PDF files via presigned URLs
    # For now, we just verify they're callable and handle errors gracefully

    logger.info("\n1. Testing generate_thumbnail (error handling)...")
    result = await mcp_server.call_tool(
        "generate_thumbnail",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    # Should fail but gracefully
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ generate_thumbnail: Error handling works")

    logger.info("\n2. Testing detect_bank_statement_type (error handling)...")
    result = await mcp_server.call_tool(
        "detect_bank_statement_type",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ detect_bank_statement_type: Error handling works")

    logger.info("\n3. Testing detect_form_fields (error handling)...")
    result = await mcp_server.call_tool(
        "detect_form_fields",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ detect_form_fields: Error handling works")

    logger.info("\n4. Testing count_signatures (error handling)...")
    result = await mcp_server.call_tool(
        "count_signatures",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ count_signatures: Error handling works")

    logger.info("\n5. Testing extract_urls (error handling)...")
    result = await mcp_server.call_tool(
        "extract_urls",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ extract_urls: Error handling works")

    logger.info("\n6. Testing compress_pdf (error handling)...")
    result = await mcp_server.call_tool(
        "compress_pdf",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ compress_pdf: Error handling works")

    logger.info("\n7. Testing pdf_to_images (error handling)...")
    result = await mcp_server.call_tool(
        "pdf_to_images",
        {"presigned_url": "https://fake.url/test.pdf"}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ pdf_to_images: Error handling works")

    logger.info("\n8. Testing images_to_pdf (error handling)...")
    result = await mcp_server.call_tool(
        "images_to_pdf",
        {"image_urls": ["https://fake.url/image1.png"]}
    )
    assert "error" in result["data"] or not result["success"]
    logger.info("✅ images_to_pdf: Error handling works")


async def main():
    """Run all Phase 3 tests"""
    logger.info("=" * 60)
    logger.info("PHASE 3 TOOLS TEST SUITE")
    logger.info("=" * 60)

    try:
        await test_financial_tools()
        await test_validation_tools()
        await test_advanced_tools()

        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL PHASE 3 TESTS PASSED (18/18 tools)")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
