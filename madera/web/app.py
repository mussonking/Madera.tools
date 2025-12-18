"""
MADERA MCP - Web UI Application
FastAPI app for AI-assisted training interface
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from madera.config import settings
from madera.database import init_db

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MADERA Training UI",
    description="AI-Assisted PDF Triage Training Interface",
    version="0.1.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Starting MADERA Training UI...")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️  Database initialization failed: {e}")
        logger.warning("⚠️  Web UI will run without database (limited functionality)")

# Import and register routes
from madera.web.routes import dashboard, training, api, settings as settings_routes

# Important: Define specific routes BEFORE including routers
@app.get("/")
async def root():
    """Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/training")
async def training_redirect():
    """Redirect /training to /training/ (with trailing slash)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/training/", status_code=301)


# Now include routers
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(training.router, prefix="/training", tags=["Training"])
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(settings_routes.router, prefix="/settings", tags=["Settings"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "madera-web",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "madera.web.app:app",
        host=settings.WEB_UI_HOST,
        port=settings.WEB_UI_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
