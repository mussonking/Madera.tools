"""
MADERA MCP - HINTS Tools
Pre-analysis tools that run BEFORE AI to provide contextual hints

All 7 Phase 1 MVP tools:
1. detect_blank_pages - Identifies blank pages to skip (50ms)
2. detect_id_card_sides - Detects recto/verso ID cards (50ms)
3. identify_cra_document_type - CRA document classification (200ms)
4. detect_tax_form_type - T4/T1/T5 detection (100ms)
5. detect_document_boundaries - Multi-document split points (150ms)
6. detect_fiscal_year - Fiscal year extraction (80ms)
7. assess_image_quality - Image quality assessment (100ms)

Total parallel execution: 250-300ms
"""

__all__ = [
    "blank_page_detector",
    "id_card_detector",
    "cra_doc_detector",
    "tax_form_detector",
    "document_splitter",
    "fiscal_year_detector",
    "quality_assessor",
]
