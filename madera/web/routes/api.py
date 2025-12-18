"""
MADERA MCP - API Routes
RESTful API endpoints for external integration
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import logging

from madera.mcp.server import mcp_server
from madera.database import get_db, get_db_session, ToolExecution, ToolTemplate
from madera.mcp.categories import (
    MAIN_CATEGORIES,
    SUBCATEGORIES,
    TOOL_SUBCATEGORY,
    TOOL_SHORT_DESCRIPTIONS,
    get_tool_category,
    get_tools_by_subcategory,
    get_tools_by_category,
    get_all_categories_with_tools,
    get_category_stats,
)
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# CATEGORY ENDPOINTS
# ============================================

@router.get("/categories")
async def list_categories():
    """
    List all categories with subcategories

    Returns:
        {
            "categories": [
                {
                    "id": "pdf",
                    "name": "PDF Processing",
                    "icon": "📂",
                    "color": "#00a67e",
                    "description": "...",
                    "subcategories": [
                        {"id": "analysis", "name": "Analysis", "icon": "🎯", ...},
                        {"id": "transform", "name": "Transform", "icon": "📄", ...}
                    ]
                }
            ],
            "stats": {"total_tools": 40, ...}
        }
    """
    categories = []
    for cat_id, cat_info in MAIN_CATEGORIES.items():
        subcats = [
            {**SUBCATEGORIES[subcat_id]}
            for subcat_id in cat_info["subcategories"]
        ]
        categories.append({
            "id": cat_id,
            "name": cat_info["name"],
            "icon": cat_info["icon"],
            "color": cat_info["color"],
            "description": cat_info["description"],
            "subcategories": subcats
        })

    stats = get_category_stats()

    return JSONResponse({
        "categories": categories,
        "stats": stats
    })


@router.get("/categories/{category_id}")
async def get_category(category_id: str):
    """
    Get category details with tools grouped by subcategory

    Args:
        category_id: Category ID (pdf, debug)

    Returns:
        {
            "id": "pdf",
            "name": "PDF Processing",
            "subcategories": {
                "analysis": {
                    "name": "Analysis",
                    "icon": "🎯",
                    "tools": [
                        {"name": "detect_blank_pages", "short_description": "..."},
                        ...
                    ]
                }
            }
        }
    """
    if category_id not in MAIN_CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found")

    cat_info = MAIN_CATEGORIES[category_id]
    tools_by_subcat = get_tools_by_category(category_id)

    subcategories = {}
    for subcat_id in cat_info["subcategories"]:
        subcat_info = SUBCATEGORIES[subcat_id]
        tools = tools_by_subcat.get(subcat_id, [])
        subcategories[subcat_id] = {
            **subcat_info,
            "tools": [
                {
                    "name": tool,
                    "short_description": TOOL_SHORT_DESCRIPTIONS.get(tool, "")
                }
                for tool in tools
            ],
            "tool_count": len(tools)
        }

    return JSONResponse({
        "id": category_id,
        **cat_info,
        "subcategories": subcategories,
        "total_tools": sum(len(t) for t in tools_by_subcat.values())
    })


@router.get("/tools")
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by main category (pdf, debug)"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory (analysis, transform, visual, monitoring)")
):
    """
    List all registered MCP tools with category info

    Args:
        category: Filter by main category (pdf, debug)
        subcategory: Filter by subcategory (analysis, transform, visual, monitoring)

    Returns:
        {
            "tools": [
                {
                    "name": "detect_blank_pages",
                    "short_description": "Detect blank/empty pages in PDF",
                    "description": "...",
                    "category": "pdf",
                    "subcategory": "analysis",
                    "category_info": {...}
                }
            ],
            "total": 40
        }
    """
    tools = await mcp_server.list_tools()

    tools_list = []
    for tool in tools:
        tool_cat = get_tool_category(tool.name)

        # Apply filters
        if category and (not tool_cat or tool_cat["category"]["id"] != category):
            continue
        if subcategory and (not tool_cat or tool_cat["subcategory"]["id"] != subcategory):
            continue

        tools_list.append({
            "name": tool.name,
            "short_description": TOOL_SHORT_DESCRIPTIONS.get(tool.name, ""),
            "description": tool.description,
            "category": tool_cat["category"]["id"] if tool_cat else "unknown",
            "subcategory": tool_cat["subcategory"]["id"] if tool_cat else "unknown",
            "category_info": {
                "category_name": tool_cat["category"]["name"] if tool_cat else "Unknown",
                "category_icon": tool_cat["category"]["icon"] if tool_cat else "❓",
                "subcategory_name": tool_cat["subcategory"]["name"] if tool_cat else "Unknown",
                "subcategory_icon": tool_cat["subcategory"]["icon"] if tool_cat else "❓",
                "color": tool_cat["subcategory"]["color"] if tool_cat else "#666",
            } if tool_cat else None
        })

    return JSONResponse({
        "tools": tools_list,
        "total": len(tools_list),
    })


@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """
    Get detailed info about a specific tool

    Args:
        tool_name: Tool name (e.g., "detect_blank_pages")

    Returns:
        {
            "name": "detect_blank_pages",
            "short_description": "Detect blank/empty pages in PDF",
            "description": "...",
            "input_schema": {...},
            "category_info": {...},
            "stats": {...}
        }
    """
    tools_list = await mcp_server.list_tools()
    tools = {tool.name: tool for tool in tools_list}

    tool_cat = get_tool_category(tool_name)

    # Tool not loaded in MCP server, but exists in category registry
    if tool_name not in tools:
        # Return basic info from categories if available
        if tool_cat:
            return JSONResponse({
                "name": tool_name,
                "short_description": TOOL_SHORT_DESCRIPTIONS.get(tool_name, ""),
                "description": f"Tool registered but not loaded (missing dependencies). {TOOL_SHORT_DESCRIPTIONS.get(tool_name, '')}",
                "input_schema": {},
                "category": tool_cat["category"]["id"],
                "subcategory": tool_cat["subcategory"]["id"],
                "category_info": {
                    "category_name": tool_cat["category"]["name"],
                    "category_icon": tool_cat["category"]["icon"],
                    "subcategory_name": tool_cat["subcategory"]["name"],
                    "subcategory_icon": tool_cat["subcategory"]["icon"],
                    "color": tool_cat["subcategory"]["color"],
                },
                "stats": {
                    "total_executions": 0,
                    "success_rate": 0,
                    "avg_confidence": 0,
                    "avg_execution_time_ms": 0,
                },
                "warning": "Tool not loaded on web server (available via MCP stdio only)"
            })
        else:
            raise HTTPException(status_code=404, detail="Tool not found")

    tool = tools[tool_name]

    # Get tool statistics
    total_executions = 0
    successful = 0
    avg_confidence = 0.0
    avg_time = 0.0

    try:
        async for db in get_db_session():
            stats_query = await db.execute(
                select(ToolExecution)
                .where(ToolExecution.tool_name == tool_name)
                .order_by(ToolExecution.created_at.desc())
                .limit(100)
            )
            executions = stats_query.scalars().all()

            total_executions = len(executions)
            successful = sum(1 for e in executions if e.success)
            avg_confidence = sum(e.confidence for e in executions if e.confidence) / total_executions if total_executions > 0 else 0
            avg_time = sum(e.execution_time_ms for e in executions if e.execution_time_ms) / total_executions if total_executions > 0 else 0
            break  # Exit after first iteration
    except Exception as e:
        logger.warning(f"Failed to fetch tool stats for {tool_name}: {e}")

    category_info = None
    if tool_cat:
        category_info = {
            "category_name": tool_cat["category"]["name"],
            "category_icon": tool_cat["category"]["icon"],
            "subcategory_name": tool_cat["subcategory"]["name"],
            "subcategory_icon": tool_cat["subcategory"]["icon"],
            "color": tool_cat["subcategory"]["color"],
        }

    return JSONResponse({
        "name": tool.name,
        "short_description": TOOL_SHORT_DESCRIPTIONS.get(tool_name, ""),
        "description": tool.description,
        "input_schema": tool.inputSchema,  # MCP Tool uses camelCase
        "category": tool_cat["category"]["id"] if tool_cat else "unknown",
        "subcategory": tool_cat["subcategory"]["id"] if tool_cat else "unknown",
        "category_info": category_info,
        "stats": {
            "total_executions": total_executions,
            "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
            "avg_confidence": round(avg_confidence, 2),
            "avg_execution_time_ms": round(avg_time, 1),
        }
    })


@router.get("/templates")
async def list_templates(
    tool_name: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = 50
):
    """
    List trained templates

    Args:
        tool_name: Filter by tool
        document_type: Filter by document type
        limit: Max results

    Returns:
        {
            "templates": [...],
            "total": 10
        }
    """
    async with get_db_session() as db:
        query = select(ToolTemplate).where(ToolTemplate.is_active == True)

        if tool_name:
            query = query.where(ToolTemplate.tool_name == tool_name)

        if document_type:
            query = query.where(ToolTemplate.document_type == document_type)

        query = query.order_by(ToolTemplate.created_at.desc()).limit(limit)

        result = await db.execute(query)
        templates = result.scalars().all()

    return JSONResponse({
        "templates": [
            {
                "id": t.id,
                "tool_name": t.tool_name,
                "document_type": t.document_type,
                "logo_name": t.logo_name,
                "precision_rate": t.precision_rate,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ],
        "total": len(templates),
    })


@router.get("/templates/{template_id}")
async def get_template(template_id: int):
    """
    Get specific template details

    Args:
        template_id: Template ID

    Returns:
        {
            "id": 1,
            "tool_name": "logo_detector",
            "zones": {...},
            ...
        }
    """
    async with get_db_session() as db:
        result = await db.execute(
            select(ToolTemplate).where(ToolTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

    return JSONResponse({
        "id": template.id,
        "tool_name": template.tool_name,
        "document_type": template.document_type,
        "logo_name": template.logo_name,
        "zones": template.zones,
        "thresholds": template.thresholds,
        "precision_rate": template.precision_rate,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    })


@router.get("/stats")
async def get_stats():
    """
    Get global statistics

    Returns:
        {
            "total_tools": 7,
            "total_executions": 1234,
            "total_templates": 45,
            ...
        }
    """
    from sqlalchemy import func

    async with get_db_session() as db:
        # Total executions
        total_exec_query = await db.execute(select(func.count(ToolExecution.id)))
        total_executions = total_exec_query.scalar() or 0

        # Success rate
        success_query = await db.execute(
            select(func.count(ToolExecution.id)).where(ToolExecution.success == True)
        )
        successful = success_query.scalar() or 0

        # Total templates
        total_templates_query = await db.execute(
            select(func.count(ToolTemplate.id)).where(ToolTemplate.is_active == True)
        )
        total_templates = total_templates_query.scalar() or 0

        # Average confidence
        avg_conf_query = await db.execute(
            select(func.avg(ToolExecution.confidence)).where(ToolExecution.success == True)
        )
        avg_confidence = avg_conf_query.scalar() or 0.0

    tools_list = await mcp_server.list_tools()

    return JSONResponse({
        "total_tools": len(tools_list),
        "total_executions": total_executions,
        "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
        "total_templates": total_templates,
        "avg_confidence": round(avg_confidence, 2),
    })
