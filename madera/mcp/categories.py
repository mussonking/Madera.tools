"""
MADERA MCP - Tool Categories System
Hierarchical categories for MCP tools with 2 main categories and 4 subcategories
"""

# Main Categories (2)
MAIN_CATEGORIES = {
    "pdf": {
        "id": "pdf",
        "name": "PDF Processing",
        "icon": "📂",
        "color": "#00a67e",
        "description": "Document analysis, manipulation, and data extraction tools",
        "subcategories": ["analysis", "transform"]
    },
    "debug": {
        "id": "debug",
        "name": "Debug & Testing",
        "icon": "🔧",
        "color": "#667eea",
        "description": "Visual testing, browser automation, and monitoring tools",
        "subcategories": ["visual", "monitoring"]
    }
}

# Subcategories (4)
SUBCATEGORIES = {
    # PDF Processing subcategories
    "analysis": {
        "id": "analysis",
        "name": "Analysis",
        "icon": "🎯",
        "color": "#10b981",
        "parent": "pdf",
        "description": "Document detection, classification, and quality assessment"
    },
    "transform": {
        "id": "transform",
        "name": "Transform",
        "icon": "📄",
        "color": "#3b82f6",
        "parent": "pdf",
        "description": "PDF manipulation, text extraction, normalization, and calculations"
    },

    # Debug & Testing subcategories
    "visual": {
        "id": "visual",
        "name": "Visual",
        "icon": "👁️",
        "color": "#8b5cf6",
        "parent": "debug",
        "description": "Screenshots, browser interactions, and UI testing"
    },
    "monitoring": {
        "id": "monitoring",
        "name": "Monitoring",
        "icon": "📊",
        "color": "#f59e0b",
        "parent": "debug",
        "description": "Console logs, network requests, and test reports"
    }
}

# Tool to Subcategory Mapping
# Each tool maps to exactly one subcategory
TOOL_SUBCATEGORY = {
    # ============================================
    # ANALYSIS - Detection & Classification (7+)
    # ============================================
    "detect_blank_pages": "analysis",
    "detect_id_card_sides": "analysis",
    "identify_cra_document_type": "analysis",
    "detect_tax_form_type": "analysis",
    "detect_document_boundaries": "analysis",
    "detect_fiscal_year": "analysis",
    "assess_image_quality": "analysis",
    "detect_bank_statement_type": "analysis",
    "detect_form_fields": "analysis",

    # ============================================
    # TRANSFORM - Manipulation & Extraction (25+)
    # ============================================
    # PDF Manipulation
    "count_pages": "transform",
    "extract_page": "transform",
    "split_pdf": "transform",
    "merge_pdfs": "transform",
    "rotate_page": "transform",
    "compress_pdf": "transform",
    "pdf_to_images": "transform",
    "images_to_pdf": "transform",
    "generate_thumbnail": "transform",

    # Text Extraction
    "extract_text": "transform",
    "extract_text_by_page": "transform",
    "search_text": "transform",
    "extract_tables": "transform",
    "extract_urls": "transform",
    "count_signatures": "transform",

    # Normalization
    "normalize_address": "transform",
    "parse_currency": "transform",
    "parse_date": "transform",
    "normalize_name": "transform",
    "split_full_name": "transform",
    "calculate_address_similarity": "transform",

    # Validation
    "validate_sin": "transform",
    "validate_postal_code": "transform",
    "validate_phone": "transform",
    "validate_email": "transform",
    "validate_date_range": "transform",

    # Financial Calculations
    "calculate_annual_income": "transform",
    "calculate_gds_tds": "transform",
    "calculate_ltv": "transform",
    "average_t4_income": "transform",
    "estimate_monthly_payment": "transform",

    # ============================================
    # VISUAL - Screenshots & Interactions (10+)
    # ============================================
    "visual_navigate": "visual",
    "visual_screenshot": "visual",
    "visual_click": "visual",
    "visual_fill": "visual",
    "visual_select": "visual",
    "visual_check_elements": "visual",
    "visual_get_element": "visual",
    "visual_evaluate": "visual",
    "visual_stop": "visual",
    # New helpers
    "visual_is_visible": "visual",
    "visual_wait_for": "visual",
    "visual_wait_animations": "visual",
    "visual_wait_full_load": "visual",
    "visual_scroll_to": "visual",
    "visual_hover": "visual",

    # ============================================
    # MONITORING - Console, Network, Reports (10+)
    # ============================================
    # Console capture
    "visual_console_start": "monitoring",
    "visual_console_get_errors": "monitoring",
    "visual_console_get_all": "monitoring",
    "visual_console_detect_patterns": "monitoring",
    "visual_console_clear": "monitoring",

    # Network monitoring
    "visual_network_start": "monitoring",
    "visual_network_get_failed": "monitoring",
    "visual_network_get_all": "monitoring",
    "visual_network_export_har": "monitoring",
    "visual_network_clear": "monitoring",

    # Report building
    "visual_report_build": "monitoring",
    "visual_report_hypothesis": "monitoring",
    "visual_report_export": "monitoring",
}

