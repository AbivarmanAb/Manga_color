import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from ..config import settings
from ..database.connection import get_db_connection
from ..models.schemas import ProjectCreate, ProjectResponse
from ..services.project_service import ProjectService
from ..services.file_service import extract_zip_archive, extract_pdf_document, natural_sort_key

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def list_projects():
    return ProjectService.get_all_projects()

@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate):
    return ProjectService.create_project(data.model_dump())

@router.get("/{project_id}")
def get_project(project_id: str):
    proj = ProjectService.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    pages = ProjectService.get_project_pages(project_id)
    chars = ProjectService.get_project_by_id(project_id)
    return {
        "project": proj,
        "pages": pages
    }

@router.delete("/{project_id}")
def delete_project(project_id: str):
    conn = get_db_connection()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    
    # Clean storage
    proj_dir = settings.projects_dir / project_id
    if proj_dir.exists():
        shutil.rmtree(proj_dir, ignore_errors=True)
        
    return {"status": "success", "message": f"Project {project_id} deleted."}

@router.post("/{project_id}/upload")
async def upload_project_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Accepts individual images (PNG, JPG, WebP), ZIP archives, or PDF documents.
    Safely extracts pages, naturally sorts them, detects colored preview pages,
    and registers all pages into SQLite.
    """
    proj = ProjectService.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    proj_dir = settings.projects_dir / project_id
    temp_upload_dir = proj_dir / "temp_upload"
    temp_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Get current highest page number
    conn = get_db_connection()
    last_page = conn.execute(
        "SELECT MAX(page_number) as max_num FROM pages WHERE project_id = ?", 
        (project_id,)
    ).fetchone()
    conn.close()
    
    current_page_idx = (last_page["max_num"] or 0) + 1
    added_pages = []
    
    for upload in files:
        filename = upload.filename or "upload"
        ext = Path(filename).suffix.lower()
        temp_file = temp_upload_dir / filename
        
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
            
        if ext == ".zip":
            # Extract ZIP
            extracted = extract_zip_archive(temp_file, temp_upload_dir / f"zip_{filename}")
            for img_path in extracted:
                page_rec = ProjectService.add_page_to_project(
                    project_id=project_id,
                    source_image_path=img_path,
                    page_number=current_page_idx,
                    filename_override=img_path.name
                )
                added_pages.append(page_rec)
                current_page_idx += 1
                
        elif ext == ".pdf":
            # Extract PDF
            extracted = extract_pdf_document(temp_file, temp_upload_dir / f"pdf_{filename}")
            for img_path in extracted:
                page_rec = ProjectService.add_page_to_project(
                    project_id=project_id,
                    source_image_path=img_path,
                    page_number=current_page_idx,
                    filename_override=img_path.name
                )
                added_pages.append(page_rec)
                current_page_idx += 1
                
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            # Single image file
            page_rec = ProjectService.add_page_to_project(
                project_id=project_id,
                source_image_path=temp_file,
                page_number=current_page_idx,
                filename_override=filename
            )
            added_pages.append(page_rec)
            current_page_idx += 1
            
    # Clean temp files
    shutil.rmtree(temp_upload_dir, ignore_errors=True)
    
    return {
        "status": "success",
        "pages_added": len(added_pages),
        "total_pages": current_page_idx - 1
    }

@router.post("/{project_id}/analyze")
def trigger_chapter_analysis(project_id: str):
    """Triggers AI page analysis, character recognition, and color memory seeding."""
    res = ProjectService.analyze_project_chapter(project_id)
    return res
