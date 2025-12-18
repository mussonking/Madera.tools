"""
Settings routes - AI model configuration
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# In-memory settings cache (could be moved to DB later)
current_settings = {
    "ai_provider": os.getenv("TRAINING_AI_PROVIDER", "gemini"),
    "model_name": "gemini-2.5-pro",  # Default - best for training
}

# Logo database - Predefined logos for validation dropdown
logo_database = [
    # Canadian Banks
    {"code": "TD_CANADA_TRUST", "display": "TD Canada Trust", "category": "bank"},
    {"code": "RBC_ROYAL_BANK", "display": "RBC Royal Bank", "category": "bank"},
    {"code": "SCOTIABANK", "display": "Scotiabank", "category": "bank"},
    {"code": "BMO", "display": "BMO Bank of Montreal", "category": "bank"},
    {"code": "CIBC", "display": "CIBC", "category": "bank"},
    {"code": "NATIONAL_BANK", "display": "National Bank of Canada", "category": "bank"},
    {"code": "DESJARDINS", "display": "Desjardins", "category": "bank"},
    {"code": "TANGERINE", "display": "Tangerine", "category": "bank"},
    {"code": "SIMPLII", "display": "Simplii Financial", "category": "bank"},

    # Government
    {"code": "CRA", "display": "Canada Revenue Agency", "category": "government"},
    {"code": "REVENU_QUEBEC", "display": "Revenu Québec", "category": "government"},
    {"code": "SERVICE_CANADA", "display": "Service Canada", "category": "government"},

    # Insurance
    {"code": "MANULIFE", "display": "Manulife", "category": "insurance"},
    {"code": "SUNLIFE", "display": "Sun Life", "category": "insurance"},
    {"code": "DESJARDINS_INSURANCE", "display": "Desjardins Insurance", "category": "insurance"},
    {"code": "INTACT", "display": "Intact Insurance", "category": "insurance"},

    # Credit Bureaus
    {"code": "EQUIFAX", "display": "Equifax Canada", "category": "credit"},
    {"code": "TRANSUNION", "display": "TransUnion Canada", "category": "credit"},
]

# Categories database - Custom logo categories (shared across all modes)
categories_database = []

# Document types database - For classification training (shared across all modes)
doctypes_database = [
    {"code": "bank_statement", "label": "Bank Statement", "category": "financial"},
    {"code": "tax_form", "label": "Tax Form (T4, T1, etc.)", "category": "tax"},
    {"code": "paystub", "label": "Pay Stub", "category": "financial"},
    {"code": "insurance_doc", "label": "Insurance Document", "category": "insurance"},
    {"code": "mortgage_document", "label": "Mortgage Document", "category": "financial"},
    {"code": "id_card", "label": "ID Card / Permit", "category": "identity"},
    {"code": "credit_report", "label": "Credit Report", "category": "financial"},
    {"code": "investment_statement", "label": "Investment Statement", "category": "financial"},
    {"code": "other", "label": "Other", "category": "other"},
]

@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page - configure AI models"""

    # Recommended models per provider (OFFICIAL LIST - Dec 2025)
    recommended_models = {
        "gemini": [
            {"name": "gemini-3-pro-preview", "desc": "Latest Pro (experimental)", "default": False},
            {"name": "gemini-2.5-pro", "desc": "Best for training (recommended)", "default": True},
            {"name": "gemini-2.5-flash", "desc": "Fast balanced model"},
            {"name": "gemini-2.5-flash-preview-09-2025", "desc": "Flash preview (Sept 2025)"},
            {"name": "gemini-2.5-flash-lite", "desc": "Ultra fast, no thinking"},
            {"name": "gemini-2.0-flash", "desc": "Previous gen fast"},
            {"name": "gemini-2.0-flash-lite", "desc": "Previous gen lite"},
        ],
        "claude": [
            {"name": "claude-sonnet-4.5-20250929", "desc": "Latest Sonnet (best balance)"},
            {"name": "claude-opus-4-5-20251101", "desc": "Most capable (expensive)"},
            {"name": "claude-3-5-sonnet-20241022", "desc": "Stable Sonnet"},
        ],
        "openai": [
            {"name": "gpt-4o", "desc": "Latest GPT-4 (multimodal)"},
            {"name": "gpt-4-turbo", "desc": "Fast GPT-4"},
            {"name": "gpt-4", "desc": "Stable GPT-4"},
        ],
    }

    return templates.TemplateResponse(
        "settings_tabbed.html",
        {
            "request": request,
            "title": "Settings - AI Training Configuration",
            "current_provider": current_settings["ai_provider"],
            "current_model": current_settings["model_name"],
            "recommended_models": recommended_models,
            "api_keys": {
                "gemini": bool(os.getenv("GOOGLE_API_KEY")),
                "claude": bool(os.getenv("ANTHROPIC_API_KEY")),
                "openai": bool(os.getenv("OPENAI_API_KEY")),
            },
        }
    )


