# Visual AI Tools for MADERA MCP
"""
MADERA Visual AI Tools

Browser automation and visual testing tools for debugging and testing.

Modules:
- screenshot: Core browser control, navigation, screenshots
- console_capture: Browser console log capture and analysis
- network_monitor: HTTP request monitoring and HAR export
- visual_helpers: Visibility checks, waiting, interaction helpers
- report_builder: AI-ready test reports and bug hypothesis

Usage:
    These tools are registered with the MCP server via registry.py
    and called through the MCP protocol.

Example workflow:
    1. visual_navigate("http://example.com")
    2. visual_console_start()
    3. visual_network_start()
    4. visual_click("#some-button")
    5. visual_screenshot(name="after_click")
    6. visual_report_build("Test Report", "Clicked button and captured state")
"""

__all__ = [
    "screenshot",
    "console_capture",
    "network_monitor",
    "visual_helpers",
    "report_builder",
]
