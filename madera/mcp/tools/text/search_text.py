"""
MADERA MCP - search_text
Core Tool - Searches for text patterns in a PDF using regex

Execution time: ~60ms
Technique: Text extraction + regex matching
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import re
import logging

logger = logging.getLogger(__name__)


class TextSearcher(BaseTool):
    """Searches for patterns in PDF text"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    async def _execute(
        self,
        presigned_url: str,
        pattern: str,
        case_sensitive: bool = False
    ) -> ToolResult:
        """
        Search for text pattern in PDF

        Args:
            presigned_url: MinIO presigned URL for PDF
            pattern: Regex pattern to search for
            case_sensitive: Case-sensitive search (default: False)

        Returns:
            ToolResult with match results
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Extract text
        reader = PdfReader(local_pdf)
        total_pages = len(reader.pages)

        # Compile pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult(
                success=False,
                data={"error": f"Invalid regex pattern: {e}"},
                hints={"message": f"Invalid pattern: {e}"},
                confidence=0.0
            )

        # Search each page
        matches = []
        total_matches = 0

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()

            # Find all matches on this page
            page_matches = []
            for match in regex.finditer(text):
                # Get context (50 chars before/after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].replace('\n', ' ')

                page_matches.append({
                    "matched_text": match.group(),
                    "context": context,
                    "position": match.start()
                })

            if page_matches:
                matches.append({
                    "page": page_num,
                    "match_count": len(page_matches),
                    "matches": page_matches
                })
                total_matches += len(page_matches)

        logger.info(
            f"Found {total_matches} matches for '{pattern}' "
            f"across {len(matches)} pages"
        )

        return ToolResult(
            success=True,
            data={
                "pattern": pattern,
                "total_matches": total_matches,
                "pages_with_matches": len(matches),
                "total_pages": total_pages,
                "case_sensitive": case_sensitive,
                "matches": matches
            },
            hints={
                "total_matches": total_matches,
                "pages_with_matches": len(matches),
                "message": f"Found {total_matches} matches on {len(matches)} pages"
            },
            confidence=1.0
        )


# Register tool with MCP server
def register(mcp_server):
    """Register search_text tool"""
    searcher = TextSearcher()

    @mcp_server.tool()
    async def search_text(
        presigned_url: str,
        pattern: str,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Searches for text patterns in a PDF using regex.

        This tool searches the entire PDF for matches and provides context
        around each match. Much faster than asking AI to find text.

        Args:
            presigned_url: MinIO presigned URL for the PDF
            pattern: Regex pattern (e.g., "\\d{3}-\\d{3}-\\d{4}" for phone numbers)
            case_sensitive: Case-sensitive search (default: False)

        Returns:
            {
                "success": true,
                "data": {
                    "pattern": "\\d{3}-\\d{3}-\\d{4}",
                    "total_matches": 5,
                    "pages_with_matches": 3,
                    "total_pages": 15,
                    "case_sensitive": false,
                    "matches": [
                        {
                            "page": 1,
                            "match_count": 2,
                            "matches": [
                                {
                                    "matched_text": "514-555-1234",
                                    "context": "...contact at 514-555-1234 for more...",
                                    "position": 123
                                }
                            ]
                        }
                    ]
                },
                "hints": {
                    "total_matches": 5,
                    "pages_with_matches": 3,
                    "message": "Found 5 matches on 3 pages"
                },
                "confidence": 1.0,
                "execution_time_ms": 58
            }

        Common patterns:
            - Phone: "\\d{3}-\\d{3}-\\d{4}"
            - Email: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
            - Postal code (CA): "[A-Z]\\d[A-Z]\\s?\\d[A-Z]\\d"
            - SIN: "\\d{3}[ -]?\\d{3}[ -]?\\d{3}"
            - Dollar amounts: "\\$\\s?[\\d,]+\\.?\\d*"

        Example usage:
            result = await search_text(
                "https://minio/file.pdf?presigned=...",
                pattern=r"\\d{3}-\\d{3}-\\d{4}"
            )
            for page_match in result["data"]["matches"]:
                print(f"Page {page_match['page']}: {page_match['match_count']} matches")
        """
        result = await searcher.execute(
            presigned_url=presigned_url,
            pattern=pattern,
            case_sensitive=case_sensitive
        )
        return result.model_dump()