@router.post("/api/update")
async def update_settings(
    provider: str = Form(...),
    model_name: str = Form(...),
):
    """Update AI settings"""

    # Validate provider
    if provider not in ["gemini", "claude", "openai"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid provider"}
        )

    # Check if API key exists
    api_key_map = {
        "gemini": "GOOGLE_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    if not os.getenv(api_key_map[provider]):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": f"API key for {provider} not configured in .env"
            }
        )

    # Update settings
    current_settings["ai_provider"] = provider
    current_settings["model_name"] = model_name.strip()

    # TODO: Save to database (system_settings table)
    # For now, in-memory only

    return JSONResponse(content={
        "success": True,
        "provider": provider,
        "model": model_name,
        "message": "Settings updated! Will be used for next training session."
    })


@router.get("/api/current")
async def get_current_settings():
    """Get current AI settings"""
    return JSONResponse(content=current_settings)


@router.get("/api/logos")
async def get_logos():
    """Get logo database for validation dropdown"""
    return JSONResponse(content={"logos": logo_database})


@router.post("/api/logos/add")
async def add_logo(
    code: str = Form(...),
    display: str = Form(...),
    category: str = Form(...)
):
    """Add new logo to database"""
    # Check if already exists
    if any(logo["code"] == code for logo in logo_database):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Logo code already exists"}
        )

    logo_database.append({
        "code": code.upper().replace(" ", "_"),
        "display": display,
        "category": category
    })

    # TODO: Save to database
    return JSONResponse(content={"success": True, "logos": logo_database})


@router.delete("/api/logos/{code}")
async def delete_logo(code: str):
    """Delete logo from database"""
    global logo_database
    logo_database = [logo for logo in logo_database if logo["code"] != code]

    # TODO: Save to database
    return JSONResponse(content={"success": True, "logos": logo_database})


@router.get("/api/categories")
async def get_categories():
    """Get categories database for custom logo categories"""
    return JSONResponse(content={"categories": categories_database})


@router.post("/api/categories/add")
async def add_category(
    code: str = Form(...),
    label: str = Form(...),
    icon: str = Form(...)
):
    """Add new category to database"""
    # Check if already exists
    if any(cat["code"] == code for cat in categories_database):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Category code already exists"}
        )

    categories_database.append({
        "code": code.lower().replace(" ", "_"),
        "label": label,
        "icon": icon
    })

    # TODO: Save to database
    return JSONResponse(content={"success": True, "categories": categories_database})


@router.delete("/api/categories/{code}")
async def delete_category(code: str):
    """Delete category from database"""
    global categories_database
    categories_database = [cat for cat in categories_database if cat["code"] != code]

    # TODO: Save to database
    return JSONResponse(content={"success": True, "categories": categories_database})


@router.get("/api/doctypes")
async def get_doctypes():
    """Get document types database for classification training"""
    return JSONResponse(content={"doctypes": doctypes_database})


@router.post("/api/doctypes/add")
async def add_doctype(
    code: str = Form(...),
    label: str = Form(...),
    category: str = Form(...)
):
    """Add new document type to database"""
    # Check if already exists
    if any(dt["code"] == code for dt in doctypes_database):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Document type code already exists"}
        )

    doctypes_database.append({
        "code": code.lower().replace(" ", "_"),
        "label": label,
        "category": category
    })

    # TODO: Save to database
    return JSONResponse(content={"success": True, "doctypes": doctypes_database})


@router.delete("/api/doctypes/{code}")
async def delete_doctype(code: str):
    """Delete document type from database"""
    global doctypes_database
    doctypes_database = [dt for dt in doctypes_database if dt["code"] != code]

    # TODO: Save to database
    return JSONResponse(content={"success": True, "doctypes": doctypes_database})
