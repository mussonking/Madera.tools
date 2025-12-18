"""
MADERA Visual AI - Console Capture Tool
Captures and analyzes browser console logs for debugging and testing
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

# Console log storage
_console_logs: list[dict] = []
_capturing: bool = False

# Error patterns for detection
ERROR_PATTERNS = {
    "network": [
        r"failed to load",
        r"net::err_",
        r"fetch.*failed",
        r"xmlhttprequest.*error",
        r"cors.*blocked",
        r"404.*not found",
        r"500.*internal server",
    ],
    "javascript": [
        r"uncaught.*error",
        r"syntaxerror",
        r"typeerror",
        r"referenceerror",
        r"rangeerror",
        r"cannot read property",
        r"undefined is not",
        r"null is not",
    ],
    "react": [
        r"react.*error",
        r"component.*unmounted",
        r"invalid hook call",
        r"maximum update depth",
        r"cannot update.*unmounted",
    ],
    "vue": [
        r"vue.*warn",
        r"vue.*error",
        r"unknown custom element",
    ],
    "security": [
        r"content security policy",
        r"blocked.*mixed content",
        r"insecure.*request",
    ],
    "deprecation": [
        r"deprecated",
        r"will be removed",
        r"legacy.*feature",
    ],
}


class ConsoleCapture:
    """Browser console capture and analysis"""

    def __init__(self):
        self.logs: list[dict] = []
        self.capturing: bool = False
        self._page = None

    async def start(self, page) -> dict:
        """
        Start capturing console messages

        Args:
            page: Playwright page instance
        """
        self._page = page
        self.logs = []
        self.capturing = True

        # Set up console listener
        page.on("console", self._on_console_message)
        page.on("pageerror", self._on_page_error)

        logger.info("Console capture started")
        return {
            "success": True,
            "message": "Console capture started",
            "timestamp": datetime.now().isoformat()
        }

    def _on_console_message(self, msg):
        """Handle console message event"""
        if not self.capturing:
            return

        log_entry = {
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.now().isoformat(),
            "location": {
                "url": msg.location.get("url", "") if hasattr(msg, "location") else "",
                "line": msg.location.get("lineNumber", 0) if hasattr(msg, "location") else 0,
            },
            "args": [],
        }

        # Try to get args
        try:
            for arg in msg.args:
                try:
                    log_entry["args"].append(str(arg))
                except Exception:
                    pass
        except Exception:
            pass

        self.logs.append(log_entry)

    def _on_page_error(self, error):
        """Handle page error event"""
        if not self.capturing:
            return

        self.logs.append({
            "type": "pageerror",
            "text": str(error),
            "timestamp": datetime.now().isoformat(),
            "location": {},
            "args": [],
        })

    async def stop(self) -> dict:
        """Stop capturing console messages"""
        self.capturing = False

        # Remove listeners if possible
        if self._page:
            try:
                self._page.remove_listener("console", self._on_console_message)
                self._page.remove_listener("pageerror", self._on_page_error)
            except Exception:
                pass

        logger.info(f"Console capture stopped. {len(self.logs)} messages captured.")
        return {
            "success": True,
            "message": "Console capture stopped",
            "total_logs": len(self.logs)
        }

    def get_errors(self, include_warnings: bool = False) -> dict:
        """
        Get only error (and optionally warning) messages

        Args:
            include_warnings: Include warning messages
        """
        error_types = ["error", "pageerror"]
        if include_warnings:
            error_types.append("warning")

        errors = [
            log for log in self.logs
            if log["type"] in error_types
        ]

        return {
            "success": True,
            "errors": errors,
            "count": len(errors),
            "has_errors": len(errors) > 0
        }

    def get_all(self, log_type: Optional[str] = None) -> dict:
        """
        Get all captured console messages

        Args:
            log_type: Filter by type (log, info, warning, error, pageerror)
        """
        if log_type:
            filtered = [log for log in self.logs if log["type"] == log_type]
        else:
            filtered = self.logs

        # Group by type
        by_type = defaultdict(int)
        for log in self.logs:
            by_type[log["type"]] += 1

        return {
            "success": True,
            "logs": filtered,
            "count": len(filtered),
            "total": len(self.logs),
            "by_type": dict(by_type)
        }

    def detect_patterns(self) -> dict:
        """
        Detect known error patterns in console logs

        Returns categorized issues for debugging
        """
        detected = defaultdict(list)

        for log in self.logs:
            text_lower = log["text"].lower()

            for category, patterns in ERROR_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        detected[category].append({
                            "pattern": pattern,
                            "message": log["text"][:200],
                            "type": log["type"],
                            "timestamp": log["timestamp"]
                        })
                        break  # One match per category per log

        # Generate summary
        issues = []
        for category, matches in detected.items():
            issues.append({
                "category": category,
                "count": len(matches),
                "severity": "high" if category in ["javascript", "security"] else "medium",
                "matches": matches[:5]  # Limit to 5 examples
            })

        return {
            "success": True,
            "issues": issues,
            "total_issues": sum(len(m) for m in detected.values()),
            "categories_affected": list(detected.keys()),
            "has_critical": any(
                cat in detected for cat in ["javascript", "security"]
            )
        }

    def clear(self) -> dict:
        """Clear all captured logs"""
        count = len(self.logs)
        self.logs = []
        return {
            "success": True,
            "message": f"Cleared {count} logs"
        }

    def search(self, query: str) -> dict:
        """
        Search console logs for specific text

        Args:
            query: Search query string
        """
        query_lower = query.lower()
        matches = [
            log for log in self.logs
            if query_lower in log["text"].lower()
        ]

        return {
            "success": True,
            "query": query,
            "matches": matches,
            "count": len(matches)
        }


# Singleton instance
_console_capture: Optional[ConsoleCapture] = None


def get_console_capture() -> ConsoleCapture:
    """Get or create ConsoleCapture instance"""
    global _console_capture
    if _console_capture is None:
        _console_capture = ConsoleCapture()
    return _console_capture


# MCP Tool Registration
def register(mcp):
    """Register console capture tools with MCP server"""

    @mcp.tool()
    async def visual_console_start() -> dict:
        """
        Start capturing browser console messages

        Must be called after visual_navigate. Captures all console.log,
        console.error, warnings, and page errors.
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started. Call visual_navigate first."}

        capture = get_console_capture()
        return await capture.start(ai.page)

    @mcp.tool()
    async def visual_console_get_errors(include_warnings: bool = False) -> dict:
        """
        Get console errors (and optionally warnings)

        Args:
            include_warnings: Include warning messages in results
        """
        capture = get_console_capture()
        return capture.get_errors(include_warnings)

    @mcp.tool()
    async def visual_console_get_all(log_type: str = None) -> dict:
        """
        Get all captured console messages

        Args:
            log_type: Filter by type (log, info, warning, error, pageerror)
        """
        capture = get_console_capture()
        return capture.get_all(log_type)

    @mcp.tool()
    async def visual_console_detect_patterns() -> dict:
        """
        Detect known error patterns in console logs

        Analyzes logs for common error patterns like:
        - Network errors (CORS, 404, fetch failures)
        - JavaScript errors (TypeError, ReferenceError)
        - React/Vue framework errors
        - Security issues
        - Deprecation warnings
        """
        capture = get_console_capture()
        return capture.detect_patterns()

    @mcp.tool()
    async def visual_console_clear() -> dict:
        """Clear all captured console logs"""
        capture = get_console_capture()
        return capture.clear()

    @mcp.tool()
    async def visual_console_search(query: str) -> dict:
        """
        Search console logs for specific text

        Args:
            query: Text to search for in console messages
        """
        capture = get_console_capture()
        return capture.search(query)

    logger.info("Console capture tools registered")
