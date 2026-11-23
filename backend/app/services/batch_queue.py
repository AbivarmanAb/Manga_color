import asyncio
import cv2
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import settings
from ..database.connection import get_db_connection
from ..core.hardware import clear_vram
from ..ai.adapter import engine_router
from ..ai.character.detector import detect_character_regions
from ..ai.character.memory import CharacterColorMemorySystem
from ..ai.quality.checker import run_quality_check

class BatchProcessingQueue:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.current_project_id: Optional[str] = None
        self.current_page_id: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    def start_project_processing(self, project_id: str):
        """Launches background asynchronous sequential chapter processing."""
        if self.is_running and self.current_project_id == project_id:
            self.is_paused = False
            return
            
        self.is_running = True
        self.is_paused = False
        self.current_project_id = project_id
        
        # Update project status
        conn = get_db_connection()
        conn.execute("UPDATE projects SET status = 'processing', updated_at = datetime('now') WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()
        
        self._task = asyncio.create_task(self._process_loop(project_id))

    def pause_processing(self):
        self.is_paused = True
        if self.current_project_id:
            conn = get_db_connection()
            conn.execute("UPDATE projects SET status = 'paused', updated_at = datetime('now') WHERE id = ?", (self.current_project_id,))
            conn.commit()
            conn.close()

    def resume_processing(self):
        self.is_paused = False
        if self.current_project_id:
            conn = get_db_connection()
            conn.execute("UPDATE projects SET status = 'processing', updated_at = datetime('now') WHERE id = ?", (self.current_project_id,))
            conn.commit()
            conn.close()

    def stop_processing(self):
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
        if self.current_project_id:
            conn = get_db_connection()
            conn.execute("UPDATE projects SET status = 'ready', updated_at = datetime('now') WHERE id = ?", (self.current_project_id,))
            conn.commit()
            conn.close()

    async def _process_loop(self, project_id: str):
        """Sequential single-page processing loop. Loads only 1 page into RAM/VRAM at a time."""
        try:
            while self.is_running:
                if self.is_paused:
                    await asyncio.sleep(0.5)
                    continue
                    
                # Fetch next pending or failed page to process
                conn = get_db_connection()
                page = conn.execute("""
                    SELECT * FROM pages 
                    WHERE project_id = ? AND status IN ('pending', 'retry')
                    ORDER BY page_number ASC 
                    LIMIT 1
                """, (project_id,)).fetchone()
                
                project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
                conn.close()
                
                if not page:
                    # All pages finished!
                    self.is_running = False
                    conn = get_db_connection()
                    conn.execute("UPDATE projects SET status = 'completed', updated_at = datetime('now') WHERE id = ?", (project_id,))
                    conn.commit()
                    conn.close()
                    break
                    
                page_dict = dict(page)
                self.current_page_id = page_dict["id"]
                
                await self.process_single_page(project_id, page_dict, project["coloring_style"])
                
                # Give event loop time to breathe and clear VRAM
                clear_vram()
                await asyncio.sleep(0.05)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Batch processing exception: {e}")
        finally:
            self.is_running = False
            self.current_page_id = None

    async def process_single_page(self, project_id: str, page: Dict[str, Any], coloring_style: str):
        """Processes one single page through all 6 AI stages with detailed progress tracking."""
        page_id = page["id"]
        orig_path = Path(page["original_path"])
        proj_dir = settings.projects_dir / project_id
        processed_dir = proj_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        target_processed_path = processed_dir / f"color_{orig_path.name}"
        
        def update_stage(stage_name: str, progress_pct: int, status_str: str = "colorizing"):
            c = get_db_connection()
            c.execute("""
                UPDATE pages 
                SET stage = ?, progress = ?, status = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (stage_name, progress_pct, status_str, page_id))
            c.commit()
            c.close()

        try:
            # Stage 1: Load image & Image Preprocessing
            update_stage("Preprocessing & Line Isolation", 15)
            await asyncio.sleep(0.02)
            
            img_bgr = cv2.imread(str(orig_path))
            if img_bgr is None:
                raise ValueError(f"Failed to read image at {orig_path}")
                
            # If the page is already a colored preview page (e.g. cover page), copy and mark complete
            if page.get("is_colored_preview"):
                cv2.imwrite(str(target_processed_path), img_bgr)
                c = get_db_connection()
                c.execute("""
                    UPDATE pages 
                    SET processed_path = ?, status = 'completed', stage = 'Colored Preview', progress = 100, updated_at = datetime('now')
                    WHERE id = ?
                """, (str(target_processed_path), page_id))
                c.commit()
                c.close()
                return

            # Stage 2: Character Detection & Memory Association
            update_stage("Character & Semantic Recognition", 35)
            await asyncio.sleep(0.02)
            
            detections = detect_character_regions(img_bgr)
            matched_characters = []
            for det in detections:
                char_info = CharacterColorMemorySystem.match_or_create_character(
                    project_id=project_id,
                    page_id=page_id,
                    page_number=page["page_number"],
                    detection=det,
                    coloring_style=coloring_style
                )
                # Combine bounding box with character colors
                char_info["character_bbox"] = det.get("character_bbox")
                char_info["face_bbox"] = det.get("face_bbox")
                matched_characters.append(char_info)
                
            # Stage 3: Color Synthesis & Diffusion
            update_stage("Neural Color Propagation", 65)
            await asyncio.sleep(0.02)
            
            colored_bgr, report = engine_router.colorize_page(
                img_bgr, 
                character_profiles=matched_characters,
                coloring_style=coloring_style
            )
            
            # Stage 4: Line Art & Speech Bubble Locking
            update_stage("Line Art Compositing & Protection", 85)
            await asyncio.sleep(0.02)
            
            # Save processed image to disk (respecting file format)
            if target_processed_path.suffix.lower() in [".jpg", ".jpeg"]:
                cv2.imwrite(str(target_processed_path), colored_bgr, [cv2.IMWRITE_JPEG_QUALITY, 96])
            else:
                cv2.imwrite(str(target_processed_path), colored_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 4])
            
            # Stage 5: Quality Check
            update_stage("Automated Quality Audit", 95)
            from ..ai.preprocessing.layout import detect_speech_bubbles_and_text
            bubble_mask = detect_speech_bubbles_and_text(img_bgr)
            qa_report = run_quality_check(img_bgr, colored_bgr, bubble_mask)
            
            # Update DB to completed!
            final_status = "completed" if qa_report["passed"] else "quality_flagged"
            c = get_db_connection()
            c.execute("""
                UPDATE pages 
                SET processed_path = ?, status = ?, stage = 'Completed', progress = 100, 
                    quality_report_json = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (str(target_processed_path), final_status, json.dumps(qa_report), page_id))
            c.commit()
            c.close()
            
        except Exception as e:
            print(f"Error processing page {page_id}: {e}")
            c = get_db_connection()
            c.execute("""
                UPDATE pages 
                SET status = 'failed', stage = 'Failed', error_message = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (str(e), page_id))
            c.commit()
            c.close()

# Global batch queue instance
batch_queue = BatchProcessingQueue()
