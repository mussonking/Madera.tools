"""
MADERA Visual AI - Report Builder
Generates AI-ready test reports and bug hypothesis for debugging
"""
import json
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportBuilder:
    """Build comprehensive test reports for AI analysis"""

    def __init__(self):
        self.output_dir = Path("/tmp/madera-reports")
        self.output_dir.mkdir(exist_ok=True)

    async def build(
        self,
        title: str,
        description: str,
        include_console: bool = True,
        include_network: bool = True,
        include_screenshot: bool = True
    ) -> dict:
        """
        Build a comprehensive test report

        Args:
            title: Report title
            description: Description of the issue or test case
            include_console: Include console logs
            include_network: Include network requests
            include_screenshot: Take and include screenshot
        """
        from madera.mcp.tools.visual.screenshot import get_visual_ai
        from madera.mcp.tools.visual.console_capture import get_console_capture
        from madera.mcp.tools.visual.network_monitor import get_network_monitor

        timestamp = datetime.now()
        report = {
            "title": title,
            "description": description,
            "timestamp": timestamp.isoformat(),
            "url": None,
            "screenshot": None,
            "console": None,
            "network": None,
            "summary": {}
        }

        # Get current page info
        ai = await get_visual_ai()
        if ai.page:
            report["url"] = ai.page.url
            report["viewport"] = ai.page.viewport_size

        # Console logs
        if include_console:
            capture = get_console_capture()
            errors = capture.get_errors(include_warnings=True)
            patterns = capture.detect_patterns()

            report["console"] = {
                "errors": errors.get("errors", [])[:20],  # Limit to 20
                "error_count": errors.get("count", 0),
                "patterns": patterns.get("issues", []),
                "has_critical": patterns.get("has_critical", False)
            }
            report["summary"]["console_errors"] = errors.get("count", 0)

        # Network requests
        if include_network:
            monitor = get_network_monitor()
            failed = monitor.get_failed()
            all_requests = monitor.get_all()

            report["network"] = {
                "failed_requests": failed.get("failed_requests", [])[:20],
                "failed_count": failed.get("count", 0),
                "total_requests": all_requests.get("total", 0),
                "by_status": all_requests.get("by_status", {})
            }
            report["summary"]["failed_requests"] = failed.get("count", 0)

        # Screenshot
        if include_screenshot and ai.page:
            screenshot_result = await ai.screenshot(name=f"report_{timestamp.strftime('%H%M%S')}")
            if screenshot_result.get("success"):
                report["screenshot"] = {
                    "path": screenshot_result.get("path"),
                    "filename": screenshot_result.get("filename")
                }

        # Generate summary
        report["summary"]["has_issues"] = (
            report["summary"].get("console_errors", 0) > 0 or
            report["summary"].get("failed_requests", 0) > 0
        )

        # Save report
        filename = f"report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "success": True,
            "report": report,
            "saved_to": str(filepath)
        }

    def generate_hypothesis(
        self,
        console_errors: list,
        failed_requests: list,
        user_action: str = ""
    ) -> dict:
        """
        Generate bug hypothesis based on collected data

        Args:
            console_errors: List of console errors
            failed_requests: List of failed network requests
            user_action: Description of user action that triggered the issue
        """
        hypotheses = []
        confidence_scores = []

        # Analyze console errors
        js_errors = [e for e in console_errors if e.get("type") in ["error", "pageerror"]]
        if js_errors:
            # Check for common patterns
            for error in js_errors[:5]:
                text = error.get("text", "").lower()

                if "undefined" in text or "null" in text:
                    hypotheses.append({
                        "type": "null_reference",
                        "description": "Possible null/undefined reference error",
                        "evidence": error.get("text", "")[:200],
                        "suggestion": "Check for null checks before accessing properties"
                    })
                    confidence_scores.append(0.8)

                elif "network" in text or "fetch" in text or "cors" in text:
                    hypotheses.append({
                        "type": "network_error",
                        "description": "Network or CORS issue",
                        "evidence": error.get("text", "")[:200],
                        "suggestion": "Check API endpoint availability and CORS configuration"
                    })
                    confidence_scores.append(0.85)

                elif "react" in text or "hook" in text:
                    hypotheses.append({
                        "type": "react_error",
                        "description": "React lifecycle or hooks error",
                        "evidence": error.get("text", "")[:200],
                        "suggestion": "Check component lifecycle and hook dependencies"
                    })
                    confidence_scores.append(0.75)

        # Analyze failed requests
        for req in failed_requests[:5]:
            status = req.get("status", 0)
            url = req.get("url", "")

            if status == 404:
                hypotheses.append({
                    "type": "missing_resource",
                    "description": f"Resource not found (404)",
                    "evidence": f"URL: {url}",
                    "suggestion": "Verify the resource exists and URL is correct"
                })
                confidence_scores.append(0.9)

            elif status >= 500:
                hypotheses.append({
                    "type": "server_error",
                    "description": f"Server error ({status})",
                    "evidence": f"URL: {url}",
                    "suggestion": "Check server logs for error details"
                })
                confidence_scores.append(0.85)

            elif req.get("type") == "network_failure":
                hypotheses.append({
                    "type": "network_failure",
                    "description": "Network connection failed",
                    "evidence": f"URL: {url}, Error: {req.get('error', 'Unknown')}",
                    "suggestion": "Check network connectivity and server availability"
                })
                confidence_scores.append(0.8)

        # No issues found
        if not hypotheses:
            return {
                "success": True,
                "hypotheses": [],
                "summary": "No obvious issues detected based on console and network data",
                "recommendation": "Consider checking application state, user input validation, or UI rendering issues"
            }

        # Sort by confidence
        sorted_hypotheses = sorted(
            zip(hypotheses, confidence_scores),
            key=lambda x: x[1],
            reverse=True
        )

        result_hypotheses = []
        for h, conf in sorted_hypotheses:
            h["confidence"] = conf
            result_hypotheses.append(h)

        # Generate overall summary
        primary = result_hypotheses[0] if result_hypotheses else None
        summary = f"Most likely issue: {primary['description']}" if primary else "No clear hypothesis"

        return {
            "success": True,
            "hypotheses": result_hypotheses,
            "primary_hypothesis": primary,
            "summary": summary,
            "total_evidence": {
                "console_errors": len(console_errors),
                "failed_requests": len(failed_requests)
            }
        }

    async def export_for_ai(
        self,
        title: str,
        description: str,
        format: str = "markdown"
    ) -> dict:
        """
        Export a report formatted for AI analysis (e.g., Claude, ChatGPT)

        Args:
            title: Issue title
            description: Description of the problem
            format: Output format (markdown, json)
        """
        from madera.mcp.tools.visual.console_capture import get_console_capture
        from madera.mcp.tools.visual.network_monitor import get_network_monitor
        from madera.mcp.tools.visual.screenshot import get_visual_ai

        ai = await get_visual_ai()
        capture = get_console_capture()
        monitor = get_network_monitor()

        # Gather data
        errors = capture.get_errors(include_warnings=True)
        failed = monitor.get_failed()

        if format == "markdown":
            report = f"""# Bug Report: {title}

## Description
{description}

## Environment
- **URL**: {ai.page.url if ai.page else "N/A"}
- **Timestamp**: {datetime.now().isoformat()}

## Console Errors ({errors.get('count', 0)} total)
"""
            for err in errors.get("errors", [])[:10]:
                report += f"\n- `{err.get('type', 'error')}`: {err.get('text', '')[:150]}"

            report += f"""

## Failed Network Requests ({failed.get('count', 0)} total)
"""
            for req in failed.get("failed_requests", [])[:10]:
                status = req.get("status", req.get("error", "failed"))
                report += f"\n- `{req.get('method', 'GET')} {req.get('url', '')}` - {status}"

            # Generate hypothesis
            hypothesis = self.generate_hypothesis(
                errors.get("errors", []),
                failed.get("failed_requests", []),
                description
            )

            report += f"""

## AI Analysis Hypothesis
**Primary Issue**: {hypothesis.get('primary_hypothesis', {}).get('description', 'Unknown')}

**Confidence**: {hypothesis.get('primary_hypothesis', {}).get('confidence', 0):.0%}

**Suggestion**: {hypothesis.get('primary_hypothesis', {}).get('suggestion', 'Review the evidence above')}

## All Hypotheses
"""
            for h in hypothesis.get("hypotheses", [])[:5]:
                report += f"\n- **{h.get('type', 'unknown')}** ({h.get('confidence', 0):.0%}): {h.get('description', '')}"

            # Save
            filename = f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = self.output_dir / filename
            with open(filepath, "w") as f:
                f.write(report)

            return {
                "success": True,
                "format": "markdown",
                "content": report,
                "saved_to": str(filepath)
            }

        else:  # JSON format
            report_data = {
                "title": title,
                "description": description,
                "url": ai.page.url if ai.page else None,
                "timestamp": datetime.now().isoformat(),
                "console_errors": errors.get("errors", [])[:20],
                "failed_requests": failed.get("failed_requests", [])[:20],
                "hypothesis": self.generate_hypothesis(
                    errors.get("errors", []),
                    failed.get("failed_requests", []),
                    description
                )
            }

            filename = f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.output_dir / filename
            with open(filepath, "w") as f:
                json.dump(report_data, f, indent=2)

            return {
                "success": True,
                "format": "json",
                "content": report_data,
                "saved_to": str(filepath)
            }


