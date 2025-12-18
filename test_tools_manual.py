"""
Quick manual test script for MADERA HINTS tools
Run with: docker compose exec madera-web python test_tools_manual.py
"""
import asyncio
import sys
from madera.mcp.server import mcp_server


async def test_tools_list():
    """Test that all 7 tools are registered"""
    print("\n🔍 Testing tool registration...")

    tools = await mcp_server.list_tools()

    print(f"\n✅ Registered tools: {len(tools)}/7")

    expected_tools = {
        "detect_blank_pages",
        "detect_id_card_sides",
        "identify_cra_document_type",
        "detect_tax_form_type",
        "detect_document_boundaries",
        "detect_fiscal_year",
        "assess_image_quality",
    }

    registered_names = {tool.name for tool in tools}

    for tool_name in expected_tools:
        if tool_name in registered_names:
            print(f"   ✅ {tool_name}")
        else:
            print(f"   ❌ {tool_name} - MISSING!")

    missing = expected_tools - registered_names
    extra = registered_names - expected_tools

    if missing:
        print(f"\n❌ Missing tools: {missing}")

    if extra:
        print(f"\n⚠️ Extra tools: {extra}")

    if not missing and not extra:
        print("\n✅ All 7 tools registered correctly!")
        return True

    return False


async def test_tool_schemas():
    """Test that all tools have proper schemas"""
    print("\n🔍 Testing tool schemas...")

    tools = await mcp_server.list_tools()

    all_valid = True

    for tool in tools:
        # Check required fields
        has_name = bool(tool.name)
        has_description = bool(tool.description)
        has_schema = hasattr(tool, 'input_schema') or hasattr(tool, 'inputSchema')

        if has_name and has_description and has_schema:
            print(f"   ✅ {tool.name}: Valid schema")
        else:
            print(f"   ❌ {tool.name}: Invalid schema")
            print(f"      - name: {has_name}")
            print(f"      - description: {has_description}")
            print(f"      - schema: {has_schema}")
            all_valid = False

    if all_valid:
        print("\n✅ All tool schemas are valid!")
    else:
        print("\n❌ Some tool schemas are invalid!")

    return all_valid


async def main():
    """Run all tests"""
    print("=" * 60)
    print("MADERA HINTS TOOLS - MANUAL TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Tool registration
    results.append(await test_tools_list())

    # Test 2: Tool schemas
    results.append(await test_tool_schemas())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
