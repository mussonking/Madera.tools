"""
MADERA MCP - extract_tables
Core Tool - Extracts tables from a PDF (basic implementation)

Execution time: ~100ms
Technique: Text extraction + pattern analysis
"""
from typing import Dict, Any, List
from madera.mcp.tools.base import BaseTool, ToolResult
from pypdf import PdfReader
import re
import logging

logger = logging.getLogger(__name__)


class TableExtractor(BaseTool):
    """Extracts tables from PDF using text patterns"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _detect_table_lines(self, text: str) -> List[str]:
        """
        Detect lines that look like table rows

        Returns:
            List of potential table lines
        """
        lines = text.split('\n')
        table_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Heuristics for table rows:
            # 1. Multiple spaces/tabs between words (column separation)
            # 2. Contains multiple numbers
            # 3. Consistent spacing pattern

            # Check for multiple consecutive spaces (common in tables)
            if re.search(r'\s{2,}', line):
                table_lines.append(line)
            # Check for tab-separated values
            elif '\t' in line:
                table_lines.append(line)
            # Check for lines with multiple numbers
            elif len(re.findall(r'\d+', line)) >= 2:
                # Also has some structure (spaces or special chars)
                if re.search(r'\s{2,}|[\|,;]', line):
                    table_lines.append(line)

        return table_lines

    def _group_into_tables(self, table_lines: List[str]) -> List[List[str]]:
        """
        Group consecutive table lines into tables

        Returns:
            List of tables (each table is a list of lines)
        """
        if not table_lines:
            return []

        tables = []
        current_table = [table_lines[0]]

        for line in table_lines[1:]:
            # Check if this line continues the table
            # (similar structure to previous line)
            if current_table:
                prev_line = current_table[-1]

                # Simple heuristic: similar number of columns
                prev_cols = len(re.split(r'\s{2,}|\t', prev_line))
                curr_cols = len(re.split(r'\s{2,}|\t', line))

                if abs(prev_cols - curr_cols) <= 1:
                    # Likely same table
                    current_table.append(line)
                else:
                    # New table
                    if len(current_table) >= 2:  # Min 2 rows for a table
                        tables.append(current_table)
                    current_table = [line]
            else:
                current_table = [line]

        # Add last table
        if len(current_table) >= 2:
            tables.append(current_table)

        return tables

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Extract tables from PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with extracted tables
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Extract text
        reader = PdfReader(local_pdf)
        total_pages = len(reader.pages)

        all_tables = []

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()

            # Detect table lines
            table_lines = self._detect_table_lines(text)

            if table_lines:
                # Group into tables
                page_tables = self._group_into_tables(table_lines)

                for table_idx, table_lines in enumerate(page_tables, 1):
                    all_tables.append({
                        "page": page_num,
                        "table_number": table_idx,
                        "row_count": len(table_lines),
                        "rows": table_lines
                    })

        logger.info(
            f"Extracted {len(all_tables)} tables from {total_pages} pages"
        )

        return ToolResult(
            success=True,
            data={
                "total_tables": len(all_tables),
                "total_pages": total_pages,
                "tables": all_tables
            },
            hints={
                "total_tables": len(all_tables),
                "message": f"Found {len(all_tables)} tables"
            },
            confidence=0.85  # Basic detection, not perfect
        )


# Register tool with MCP server
def register(mcp_server):
    """Register extract_tables tool"""
    extractor = TableExtractor()

    @mcp_server.tool()
    async def extract_tables(presigned_url: str) -> Dict[str, Any]:
        """
        Extracts tables from a PDF using text pattern analysis.

        This tool detects table-like structures in PDF text using heuristics
        like multiple spaces, tab separators, and consistent column patterns.

        Note: This is a basic implementation. For complex tables, consider
        using specialized tools like Camelot or Tabula.

        Args:
            presigned_url: MinIO presigned URL for the PDF

        Returns:
            {
                "success": true,
                "data": {
                    "total_tables": 3,
                    "total_pages": 15,
                    "tables": [
                        {
                            "page": 5,
                            "table_number": 1,
                            "row_count": 10,
                            "rows": [
                                "Name        Age    City",
                                "John Doe    35     Montreal",
                                "Jane Smith  28     Toronto"
                            ]
                        }
                    ]
                },
                "hints": {
                    "total_tables": 3,
                    "message": "Found 3 tables"
                },
                "confidence": 0.85,
                "execution_time_ms": 95
            }

        Example usage:
            result = await extract_tables("https://minio/file.pdf?presigned=...")
            for table in result["data"]["tables"]:
                print(f"Page {table['page']}, Table {table['table_number']}:")
                for row in table["rows"]:
                    print(f"  {row}")
        """
        result = await extractor.execute(presigned_url=presigned_url)
        return result.model_dump()
