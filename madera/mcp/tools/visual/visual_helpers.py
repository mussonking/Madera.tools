"""
MADERA Visual AI - Visual Helpers
Additional visibility, interaction, and waiting helpers for visual testing
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# MCP Tool Registration
def register(mcp):
    """Register visual helper tools with MCP server"""

    @mcp.tool()
    async def visual_is_visible(selector: str) -> dict:
        """
        Check if an element is visible on page

        Args:
            selector: CSS selector to check

        Returns:
            {
                "success": true,
                "visible": true/false,
                "selector": "...",
                "exists": true/false
            }
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            element = await ai.page.query_selector(selector)
            if not element:
                return {
                    "success": True,
                    "visible": False,
                    "exists": False,
                    "selector": selector
                }

            is_visible = await element.is_visible()
            return {
                "success": True,
                "visible": is_visible,
                "exists": True,
                "selector": selector
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_wait_for(
        selector: str,
        state: str = "visible",
        timeout: int = 30000
    ) -> dict:
        """
        Wait for an element to reach a specific state

        Args:
            selector: CSS selector to wait for
            state: State to wait for (visible, hidden, attached, detached)
            timeout: Maximum wait time in milliseconds (default: 30000)
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await ai.page.wait_for_selector(
                selector,
                state=state,
                timeout=timeout
            )
            return {
                "success": True,
                "selector": selector,
                "state": state,
                "message": f"Element reached '{state}' state"
            }
        except Exception as e:
            return {
                "success": False,
                "selector": selector,
                "state": state,
                "error": str(e)
            }

    @mcp.tool()
    async def visual_wait_animations(timeout: int = 5000) -> dict:
        """
        Wait for CSS animations to complete

        Useful before taking screenshots to avoid capturing mid-animation states.

        Args:
            timeout: Maximum wait time in milliseconds (default: 5000)
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            # Wait for animations using JavaScript
            await ai.page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const animations = document.getAnimations();
                        if (animations.length === 0) {
                            resolve();
                            return;
                        }
                        Promise.all(animations.map(a => a.finished))
                            .then(resolve)
                            .catch(resolve);
                    });
                }
            """)

            # Additional small delay for any CSS transitions
            await asyncio.sleep(0.1)

            return {
                "success": True,
                "message": "Animations completed"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_wait_full_load(timeout: int = 30000) -> dict:
        """
        Wait for page to be fully loaded (network idle)

        Waits for:
        - DOM content loaded
        - All network requests to settle
        - No pending XHR/Fetch requests

        Args:
            timeout: Maximum wait time in milliseconds (default: 30000)
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await ai.page.wait_for_load_state("networkidle", timeout=timeout)
            return {
                "success": True,
                "message": "Page fully loaded (network idle)"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_scroll_to(
        selector: str = None,
        x: int = None,
        y: int = None
    ) -> dict:
        """
        Scroll to an element or position

        Args:
            selector: CSS selector to scroll to (optional)
            x: X coordinate to scroll to (optional)
            y: Y coordinate to scroll to (optional)

        Either provide selector OR x/y coordinates.
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            if selector:
                element = await ai.page.query_selector(selector)
                if not element:
                    return {"success": False, "error": f"Element not found: {selector}"}
                await element.scroll_into_view_if_needed()
                return {
                    "success": True,
                    "scrolled_to": "element",
                    "selector": selector
                }
            elif x is not None and y is not None:
                await ai.page.evaluate(f"window.scrollTo({x}, {y})")
                return {
                    "success": True,
                    "scrolled_to": "position",
                    "x": x,
                    "y": y
                }
            else:
                return {"success": False, "error": "Provide either selector or x/y coordinates"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_hover(selector: str) -> dict:
        """
        Hover over an element

        Args:
            selector: CSS selector to hover over
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await ai.page.hover(selector)
            return {
                "success": True,
                "hovered": selector
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_get_text(selector: str) -> dict:
        """
        Get text content of an element

        Args:
            selector: CSS selector
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            element = await ai.page.query_selector(selector)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}

            text = await element.text_content()
            inner_text = await element.inner_text()

            return {
                "success": True,
                "selector": selector,
                "text_content": text,
                "inner_text": inner_text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_get_attribute(selector: str, attribute: str) -> dict:
        """
        Get an attribute value from an element

        Args:
            selector: CSS selector
            attribute: Attribute name to get (e.g., "href", "src", "data-id")
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            element = await ai.page.query_selector(selector)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}

            value = await element.get_attribute(attribute)

            return {
                "success": True,
                "selector": selector,
                "attribute": attribute,
                "value": value
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_count_elements(selector: str) -> dict:
        """
        Count elements matching a selector

        Args:
            selector: CSS selector
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            elements = await ai.page.query_selector_all(selector)
            return {
                "success": True,
                "selector": selector,
                "count": len(elements)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_press_key(key: str, selector: str = None) -> dict:
        """
        Press a keyboard key

        Args:
            key: Key to press (e.g., "Enter", "Escape", "Tab", "ArrowDown")
            selector: Optional element to focus before pressing (CSS selector)
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            if selector:
                await ai.page.click(selector)

            await ai.page.keyboard.press(key)

            return {
                "success": True,
                "key": key,
                "selector": selector
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_get_viewport() -> dict:
        """
        Get current viewport size
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            viewport = ai.page.viewport_size
            return {
                "success": True,
                "width": viewport["width"] if viewport else None,
                "height": viewport["height"] if viewport else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_set_viewport(width: int, height: int) -> dict:
        """
        Set viewport size

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await ai.page.set_viewport_size({"width": width, "height": height})
            return {
                "success": True,
                "width": width,
                "height": height
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_get_url() -> dict:
        """
        Get current page URL
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        return {
            "success": True,
            "url": ai.page.url
        }

    @mcp.tool()
    async def visual_go_back() -> dict:
        """Navigate back in browser history"""
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await ai.page.go_back()
            return {
                "success": True,
                "url": ai.page.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def visual_reload() -> dict:
        """Reload current page"""
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await ai.page.reload()
            return {
                "success": True,
                "url": ai.page.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    logger.info("Visual helper tools registered")
