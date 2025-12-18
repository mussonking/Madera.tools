"""
MADERA Visual AI - Screenshot Tool
Takes screenshots of web pages for visual testing and validation
"""
import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import playwright
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")


class VisualAI:
    """Visual AI tool for screenshot capture and UI validation"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self.screenshots_dir = Path("/tmp/madera-screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    async def start(self, headless: bool = True):
        """Start browser instance"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
        logger.info("Browser started")

    async def stop(self):
        """Stop browser instance"""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser stopped")

    async def navigate(self, url: str, wait_for: str = "load") -> dict:
        """Navigate to a URL"""
        if not self.page:
            await self.start()

        try:
            response = await self.page.goto(url, wait_until=wait_for)
            return {
                "success": True,
                "url": self.page.url,
                "status": response.status if response else None,
                "title": await self.page.title()
            }
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {"success": False, "error": str(e)}

    async def screenshot(
        self,
        name: str = None,
        selector: str = None,
        full_page: bool = False
    ) -> dict:
        """Take a screenshot"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name or 'screenshot'}_{timestamp}.png"
        filepath = self.screenshots_dir / filename

        try:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    await element.screenshot(path=str(filepath))
                else:
                    return {"success": False, "error": f"Selector not found: {selector}"}
            else:
                await self.page.screenshot(path=str(filepath), full_page=full_page)

            # Read as base64 for embedding
            with open(filepath, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode()

            return {
                "success": True,
                "path": str(filepath),
                "filename": filename,
                "base64": b64_data[:100] + "..." if len(b64_data) > 100 else b64_data,
                "size": filepath.stat().st_size
            }
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_element_info(self, selector: str) -> dict:
        """Get information about an element"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        try:
            element = await self.page.query_selector(selector)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}

            # Get bounding box
            bbox = await element.bounding_box()

            # Get text content
            text = await element.text_content()

            # Get attributes
            tag_name = await element.evaluate("el => el.tagName")

            # Check visibility
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()

            return {
                "success": True,
                "selector": selector,
                "tag": tag_name,
                "text": text[:200] if text else None,
                "visible": is_visible,
                "enabled": is_enabled,
                "bbox": bbox
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def check_elements_exist(self, selectors: list[str]) -> dict:
        """Check if multiple elements exist on page"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        results = {}
        for selector in selectors:
            element = await self.page.query_selector(selector)
            results[selector] = {
                "exists": element is not None,
                "visible": await element.is_visible() if element else False
            }

        all_found = all(r["exists"] for r in results.values())
        return {
            "success": True,
            "all_found": all_found,
            "results": results
        }

    async def click(self, selector: str) -> dict:
        """Click an element"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await self.page.click(selector)
            return {"success": True, "clicked": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill(self, selector: str, value: str) -> dict:
        """Fill an input field"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await self.page.fill(selector, value)
            return {"success": True, "filled": selector, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def select(self, selector: str, value: str) -> dict:
        """Select an option from dropdown"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        try:
            await self.page.select_option(selector, value)
            return {"success": True, "selected": selector, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_page_content(self) -> dict:
        """Get page HTML content"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        content = await self.page.content()
        return {
            "success": True,
            "url": self.page.url,
            "title": await self.page.title(),
            "content_length": len(content),
            "content_preview": content[:1000]
        }

    async def evaluate(self, script: str) -> dict:
        """Execute JavaScript on page"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}

        try:
            result = await self.page.evaluate(script)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_visual_ai: Optional[VisualAI] = None


async def get_visual_ai() -> VisualAI:
    """Get or create VisualAI instance"""
    global _visual_ai
    if _visual_ai is None:
        _visual_ai = VisualAI()
    return _visual_ai


# MCP Tool Registration
def register(mcp):
    """Register visual AI tools with MCP server"""

    @mcp.tool()
    async def visual_navigate(url: str, wait_for: str = "load") -> dict:
        """
        Navigate browser to a URL

        Args:
            url: URL to navigate to
            wait_for: Wait condition (load, domcontentloaded, networkidle)
        """
        ai = await get_visual_ai()
        return await ai.navigate(url, wait_for)

    @mcp.tool()
    async def visual_screenshot(
        name: str = "screenshot",
        selector: str = None,
        full_page: bool = False
    ) -> dict:
        """
        Take a screenshot of current page or element

        Args:
            name: Name for screenshot file
            selector: CSS selector for specific element (optional)
            full_page: Capture full page scroll
        """
        ai = await get_visual_ai()
        return await ai.screenshot(name, selector, full_page)

    @mcp.tool()
    async def visual_check_elements(selectors: list[str]) -> dict:
        """
        Check if elements exist on page

        Args:
            selectors: List of CSS selectors to check
        """
        ai = await get_visual_ai()
        return await ai.check_elements_exist(selectors)

    @mcp.tool()
    async def visual_get_element(selector: str) -> dict:
        """
        Get information about an element

        Args:
            selector: CSS selector
        """
        ai = await get_visual_ai()
        return await ai.get_element_info(selector)

    @mcp.tool()
    async def visual_click(selector: str) -> dict:
        """
        Click an element on page

        Args:
            selector: CSS selector to click
        """
        ai = await get_visual_ai()
        return await ai.click(selector)

    @mcp.tool()
    async def visual_fill(selector: str, value: str) -> dict:
        """
        Fill an input field

        Args:
            selector: CSS selector of input
            value: Value to fill
        """
        ai = await get_visual_ai()
        return await ai.fill(selector, value)

    @mcp.tool()
    async def visual_select(selector: str, value: str) -> dict:
        """
        Select option from dropdown

        Args:
            selector: CSS selector of select element
            value: Value to select
        """
        ai = await get_visual_ai()
        return await ai.select(selector, value)

    @mcp.tool()
    async def visual_evaluate(script: str) -> dict:
        """
        Execute JavaScript on page

        Args:
            script: JavaScript code to execute
        """
        ai = await get_visual_ai()
        return await ai.evaluate(script)

    @mcp.tool()
    async def visual_stop() -> dict:
        """Stop browser and cleanup"""
        global _visual_ai
        if _visual_ai:
            await _visual_ai.stop()
            _visual_ai = None
        return {"success": True, "message": "Browser stopped"}

    logger.info("✅ Visual AI tools registered")
