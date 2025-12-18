"""
MADERA MCP - Training Routes
Upload, analysis, and validation workflows
"""
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import uuid
import shutil

from madera.training.bot import TrainingBot
from madera.config import settings
from madera.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Upload directory
UPLOAD_DIR = Path("/tmp/madera_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def training_home(request: Request):
    """Training home page - upload interface"""
    response = templates.TemplateResponse(
        "training/upload.html",
        {
            "request": request,
            "title": "Training - Upload PDFs",
            "supported_modes": ["logo_detection", "zone_extraction"],
            "max_files": 50,
        }
    )
    # Prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    mode: str = Form("logo_detection"),
    document_type: Optional[str] = Form(None)
):
    """
    Upload PDFs for training

    Args:
        files: List of PDF files (max 50)
        mode: "logo_detection" or "zone_extraction"
        document_type: Optional document type hint

    Returns:
        {
            "session_id": "uuid",
            "files_uploaded": 30,
            "mode": "logo_detection"
        }
    """
    # Validate
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files allowed")

    if mode not in ["logo_detection", "zone_extraction"]:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # Create session
    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting upload session {session_id}: {len(files)} files, mode={mode}")

    # Save files
    uploaded_files = []

    for file in files:
        if not file.filename.endswith('.pdf'):
            continue

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_path = session_dir / f"{file_id}.pdf"

        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        uploaded_files.append({
            "file_id": file_id,
            "original_name": file.filename,
            "path": str(file_path),
        })

    logger.info(f"Session {session_id}: Uploaded {len(uploaded_files)} files")

    return JSONResponse({
        "success": True,
        "session_id": session_id,
        "files_uploaded": len(uploaded_files),
        "files": uploaded_files,
        "mode": mode,
        "document_type": document_type,
    })


@router.post("/analyze/{session_id}")
async def analyze_session(
    session_id: str,
    mode: str = Form("logo_detection"),
    document_type: Optional[str] = Form(None)
):
    """
    Analyze uploaded files with AI bot

    Args:
        session_id: Upload session ID
        mode: Analysis mode
        document_type: Optional document type hint

    Returns:
        {
            "session_id": "uuid",
            "results": [...],
            "total_analyzed": 30
        }
    """
    session_dir = UPLOAD_DIR / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all PDFs in session
    pdf_files = list(session_dir.glob("*.pdf"))

    if not pdf_files:
        raise HTTPException(status_code=400, detail="No files to analyze")

    logger.info(f"Analyzing session {session_id}: {len(pdf_files)} files")

    # Initialize bot
    bot = TrainingBot()

    # Analyze files
    results = []

    for pdf_path in pdf_files:
        try:
            if mode == "logo_detection":
                analysis = await bot.analyze_for_logo_detection(pdf_path, document_type)
            elif mode == "zone_extraction":
                analysis = await bot.analyze_for_zone_extraction(pdf_path, "auto")
            else:
                raise ValueError(f"Invalid mode: {mode}")

            results.append({
                "file_id": pdf_path.stem,
                "original_name": pdf_path.name,
                "success": True,
                "analysis": analysis,
            })

        except Exception as e:
            logger.error(f"Failed to analyze {pdf_path}: {e}")
            results.append({
                "file_id": pdf_path.stem,
                "original_name": pdf_path.name,
                "success": False,
                "error": str(e),
            })

    logger.info(f"Session {session_id}: Analysis complete - {len(results)} results")

    # Save results to JSON file for validation page
    import json
    results_file = session_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "results": results,
            "total_analyzed": len(results),
            "mode": mode,
        }, f, indent=2)

    return JSONResponse({
        "session_id": session_id,
        "results": results,
        "total_analyzed": len(results),
        "mode": mode,
        "success": True,
    })


@router.get("/validate/{session_id}", response_class=HTMLResponse)
async def validation_page(
    request: Request,
    session_id: str
):
    """
    Validation page with Fabric.js interface

    Args:
        session_id: Training session ID

    Returns:
        HTML page with visual validation interface
    """
    session_dir = UPLOAD_DIR / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    # Get session files
    pdf_files = list(session_dir.glob("*.pdf"))

    response = templates.TemplateResponse(
        "training/validate.html",
        {
            "request": request,
            "title": "Training - Validate Results",
            "session_id": session_id,
            "total_files": len(pdf_files),
        }
    )
    # Prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/api/session/{session_id}/results")
async def get_session_results(session_id: str):
    """
    Get session analysis results with image URLs

    Returns:
        {
            "files": [
                {
                    "file_id": "uuid",
                    "original_name": "doc.pdf",
                    "image_url": "/api/sessions/{session_id}/preview/{file_id}",
                    "analysis": {...}
                }
            ]
        }
    """
    from pdf2image import convert_from_path
    import json

    session_dir = UPLOAD_DIR / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    # Load analysis results
    results_file = session_dir / "results.json"
    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Analysis not completed")

    with open(results_file, "r") as f:
        analysis_results = json.load(f)

    # Convert PDFs to images
    files_data = []
    for result in analysis_results.get("results", []):
        file_id = result["file_id"]
        pdf_path = session_dir / f"{file_id}.pdf"

        if pdf_path.exists():
            # Convert first page to image
            images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=150)
            if images:
                # Save as PNG
                img_path = session_dir / f"{file_id}.png"
                images[0].save(img_path, "PNG")

                files_data.append({
                    "file_id": file_id,
                    "original_name": result.get("original_name", f"{file_id}.pdf"),
                    "image_url": f"/training/api/session/{session_id}/preview/{file_id}",
                    "analysis": result.get("analysis", {})
                })

    return JSONResponse({"files": files_data})


@router.get("/api/session/{session_id}/preview/{file_id}")
async def get_file_preview(session_id: str, file_id: str):
    """
    Serve PNG preview of PDF page

    Returns:
        PNG image
    """
    from fastapi.responses import FileResponse

    session_dir = UPLOAD_DIR / session_id
    img_path = session_dir / f"{file_id}.png"

    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Preview not found")

    return FileResponse(img_path, media_type="image/png")


@router.post("/validate/{session_id}")
async def save_validation(
    session_id: str,
    file_id: str = Form(...),
    validated_data: str = Form(...),  # JSON string
    db: AsyncSession = Depends(get_db)
):
    """
    Save validated training data

    Args:
        session_id: Training session ID
        file_id: File being validated
        validated_data: User-corrected data (JSON)

    Returns:
        {
            "success": true,
            "template_id": 123
        }
    """
    import json
    from madera.database import ToolTemplate
    from datetime import datetime

    # Parse validated data
    try:
        data = json.loads(validated_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    # Save to database
    try:
        template = ToolTemplate(
            tool_name=data.get("tool_name", "logo_detector"),
            document_type=data.get("document_type"),
            logo_name=data.get("logo_name"),
            zones=data.get("zones", {}),
            thresholds=data.get("thresholds", {}),
            is_active=True,
            precision_rate=data.get("confidence", 0.0),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        logger.info(f"Saved template {template.id} from session {session_id}")

        return JSONResponse({
            "success": True,
            "template_id": template.id,
        })
    except Exception as e:
        logger.error(f"Failed to save validation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """
    Cleanup training session files

    Args:
        session_id: Session to cleanup

    Returns:
        {"success": true}
    """
    session_dir = UPLOAD_DIR / session_id

    if session_dir.exists():
        shutil.rmtree(session_dir)
        logger.info(f"Cleaned up session {session_id}")

    return JSONResponse({"success": True})
