import os
import uuid
import shutil
import cv2
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config import settings
from ..database.connection import get_db_connection
from .file_service import (
    extract_zip_archive, 
    extract_pdf_document, 
    detect_is_colored_image, 
    get_image_dimensions,
    natural_sort_key
)
from ..ai.character.detector import detect_character_regions
from ..ai.character.palette_extractor import extract_dominant_colors, categorize_character_palette
from ..ai.character.memory import CharacterColorMemorySystem

class ProjectService:
    @staticmethod
    def create_project(data: Dict[str, Any]) -> Dict[str, Any]:
        """Initializes a new manga colorization project and sets up dedicated storage directory."""
        project_id = f"proj_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        
        # Setup clean storage folders
        proj_dir = settings.projects_dir / project_id
        for sub in ["original", "processed", "previews", "references", "exports", "corrections"]:
            (proj_dir / sub).mkdir(parents=True, exist_ok=True)
            
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO projects (id, title, manga_title, chapter_num, description, mode, coloring_style, output_resolution, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'created', ?, ?)
        """, (
            project_id,
            data["title"],
            data["manga_title"],
            data.get("chapter_num", "1"),
            data.get("description", ""),
            data.get("mode", "combined"),
            data.get("coloring_style", "vibrant_anime"),
            data.get("output_resolution", "original"),
            now,
            now
        ))
        conn.commit()
        
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        conn.close()
        return dict(row)

    @staticmethod
    def get_all_projects() -> List[Dict[str, Any]]:
        """Retrieves list of all projects with statistics."""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pg.id) as page_count,
                   SUM(CASE WHEN pg.status = 'completed' THEN 1 ELSE 0 END) as completed_page_count,
                   COUNT(DISTINCT c.id) as character_count
            FROM projects p
            LEFT JOIN pages pg ON p.id = pg.project_id
            LEFT JOIN characters c ON p.id = c.project_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves single project details."""
        conn = get_db_connection()
        row = conn.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pg.id) as page_count,
                   SUM(CASE WHEN pg.status = 'completed' THEN 1 ELSE 0 END) as completed_page_count,
                   COUNT(DISTINCT c.id) as character_count
            FROM projects p
            LEFT JOIN pages pg ON p.id = pg.project_id
            LEFT JOIN characters c ON p.id = c.project_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (project_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def add_page_to_project(
        project_id: str, 
        source_image_path: Path, 
        page_number: int,
        filename_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registers a page into the project, detects colored preview status, and saves to storage."""
        proj_dir = settings.projects_dir / project_id
        orig_dir = proj_dir / "original"
        
        filename = filename_override or source_image_path.name
        dest_path = orig_dir / f"p{page_number:04d}_{filename}"
        
        if source_image_path.resolve() != dest_path.resolve():
            shutil.copy2(source_image_path, dest_path)
            
        width, height = get_image_dimensions(dest_path)
        is_colored = detect_is_colored_image(dest_path)
        
        now = datetime.now().isoformat()
        page_id = f"page_{project_id}_{page_number:04d}"
        
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO pages (
                id, project_id, page_number, filename, original_path, 
                width, height, is_colored_preview, status, stage, progress, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'Uploaded', 0, ?, ?)
        """, (
            page_id,
            project_id,
            page_number,
            filename,
            str(dest_path),
            width,
            height,
            1 if is_colored else 0,
            now,
            now
        ))
        conn.commit()
        row = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        conn.close()
        return dict(row)

    @staticmethod
    def get_project_pages(project_id: str) -> List[Dict[str, Any]]:
        """Retrieves ordered pages of a project."""
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT * FROM pages WHERE project_id = ? ORDER BY page_number ASC",
            (project_id,)
        ).fetchall()
        conn.close()
        
        pages = []
        for r in rows:
            d = dict(r)
            d["original_url"] = f"/api/pages/{d['id']}/original"
            d["preview_url"] = f"/api/pages/{d['id']}/preview" if d.get("processed_path") else d["original_url"]
            d["processed_url"] = f"/api/pages/{d['id']}/processed" if d.get("processed_path") else None
            pages.append(d)
        return pages

    @staticmethod
    def analyze_project_chapter(project_id: str) -> Dict[str, Any]:
        """
        Executes complete intelligent chapter analysis:
        1. Identifies colored preview pages vs B&W pages.
        2. In Mode B: extracts color swatches from colored preview pages.
        3. Scans all pages to identify recurring characters.
        4. Initializes Character Color Memory profiles.
        """
        conn = get_db_connection()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        pages = conn.execute("SELECT * FROM pages WHERE project_id = ? ORDER BY page_number ASC", (project_id,)).fetchall()
        conn.close()
        
        if not project or not pages:
            return {"status": "no_pages", "characters_found": 0}
            
        style = project["coloring_style"]
        colored_pages = [p for p in pages if p["is_colored_preview"]]
        
        # Step A: If colored preview pages exist (Mode B), extract reference palettes!
        extracted_ref_palettes = []
        for cpage in colored_pages:
            img = cv2.imread(cpage["original_path"])
            if img is not None:
                palette = extract_dominant_colors(img, num_colors=6)
                cat_colors = categorize_character_palette(palette)
                extracted_ref_palettes.append(cat_colors)
                
        # Step B: Scan pages for character occurrences and populate CCMS
        characters_found = []
        for page in pages:
            img = cv2.imread(page["original_path"])
            if img is None:
                continue
            detections = detect_character_regions(img)
            for det in detections:
                matched_char = CharacterColorMemorySystem.match_or_create_character(
                    project_id=project_id,
                    page_id=page["id"],
                    page_number=page["page_number"],
                    detection=det,
                    coloring_style=style
                )
                
                # If this was a colored preview page, seed the character's colors from extracted references!
                if page["is_colored_preview"] and extracted_ref_palettes:
                    ref_pal = extracted_ref_palettes[0]
                    CharacterColorMemorySystem.update_character_palette(matched_char["id"], {
                        "hair_color": ref_pal["hair_color"],
                        "skin_color": ref_pal["skin_color"],
                        "eye_color": ref_pal["eye_color"],
                        "primary_outfit_color": ref_pal["primary_outfit_color"],
                        "secondary_outfit_color": ref_pal["secondary_outfit_color"],
                        "is_locked": 1
                    })
                    
                characters_found.append(matched_char["id"])
                
        return {
            "status": "ready",
            "total_pages": len(pages),
            "colored_previews": len(colored_pages),
            "characters_detected": len(set(characters_found))
        }
