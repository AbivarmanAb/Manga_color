import os
import uuid
import zipfile
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from ..config import settings
from ..database.connection import get_db_connection

class ExportService:
    @staticmethod
    def export_chapter_pdf(
        project_id: str, 
        resolution_scale: str = "original",
        page_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a professional, high-resolution full-color PDF of the manga chapter.
        Strictly preserves original page order, aspect ratios, and color fidelity.
        """
        conn = get_db_connection()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        
        query = "SELECT * FROM pages WHERE project_id = ? ORDER BY page_number ASC"
        pages = conn.execute(query, (project_id,)).fetchall()
        conn.close()
        
        if not pages:
            raise ValueError("No pages found to export.")
            
        proj_dir = settings.projects_dir / project_id
        exports_dir = proj_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        manga_title_clean = "".join([c if c.isalnum() else "_" for c in project["manga_title"]])
        pdf_filename = f"{manga_title_clean}_Ch{project['chapter_num']}_Color.pdf"
        pdf_path = exports_dir / pdf_filename
        
        c = canvas.Canvas(str(pdf_path))
        
        scale_factor = 2 if resolution_scale == "2x" else (4 if resolution_scale == "4x" else 1)
        
        for row in pages:
            p = dict(row)
            # Use processed colored image if available, otherwise original
            img_path = Path(p["processed_path"]) if p.get("processed_path") and Path(p["processed_path"]).exists() else Path(p["original_path"])
            
            with Image.open(img_path) as img:
                w, h = img.size
                if scale_factor > 1:
                    img = img.resize((w * scale_factor, h * scale_factor), Image.Resampling.LANCZOS)
                    
                # Setup page dimensions matching exact manga page aspect ratio in points (1 pt = 1/72 inch)
                pdf_w = w * 0.75
                pdf_h = h * 0.75
                c.setPageSize((pdf_w, pdf_h))
                
                # Draw image directly to fill entire canvas without white borders
                c.drawImage(ImageReader(img), 0, 0, width=pdf_w, height=pdf_h)
                c.showPage()
                
        c.save()
        
        file_size = os.path.getsize(pdf_path)
        record_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO export_records (id, project_id, export_type, file_path, resolution_scale, file_size_bytes, created_at)
            VALUES (?, ?, 'pdf', ?, ?, ?, datetime('now'))
        """, (record_id, project_id, str(pdf_path), resolution_scale, file_size))
        conn.commit()
        conn.close()
        
        return {
            "id": record_id,
            "filename": pdf_filename,
            "file_path": str(pdf_path),
            "file_size_bytes": file_size,
            "download_url": f"/api/export/{project_id}/download/{pdf_filename}"
        }

    @staticmethod
    def export_chapter_zip(
        project_id: str, 
        resolution_scale: str = "original"
    ) -> Dict[str, Any]:
        """Packages all colorized chapter pages into a sorted, structured ZIP file."""
        conn = get_db_connection()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        pages = conn.execute("SELECT * FROM pages WHERE project_id = ? ORDER BY page_number ASC", (project_id,)).fetchall()
        conn.close()
        
        proj_dir = settings.projects_dir / project_id
        exports_dir = proj_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        manga_title_clean = "".join([c if c.isalnum() else "_" for c in project["manga_title"]])
        zip_filename = f"{manga_title_clean}_Ch{project['chapter_num']}_Color_Pages.zip"
        zip_path = exports_dir / zip_filename
        
        scale_factor = 2 if resolution_scale == "2x" else 1
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for row in pages:
                p = dict(row)
                img_path = Path(p["processed_path"]) if p.get("processed_path") and Path(p["processed_path"]).exists() else Path(p["original_path"])
                arcname = f"page_{p['page_number']:04d}.png"
                
                if scale_factor > 1:
                    with Image.open(img_path) as img:
                        w, h = img.size
                        scaled = img.resize((w * scale_factor, h * scale_factor), Image.Resampling.LANCZOS)
                        tmp_scaled = exports_dir / f"tmp_{arcname}"
                        scaled.save(tmp_scaled, "PNG")
                        zip_file.write(tmp_scaled, arcname=arcname)
                        if tmp_scaled.exists():
                            tmp_scaled.unlink()
                else:
                    zip_file.write(img_path, arcname=arcname)
                    
        file_size = os.path.getsize(zip_path)
        record_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO export_records (id, project_id, export_type, file_path, resolution_scale, file_size_bytes, created_at)
            VALUES (?, ?, 'zip', ?, ?, ?, datetime('now'))
        """, (record_id, project_id, str(zip_path), resolution_scale, file_size))
        conn.commit()
        conn.close()
        
        return {
            "id": record_id,
            "filename": zip_filename,
            "file_path": str(zip_path),
            "file_size_bytes": file_size,
            "download_url": f"/api/export/{project_id}/download/{zip_filename}"
        }

    @staticmethod
    def generate_before_after_comparison(page_id: str) -> Path:
        """Creates a side-by-side split comparison image of black & white original vs full color."""
        conn = get_db_connection()
        page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        conn.close()
        
        if not page or not page["processed_path"]:
            raise ValueError("Processed page not found for comparison.")
            
        orig = cv2.imread(page["original_path"])
        color = cv2.imread(page["processed_path"])
        
        # Match dimensions if needed
        h, w = orig.shape[:2]
        color_resized = cv2.resize(color, (w, h))
        
        # Side-by-side comparison
        combined = np.hstack([orig, color_resized])
        
        # Overlay divider and labels
        divider_x = w
        cv2.line(combined, (divider_x, 0), (divider_x, h), (180, 100, 255), 4)
        
        out_path = Path(page["processed_path"]).parent / f"comparison_{page_id}.png"
        cv2.imwrite(str(out_path), combined)
        return out_path
