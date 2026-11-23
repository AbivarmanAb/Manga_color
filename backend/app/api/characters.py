import uuid
import shutil
import cv2
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from ..config import settings
from ..database.connection import get_db_connection
from ..models.schemas import CharacterCreate, CharacterUpdate, CharacterResponse
from ..ai.character.memory import CharacterColorMemorySystem
from ..ai.character.palette_extractor import extract_dominant_colors, categorize_character_palette

router = APIRouter(prefix="/api/characters", tags=["Characters & Color Memory"])

@router.get("/project/{project_id}")
def get_project_characters(project_id: str):
    return CharacterColorMemorySystem.get_project_characters(project_id)

@router.post("/project/{project_id}")
def create_character(project_id: str, data: CharacterCreate):
    char_id = f"char_{project_id}_{uuid.uuid4().hex[:6]}"
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO characters (
            id, project_id, name, hair_color, skin_color, eye_color,
            primary_outfit_color, secondary_outfit_color, accent_color,
            confidence_score, first_appearance_page, last_appearance_page,
            is_locked, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (
        char_id,
        project_id,
        data.name,
        data.hair_color,
        data.skin_color,
        data.eye_color,
        data.primary_outfit_color,
        data.secondary_outfit_color,
        data.accent_color,
        data.confidence_score,
        data.first_appearance_page,
        data.last_appearance_page,
        1 if data.is_locked else 0
    ))
    conn.commit()
    row = conn.execute("SELECT * FROM characters WHERE id = ?", (char_id,)).fetchone()
    conn.close()
    return dict(row)

@router.patch("/{character_id}")
def update_character(character_id: str, data: CharacterUpdate):
    updated = CharacterColorMemorySystem.update_character_palette(
        character_id, data.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated

@router.post("/{character_id}/propagate")
def propagate_character_colors_to_chapter(character_id: str):
    """
    Propagates updated/locked character colors to all appearances across the chapter.
    Marks affected pages for re-processing so updated colors take effect!
    """
    conn = get_db_connection()
    char = conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
        
    # Find all pages where this character appeared
    appearances = conn.execute(
        "SELECT DISTINCT page_id FROM character_appearances WHERE character_id = ?",
        (character_id,)
    ).fetchall()
    
    page_ids = [a["page_id"] for a in appearances]
    
    if page_ids:
        placeholders = ','.join('?' * len(page_ids))
        conn.execute(
            f"UPDATE pages SET status = 'retry', stage = 'Reprocess Pending' WHERE id IN ({placeholders})",
            page_ids
        )
        conn.commit()
        
    conn.close()
    return {
        "status": "success",
        "character_id": character_id,
        "affected_pages": len(page_ids),
        "message": f"Updated colors locked and {len(page_ids)} pages queued for regeneration."
    }

@router.post("/project/{project_id}/reference-upload")
async def upload_character_reference(
    project_id: str,
    character_name: str = Form("Reference Character"),
    file: UploadFile = File(...)
):
    """
    Ingests official character artwork (Mode C), extracts dominant color swatches,
    and automatically builds a Character Color Memory profile.
    """
    proj_dir = settings.projects_dir / project_id
    ref_dir = proj_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    
    file_id = uuid.uuid4().hex[:8]
    ext = Path(file.filename or "ref.png").suffix.lower()
    dest_path = ref_dir / f"ref_{file_id}{ext}"
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Analyze uploaded reference image
    img_bgr = cv2.imread(str(dest_path))
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image file uploaded.")
        
    palette = extract_dominant_colors(img_bgr, num_colors=6)
    cat_palette = categorize_character_palette(palette)
    
    # Create Character Profile linked to this reference
    char_id = f"char_{project_id}_{file_id[:4]}"
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO characters (
            id, project_id, name, hair_color, skin_color, eye_color,
            primary_outfit_color, secondary_outfit_color, accent_color,
            confidence_score, first_appearance_page, last_appearance_page,
            avatar_path, is_locked, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.95, 1, 1, ?, 1, datetime('now'), datetime('now'))
    """, (
        char_id,
        project_id,
        character_name,
        cat_palette["hair_color"],
        cat_palette["skin_color"],
        cat_palette["eye_color"],
        cat_palette["primary_outfit_color"],
        cat_palette["secondary_outfit_color"],
        cat_palette["accent_color"],
        str(dest_path)
    ))
    
    # Save reference record
    ref_id = f"ref_{file_id}"
    conn.execute("""
        INSERT INTO reference_images (id, project_id, character_id, file_path, source_type, created_at)
        VALUES (?, ?, ?, ?, 'official_art', datetime('now'))
    """, (ref_id, project_id, char_id, str(dest_path)))
    
    conn.commit()
    char_row = conn.execute("SELECT * FROM characters WHERE id = ?", (char_id,)).fetchone()
    conn.close()
    
    return {
        "status": "success",
        "character": dict(char_row),
        "extracted_palette": cat_palette
    }
