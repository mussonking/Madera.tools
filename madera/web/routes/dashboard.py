"""
MADERA MCP - Dashboard Routes
Main dashboard and statistics
"""
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from madera.database import get_db, ToolExecution, ToolTemplate, TrainingQueue

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Main dashboard page"""
    # Get statistics from database
    stats = await get_dashboard_stats(db)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Dashboard",
            "stats": stats,
        }
    )


@router.get("/tools", response_class=HTMLResponse)
async def tools_list(request: Request):
    """
    List all MCP tools - Tools page with hierarchical categories

    Data is loaded dynamically via JavaScript from /api/tools and /api/categories
    """
    return templates.TemplateResponse(
        "tools.html",
        {
            "request": request,
            "title": "MCP Tools",
        }
    )


@router.get("/templates", response_class=HTMLResponse)
async def templates_list(request: Request, db: AsyncSession = Depends(get_db)):
    """List all trained templates"""
    # Query templates
    result = await db.execute(
        select(ToolTemplate)
        .where(ToolTemplate.is_active == True)
        .order_by(ToolTemplate.created_at.desc())
        .limit(50)
    )

    templates_data = result.scalars().all()

    return templates.TemplateResponse(
        "templates.html",
        {
            "request": request,
            "title": "Trained Templates",
            "templates": templates_data,
        }
    )


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """Get dashboard statistics"""
    # Total tool executions
    total_executions_query = await db.execute(
        select(func.count(ToolExecution.id))
    )
    total_executions = total_executions_query.scalar() or 0

    # Success rate
    success_query = await db.execute(
        select(func.count(ToolExecution.id))
        .where(ToolExecution.success == True)
    )
    successful_executions = success_query.scalar() or 0
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

    # Average confidence
    avg_confidence_query = await db.execute(
        select(func.avg(ToolExecution.confidence))
        .where(ToolExecution.success == True)
    )
    avg_confidence = avg_confidence_query.scalar() or 0.0

    # Average execution time
    avg_time_query = await db.execute(
        select(func.avg(ToolExecution.execution_time_ms))
        .where(ToolExecution.success == True)
    )
    avg_execution_time = avg_time_query.scalar() or 0

    # Total templates
    total_templates_query = await db.execute(
        select(func.count(ToolTemplate.id))
        .where(ToolTemplate.is_active == True)
    )
    total_templates = total_templates_query.scalar() or 0

    # Pending training queue
    pending_queue_query = await db.execute(
        select(func.count(TrainingQueue.id))
        .where(TrainingQueue.processed == False)
    )
    pending_queue = pending_queue_query.scalar() or 0

    return {
        "total_executions": total_executions,
        "success_rate": round(success_rate, 1),
        "avg_confidence": round(avg_confidence, 2),
        "avg_execution_time": round(avg_execution_time, 1),
        "total_templates": total_templates,
        "pending_queue": pending_queue,
    }


@router.get("/testing", response_class=HTMLResponse)
async def testing_guide(request: Request):
    """Testing TODO guide page"""
    return templates.TemplateResponse(
        "testing.html",
        {
            "request": request,
            "title": "Testing TODO",
        }
    )