# Singleton instance
_report_builder: Optional[ReportBuilder] = None


def get_report_builder() -> ReportBuilder:
    """Get or create ReportBuilder instance"""
    global _report_builder
    if _report_builder is None:
        _report_builder = ReportBuilder()
    return _report_builder


# MCP Tool Registration
def register(mcp):
    """Register report builder tools with MCP server"""

    @mcp.tool()
    async def visual_report_build(
        title: str,
        description: str,
        include_console: bool = True,
        include_network: bool = True,
        include_screenshot: bool = True
    ) -> dict:
        """
        Build a comprehensive test report

        Combines console logs, network requests, and screenshots into a
        single report for debugging.

        Args:
            title: Report title
            description: Description of the issue
            include_console: Include console error logs
            include_network: Include failed network requests
            include_screenshot: Take and include a screenshot
        """
        builder = get_report_builder()
        return await builder.build(
            title, description,
            include_console, include_network, include_screenshot
        )

    @mcp.tool()
    async def visual_report_hypothesis() -> dict:
        """
        Generate bug hypothesis based on collected data

        Analyzes console errors and failed network requests to suggest
        likely causes of issues.
        """
        from madera.mcp.tools.visual.console_capture import get_console_capture
        from madera.mcp.tools.visual.network_monitor import get_network_monitor

        capture = get_console_capture()
        monitor = get_network_monitor()

        errors = capture.get_errors(include_warnings=True)
        failed = monitor.get_failed()

        builder = get_report_builder()
        return builder.generate_hypothesis(
            errors.get("errors", []),
            failed.get("failed_requests", [])
        )

    @mcp.tool()
    async def visual_report_export(
        title: str,
        description: str,
        format: str = "markdown"
    ) -> dict:
        """
        Export report formatted for AI analysis

        Creates a report optimized for Claude, ChatGPT, or other AI assistants
        to analyze and debug issues.

        Args:
            title: Issue title
            description: Description of the problem
            format: Output format (markdown, json)
        """
        builder = get_report_builder()
        return await builder.export_for_ai(title, description, format)

    logger.info("Report builder tools registered")
