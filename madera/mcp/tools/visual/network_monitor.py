"""
MADERA Visual AI - Network Monitor Tool
Monitors HTTP requests/responses and exports HAR files for debugging
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Browser network request monitoring"""

    def __init__(self):
        self.requests: list[dict] = []
        self.responses: list[dict] = []
        self.monitoring: bool = False
        self._page = None
        self._start_time: Optional[datetime] = None
        self.output_dir = Path("/tmp/madera-network")
        self.output_dir.mkdir(exist_ok=True)

    async def start(self, page) -> dict:
        """
        Start monitoring network requests

        Args:
            page: Playwright page instance
        """
        self._page = page
        self.requests = []
        self.responses = []
        self.monitoring = True
        self._start_time = datetime.now()

        # Set up network listeners
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

        logger.info("Network monitoring started")
        return {
            "success": True,
            "message": "Network monitoring started",
            "timestamp": self._start_time.isoformat()
        }

    def _on_request(self, request):
        """Handle request event"""
        if not self.monitoring:
            return

        req_data = {
            "id": id(request),
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "resource_type": request.resource_type,
            "timestamp": datetime.now().isoformat(),
            "post_data": None,
            "status": "pending",
        }

        # Try to get POST data
        try:
            req_data["post_data"] = request.post_data
        except Exception:
            pass

        self.requests.append(req_data)

    def _on_response(self, response):
        """Handle response event"""
        if not self.monitoring:
            return

        resp_data = {
            "id": id(response.request),
            "url": response.url,
            "status": response.status,
            "status_text": response.status_text,
            "headers": dict(response.headers),
            "timestamp": datetime.now().isoformat(),
            "ok": response.ok,
        }

        self.responses.append(resp_data)

        # Update request status
        for req in self.requests:
            if req["url"] == response.url and req["status"] == "pending":
                req["status"] = "completed"
                req["response_status"] = response.status
                break

    def _on_request_failed(self, request):
        """Handle failed request event"""
        if not self.monitoring:
            return

        # Update request status
        for req in self.requests:
            if req["url"] == request.url and req["status"] == "pending":
                req["status"] = "failed"
                req["failure_text"] = request.failure if hasattr(request, "failure") else "Unknown error"
                break

    async def stop(self) -> dict:
        """Stop monitoring network requests"""
        self.monitoring = False

        # Remove listeners if possible
        if self._page:
            try:
                self._page.remove_listener("request", self._on_request)
                self._page.remove_listener("response", self._on_response)
                self._page.remove_listener("requestfailed", self._on_request_failed)
            except Exception:
                pass

        logger.info(f"Network monitoring stopped. {len(self.requests)} requests captured.")
        return {
            "success": True,
            "message": "Network monitoring stopped",
            "total_requests": len(self.requests),
            "total_responses": len(self.responses)
        }

    def get_failed(self) -> dict:
        """Get failed requests (HTTP errors or network failures)"""
        failed = []

        for req in self.requests:
            # Network failures
            if req["status"] == "failed":
                failed.append({
                    "url": req["url"],
                    "method": req["method"],
                    "type": "network_failure",
                    "error": req.get("failure_text", "Unknown"),
                    "timestamp": req["timestamp"]
                })
            # HTTP errors (4xx, 5xx)
            elif req.get("response_status", 200) >= 400:
                failed.append({
                    "url": req["url"],
                    "method": req["method"],
                    "type": "http_error",
                    "status": req["response_status"],
                    "timestamp": req["timestamp"]
                })

        return {
            "success": True,
            "failed_requests": failed,
            "count": len(failed),
            "has_failures": len(failed) > 0
        }

    def get_all(
        self,
        resource_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> dict:
        """
        Get all captured requests

        Args:
            resource_type: Filter by type (xhr, fetch, document, stylesheet, image, etc.)
            status_filter: Filter by status (pending, completed, failed)
        """
        filtered = self.requests

        if resource_type:
            filtered = [r for r in filtered if r["resource_type"] == resource_type]

        if status_filter:
            filtered = [r for r in filtered if r["status"] == status_filter]

        # Stats by type
        by_type = defaultdict(int)
        for req in self.requests:
            by_type[req["resource_type"]] += 1

        # Stats by status code
        by_status = defaultdict(int)
        for req in self.requests:
            status = req.get("response_status", 0)
            if status == 0:
                by_status["pending"] += 1
            elif status < 300:
                by_status["2xx"] += 1
            elif status < 400:
                by_status["3xx"] += 1
            elif status < 500:
                by_status["4xx"] += 1
            else:
                by_status["5xx"] += 1

        return {
            "success": True,
            "requests": filtered,
            "count": len(filtered),
            "total": len(self.requests),
            "by_type": dict(by_type),
            "by_status": dict(by_status)
        }

    def get_by_url_pattern(self, pattern: str) -> dict:
        """
        Get requests matching URL pattern

        Args:
            pattern: Substring to search in URLs
        """
        matches = [
            req for req in self.requests
            if pattern.lower() in req["url"].lower()
        ]

        return {
            "success": True,
            "pattern": pattern,
            "matches": matches,
            "count": len(matches)
        }

    def export_har(self, filename: Optional[str] = None) -> dict:
        """
        Export captured requests as HAR (HTTP Archive) file

        Args:
            filename: Output filename (optional)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_{timestamp}.har"

        filepath = self.output_dir / filename

        # Build HAR structure
        har = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "MADERA Visual AI",
                    "version": "1.0"
                },
                "entries": []
            }
        }

        # Match requests with responses
        response_map = {r["url"]: r for r in self.responses}

        for req in self.requests:
            response = response_map.get(req["url"], {})

            entry = {
                "startedDateTime": req["timestamp"],
                "request": {
                    "method": req["method"],
                    "url": req["url"],
                    "headers": [
                        {"name": k, "value": v}
                        for k, v in req["headers"].items()
                    ],
                    "postData": {
                        "text": req.get("post_data", "")
                    } if req.get("post_data") else None
                },
                "response": {
                    "status": response.get("status", 0),
                    "statusText": response.get("status_text", ""),
                    "headers": [
                        {"name": k, "value": v}
                        for k, v in response.get("headers", {}).items()
                    ]
                },
                "cache": {},
                "timings": {
                    "send": 0,
                    "wait": 0,
                    "receive": 0
                }
            }

            har["log"]["entries"].append(entry)

        # Write HAR file
        with open(filepath, "w") as f:
            json.dump(har, f, indent=2)

        return {
            "success": True,
            "path": str(filepath),
            "filename": filename,
            "entries": len(har["log"]["entries"])
        }

    def clear(self) -> dict:
        """Clear all captured network data"""
        count = len(self.requests)
        self.requests = []
        self.responses = []
        return {
            "success": True,
            "message": f"Cleared {count} requests"
        }

    def get_api_calls(self, api_base: str = "/api") -> dict:
        """
        Get only API calls (useful for debugging API issues)

        Args:
            api_base: Base path for API calls (default: /api)
        """
        api_calls = [
            req for req in self.requests
            if api_base in req["url"]
        ]

        # Match with responses
        response_map = {r["url"]: r for r in self.responses}

        results = []
        for req in api_calls:
            resp = response_map.get(req["url"], {})
            results.append({
                "method": req["method"],
                "url": req["url"],
                "status": resp.get("status", req.get("response_status", "pending")),
                "ok": resp.get("ok", False) if resp else (req["status"] == "completed"),
                "timestamp": req["timestamp"]
            })

        return {
            "success": True,
            "api_calls": results,
            "count": len(results),
            "failed": len([r for r in results if not r.get("ok", True)])
        }


# Singleton instance
_network_monitor: Optional[NetworkMonitor] = None


def get_network_monitor() -> NetworkMonitor:
    """Get or create NetworkMonitor instance"""
    global _network_monitor
    if _network_monitor is None:
        _network_monitor = NetworkMonitor()
    return _network_monitor


# MCP Tool Registration
def register(mcp):
    """Register network monitor tools with MCP server"""

    @mcp.tool()
    async def visual_network_start() -> dict:
        """
        Start monitoring network requests

        Must be called after visual_navigate. Captures all HTTP requests,
        responses, and failures.
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        if not ai.page:
            return {"success": False, "error": "Browser not started. Call visual_navigate first."}

        monitor = get_network_monitor()
        return await monitor.start(ai.page)

    @mcp.tool()
    async def visual_network_get_failed() -> dict:
        """
        Get failed network requests

        Returns requests with HTTP errors (4xx, 5xx) or network failures
        """
        monitor = get_network_monitor()
        return monitor.get_failed()

    @mcp.tool()
    async def visual_network_get_all(
        resource_type: str = None,
        status_filter: str = None
    ) -> dict:
        """
        Get all captured network requests

        Args:
            resource_type: Filter by type (xhr, fetch, document, stylesheet, image)
            status_filter: Filter by status (pending, completed, failed)
        """
        monitor = get_network_monitor()
        return monitor.get_all(resource_type, status_filter)

    @mcp.tool()
    async def visual_network_get_api_calls(api_base: str = "/api") -> dict:
        """
        Get only API calls for debugging

        Args:
            api_base: Base path for API calls (default: /api)
        """
        monitor = get_network_monitor()
        return monitor.get_api_calls(api_base)

    @mcp.tool()
    async def visual_network_export_har(filename: str = None) -> dict:
        """
        Export captured requests as HAR file

        HAR files can be imported into browser DevTools for analysis.

        Args:
            filename: Output filename (optional, auto-generated if not provided)
        """
        monitor = get_network_monitor()
        return monitor.export_har(filename)

    @mcp.tool()
    async def visual_network_clear() -> dict:
        """Clear all captured network data"""
        monitor = get_network_monitor()
        return monitor.clear()

    @mcp.tool()
    async def visual_network_search(pattern: str) -> dict:
        """
        Search network requests by URL pattern

        Args:
            pattern: Substring to search in URLs
        """
        monitor = get_network_monitor()
        return monitor.get_by_url_pattern(pattern)

    logger.info("Network monitor tools registered")
