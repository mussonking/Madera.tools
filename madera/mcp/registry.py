"""
MADERA MCP - Tool Registry
Auto-discovers and registers all tools with MCP server
"""
import logging

logger = logging.getLogger(__name__)


def register_all_tools(mcp_server):
    """
    Register all tools with MCP server

    Phase 1 MVP: 7 HINTS tools ✅
    Phase 2 Core: 15 tools (PDF + Text + Normalization) ✅
    Phase 3 Advanced: 18 tools (Financial + Validation + Advanced) ✅
    Phase 4 Visual: 34+ tools (Browser automation, debugging, reporting) ✅
    """
    logger.info("Registering MADERA MCP tools...")

    # Phase 1: HINTS TOOLS (7 tools)
    hints_tools = [
        ("blank_page_detector", "detect_blank_pages"),
        ("id_card_detector", "detect_id_card_sides"),
        ("cra_doc_detector", "identify_cra_document_type"),
        ("tax_form_detector", "detect_tax_form_type"),
        ("document_splitter", "detect_document_boundaries"),
        ("fiscal_year_detector", "detect_fiscal_year"),
        ("quality_assessor", "assess_image_quality"),
    ]

    # Phase 2: PDF MANIPULATION (5 tools)
    pdf_tools = [
        ("count_pages", "count_pages"),
        ("extract_page", "extract_page"),
        ("split_pdf", "split_pdf"),
        ("merge_pdfs", "merge_pdfs"),
        ("rotate_page", "rotate_page"),
    ]

    # Phase 2: TEXT EXTRACTION (4 tools)
    text_tools = [
        ("extract_text", "extract_text"),
        ("extract_text_by_page", "extract_text_by_page"),
        ("search_text", "search_text"),
        ("extract_tables", "extract_tables"),
    ]

    # Phase 2: DATA NORMALIZATION (6 tools)
    norm_tools = [
        ("normalize_address", "normalize_address"),
        ("parse_currency", "parse_currency"),
        ("parse_date", "parse_date"),
        ("normalize_name", "normalize_name"),
        ("split_full_name", "split_full_name"),
        ("calculate_address_similarity", "calculate_address_similarity"),
    ]

    # Phase 3: FINANCIAL CALCULATIONS (5 tools)
    financial_tools = [
        ("calculate_annual_income", "calculate_annual_income"),
        ("calculate_gds_tds", "calculate_gds_tds"),
        ("calculate_ltv", "calculate_ltv"),
        ("average_t4_income", "average_t4_income"),
        ("estimate_monthly_payment", "estimate_monthly_payment"),
    ]

    # Phase 3: DATA VALIDATION (5 tools)
    validation_tools = [
        ("validate_sin", "validate_sin"),
        ("validate_postal_code", "validate_postal_code"),
        ("validate_phone", "validate_phone"),
        ("validate_email", "validate_email"),
        ("validate_date_range", "validate_date_range"),
    ]

    # Phase 3: ADVANCED TOOLS (8 tools)
    advanced_tools = [
        ("generate_thumbnail", "generate_thumbnail"),
        ("detect_bank_statement_type", "detect_bank_statement_type"),
        ("detect_form_fields", "detect_form_fields"),
        ("count_signatures", "count_signatures"),
        ("extract_urls", "extract_urls"),
        ("compress_pdf", "compress_pdf"),
        ("pdf_to_images", "pdf_to_images"),
        ("images_to_pdf", "images_to_pdf"),
    ]

    # Phase 4: VISUAL AI TOOLS (34+ tools)
    # Core visual tools (screenshot.py)
    visual_tools = [
        ("screenshot", "visual_ai"),
        # Console capture tools
        ("console_capture", "console_capture"),
        # Network monitor tools
        ("network_monitor", "network_monitor"),
        # Visual helpers
        ("visual_helpers", "visual_helpers"),
        # Report builder
        ("report_builder", "report_builder"),
    ]

    # Register all tools
    all_tools = [
        ("hints", hints_tools),
        ("pdf", pdf_tools),
        ("text", text_tools),
        ("normalization", norm_tools),
        ("financial", financial_tools),
        ("validation", validation_tools),
        ("advanced", advanced_tools),
        ("visual", visual_tools),
    ]

    registered_count = 0
    total_count = sum(len(tools) for _, tools in all_tools)

    for category, tools in all_tools:
        for module_name, tool_name in tools:
            try:
                module = __import__(
                    f"madera.mcp.tools.{category}.{module_name}",
                    fromlist=["register"]
                )
                module.register(mcp_server)
                logger.info(f"✅ Registered: {tool_name}")
                registered_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to register {tool_name}: {e}")

    logger.info(f"Tool registration complete: {registered_count}/{total_count} tools registered")
