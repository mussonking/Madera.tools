"""
MADERA MCP Server - Main initialization
Uses FastMCP for simplified tool registration
"""
from mcp.server.fastmcp import FastMCP
from madera.config import settings
import logging
import sys
import os

# Disable all logging to stderr for MCP stdio mode
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[logging.NullHandler()]
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp_server = FastMCP("madera-tools")


def init_mcp_server():
    """
    Initialize and register all MCP tools

    Tools are registered via the registry system which
    auto-discovers all tool modules
    """
    # Suppress tool registration output but keep logging
    devnull = open(os.devnull, 'w')
    old_stdout = sys.stdout
    sys.stdout = devnull

    try:
        # Register all tools from registry
        from madera.mcp.registry import register_all_tools
        register_all_tools(mcp_server)
    finally:
        # Always restore stdout, even if registration fails
        sys.stdout = old_stdout
        devnull.close()

    return mcp_server


# Create server instance
server = init_mcp_server()


if __name__ == "__main__":
    """Run MCP server in stdio mode"""
    mcp_server.run()