# Short descriptions for each tool (used in compact cards)
TOOL_SHORT_DESCRIPTIONS = {
    # Analysis
    "detect_blank_pages": "Detect blank/empty pages in PDF",
    "detect_id_card_sides": "Identify front/back of ID cards",
    "identify_cra_document_type": "Classify CRA tax documents",
    "detect_tax_form_type": "Identify tax form types (T4, T1, etc.)",
    "detect_document_boundaries": "Find document boundaries in multi-doc PDF",
    "detect_fiscal_year": "Extract fiscal year from documents",
    "assess_image_quality": "Assess scan quality and readability",
    "detect_bank_statement_type": "Identify bank statement format",
    "detect_form_fields": "Detect fillable form fields",

    # Transform - PDF
    "count_pages": "Count pages in PDF",
    "extract_page": "Extract specific pages from PDF",
    "split_pdf": "Split PDF into separate documents",
    "merge_pdfs": "Merge multiple PDFs into one",
    "rotate_page": "Rotate pages in PDF",
    "compress_pdf": "Reduce PDF file size",
    "pdf_to_images": "Convert PDF pages to images",
    "images_to_pdf": "Create PDF from images",
    "generate_thumbnail": "Generate thumbnail preview",

    # Transform - Text
    "extract_text": "Extract all text from PDF",
    "extract_text_by_page": "Extract text page by page",
    "search_text": "Search for text patterns",
    "extract_tables": "Extract tabular data",
    "extract_urls": "Find URLs in document",
    "count_signatures": "Count signature fields",

    # Transform - Normalization
    "normalize_address": "Standardize address format",
    "parse_currency": "Parse currency values",
    "parse_date": "Parse and normalize dates",
    "normalize_name": "Standardize name format",
    "split_full_name": "Split into first/last name",
    "calculate_address_similarity": "Compare address similarity",

    # Transform - Validation
    "validate_sin": "Validate Canadian SIN",
    "validate_postal_code": "Validate postal/zip code",
    "validate_phone": "Validate phone number",
    "validate_email": "Validate email address",
    "validate_date_range": "Validate date range logic",

    # Transform - Financial
    "calculate_annual_income": "Calculate annual income",
    "calculate_gds_tds": "Calculate GDS/TDS ratios",
    "calculate_ltv": "Calculate loan-to-value ratio",
    "average_t4_income": "Average T4 income over years",
    "estimate_monthly_payment": "Estimate mortgage payment",

    # Visual
    "visual_navigate": "Navigate to URL",
    "visual_screenshot": "Take screenshot",
    "visual_click": "Click element",
    "visual_fill": "Fill input field",
    "visual_select": "Select dropdown option",
    "visual_check_elements": "Check elements exist",
    "visual_get_element": "Get element info",
    "visual_evaluate": "Execute JavaScript",
    "visual_stop": "Stop browser session",
    "visual_is_visible": "Check element visibility",
    "visual_wait_for": "Wait for selector",
    "visual_wait_animations": "Wait for animations",
    "visual_wait_full_load": "Wait for full page load",
    "visual_scroll_to": "Scroll to element",
    "visual_hover": "Hover over element",

    # Monitoring
    "visual_console_start": "Start console capture",
    "visual_console_get_errors": "Get console errors",
    "visual_console_get_all": "Get all console logs",
    "visual_console_detect_patterns": "Detect error patterns",
    "visual_console_clear": "Clear captured logs",
    "visual_network_start": "Start network monitor",
    "visual_network_get_failed": "Get failed requests",
    "visual_network_get_all": "Get all network requests",
    "visual_network_export_har": "Export HAR file",
    "visual_network_clear": "Clear network logs",
    "visual_report_build": "Build test report",
    "visual_report_hypothesis": "Generate bug hypothesis",
    "visual_report_export": "Export report to file",
}


# Utility functions
def get_tool_category(tool_name: str) -> dict | None:
    """Get full category info for a tool"""
    subcat_id = TOOL_SUBCATEGORY.get(tool_name)
    if not subcat_id:
        return None

    subcat = SUBCATEGORIES.get(subcat_id)
    if not subcat:
        return None

    main_cat = MAIN_CATEGORIES.get(subcat["parent"])
    if not main_cat:
        return None

    return {
        "tool": tool_name,
        "subcategory": subcat,
        "category": main_cat,
        "short_description": TOOL_SHORT_DESCRIPTIONS.get(tool_name, "")
    }


def get_tools_by_subcategory(subcat_id: str) -> list[str]:
    """Get all tools in a subcategory"""
    return [
        tool for tool, subcat in TOOL_SUBCATEGORY.items()
        if subcat == subcat_id
    ]


def get_tools_by_category(cat_id: str) -> dict[str, list[str]]:
    """Get all tools in a category, grouped by subcategory"""
    category = MAIN_CATEGORIES.get(cat_id)
    if not category:
        return {}

    result = {}
    for subcat_id in category["subcategories"]:
        result[subcat_id] = get_tools_by_subcategory(subcat_id)
    return result


def get_all_categories_with_tools() -> dict:
    """Get complete category tree with tools"""
    result = {}
    for cat_id, cat_info in MAIN_CATEGORIES.items():
        result[cat_id] = {
            **cat_info,
            "tools_by_subcategory": {}
        }
        for subcat_id in cat_info["subcategories"]:
            subcat_info = SUBCATEGORIES[subcat_id]
            tools = get_tools_by_subcategory(subcat_id)
            result[cat_id]["tools_by_subcategory"][subcat_id] = {
                **subcat_info,
                "tools": [
                    {
                        "name": tool,
                        "short_description": TOOL_SHORT_DESCRIPTIONS.get(tool, "")
                    }
                    for tool in tools
                ]
            }
    return result


def get_category_stats() -> dict:
    """Get statistics about categories"""
    stats = {
        "total_tools": len(TOOL_SUBCATEGORY),
        "categories": {}
    }

    for cat_id, cat_info in MAIN_CATEGORIES.items():
        cat_tools = get_tools_by_category(cat_id)
        total = sum(len(tools) for tools in cat_tools.values())
        stats["categories"][cat_id] = {
            "name": cat_info["name"],
            "total_tools": total,
            "subcategories": {
                subcat_id: len(tools)
                for subcat_id, tools in cat_tools.items()
            }
        }

    return stats
