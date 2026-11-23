from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import settings
from ..database.connection import get_db_connection
from ..models.schemas import ExportRequest
from ..services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["Exports"])

@router.get("/{project_id}/records")
def get_project_export_records(project_id: str):
    """Retrieves all generated PDF and ZIP download records for a project."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM export_records 
        WHERE project_id = ? 
        ORDER BY created_at DESC
    """, (project_id,)).fetchall()
    conn.close()
    
    results = []
    for r in rows:
        d = dict(r)
        p = Path(d["file_path"])
        if p.exists():
            d["filename"] = p.name
            d["download_url"] = f"/api/export/{project_id}/download/{p.name}"
            results.append(d)
    return results

@router.post("/{project_id}/pdf")
def export_pdf(project_id: str, req: ExportRequest):
    try:
        result = ExportService.export_chapter_pdf(
            project_id=project_id,
            resolution_scale=req.resolution_scale,
            page_ids=req.page_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/zip")
def export_zip(project_id: str, req: ExportRequest):
    try:
        result = ExportService.export_chapter_zip(
            project_id=project_id,
            resolution_scale=req.resolution_scale
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/download/{filename}")
def download_export_file(project_id: str, filename: str):
    file_path = settings.projects_dir / project_id / "exports" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found.")
    return FileResponse(
        str(file_path), 
        filename=filename, 
        media_type="application/octet-stream"
    )
