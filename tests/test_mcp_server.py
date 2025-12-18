"""
MADERA MCP - MCP Server Integration Tests
Tests for FastMCP server and tool registration
"""
import pytest
from madera.mcp.server import mcp_server, init_mcp_server
from madera.mcp.registry import register_all_tools


class TestMCPServerInitialization:
    """Test MCP server initialization"""

    def test_server_created(self):
        """Test server instance is created"""
        assert mcp_server is not None
        assert mcp_server.name == "madera-tools"

    def test_server_has_tools(self):
        """Test server has registered tools"""
        tools = mcp_server.list_tools()
        assert len(tools) == 7  # 7 HINTS tools

    def test_all_hints_tools_registered(self):
        """Test all 7 HINTS tools are registered"""
        tools = mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "detect_blank_pages",
            "detect_id_card_sides",
            "identify_cra_document_type",
            "detect_tax_form_type",
            "detect_document_boundaries",
            "detect_fiscal_year",
            "assess_image_quality",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Tool {expected} not registered"


class TestToolMetadata:
    """Test tool metadata and descriptions"""

    def test_tools_have_descriptions(self):
        """Test all tools have proper descriptions"""
        tools = mcp_server.list_tools()

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 50  # Meaningful description

    def test_tools_have_parameters(self):
        """Test all tools have proper parameters"""
        tools = mcp_server.list_tools()

        for tool in tools:
            # All HINTS tools should have presigned_url parameter
            assert "presigned_url" in str(tool.input_schema)


class TestToolRegistry:
    """Test tool registry functionality"""

    def test_register_all_tools_idempotent(self):
        """Test registering tools multiple times doesn't duplicate"""
        # Get initial count
        initial_tools = mcp_server.list_tools()
        initial_count = len(initial_tools)

        # Register again (should not duplicate)
        register_all_tools(mcp_server)

        # Count should be the same
        final_tools = mcp_server.list_tools()
        assert len(final_tools) == initial_count


@pytest.mark.asyncio
class TestToolExecution:
    """Test tool execution through MCP server"""

    async def test_execute_blank_detector_via_mcp(self, sample_pdf_3_pages):
        """Test executing blank_page_detector through MCP"""
        tools = {tool.name: tool for tool in mcp_server.list_tools()}

        detect_blank_pages = tools.get("detect_blank_pages")
        assert detect_blank_pages is not None

        # Execute tool
        result = await detect_blank_pages.fn(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result is not None
        assert result["success"] is True
        assert "data" in result
        assert "hints" in result

    async def test_execute_all_tools_via_mcp(self, sample_pdf_3_pages):
        """Test all tools can be executed through MCP"""
        tools = {tool.name: tool for tool in mcp_server.list_tools()}
        pdf_url = f"file://{sample_pdf_3_pages}"

        for tool_name, tool in tools.items():
            result = await tool.fn(presigned_url=pdf_url)

            assert result is not None, f"Tool {tool_name} returned None"
            assert "success" in result, f"Tool {tool_name} missing success field"
            assert result["success"] is True, f"Tool {tool_name} failed"

    async def test_tool_return_format(self, sample_pdf_3_pages):
        """Test all tools return proper format"""
        tools = {tool.name: tool for tool in mcp_server.list_tools()}
        pdf_url = f"file://{sample_pdf_3_pages}"

        for tool_name, tool in tools.items():
            result = await tool.fn(presigned_url=pdf_url)

            # Check required fields
            assert "success" in result
            assert "data" in result
            assert "hints" in result
            assert "confidence" in result
            assert "execution_time_ms" in result

            # Check types
            assert isinstance(result["success"], bool)
            assert isinstance(result["data"], dict)
            assert isinstance(result["hints"], dict)
            assert isinstance(result["confidence"], (int, float))
            assert isinstance(result["execution_time_ms"], int)


@pytest.mark.asyncio
class TestErrorHandlingInMCP:
    """Test error handling through MCP"""

    async def test_invalid_url_returns_error(self):
        """Test tools return error for invalid URL"""
        tools = {tool.name: tool for tool in mcp_server.list_tools()}
        invalid_url = "file:///nonexistent_file.pdf"

        blank_detector = tools["detect_blank_pages"]
        result = await blank_detector.fn(presigned_url=invalid_url)

        # Should gracefully fail
        assert result["success"] is False
        assert "error" in result


class TestServerConfiguration:
    """Test server configuration"""

    def test_server_name(self):
        """Test server has correct name"""
        assert mcp_server.name == "madera-tools"

    def test_init_function_returns_server(self):
        """Test init function returns server"""
        server = init_mcp_server()
        assert server is not None
        assert server.name == "madera-tools"
