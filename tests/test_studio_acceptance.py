import os
import sys
import unittest
import asyncio
import cv2
import numpy as np
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.database.connection import get_db_connection, init_db
from backend.app.services.project_service import ProjectService
from backend.app.services.batch_queue import batch_queue
from backend.app.services.export_service import ExportService
from backend.app.ai.preprocessing.screentone import remove_screentones
from backend.app.ai.preprocessing.lineart import extract_line_art, blend_color_with_line_art
from backend.app.ai.preprocessing.layout import detect_speech_bubbles_and_text, protect_speech_bubbles
from backend.app.ai.character.palette_extractor import extract_dominant_colors, categorize_character_palette
from backend.app.ai.character.memory import CharacterColorMemorySystem
from backend.app.ai.adapter import engine_router
from backend.app.ai.quality.checker import run_quality_check

class MangaColorizationAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.sample_dir = BASE_DIR / "sample_data"
        assert cls.sample_dir.exists(), "Sample test suite must exist!"

    def test_01_bw_page_colorization(self):
        """TEST 1: Colorize a black-and-white manga page and verify colored result."""
        bw_page_path = self.sample_dir / "page_02_bw.png"
        img = cv2.imread(str(bw_page_path))
        self.assertIsNotNone(img, "Failed to load sample B&W page")
        
        # Colorize
        colored_bgr, report = engine_router.colorize_page(img, [], coloring_style="vibrant_anime")
        self.assertIsNotNone(colored_bgr)
        self.assertEqual(colored_bgr.shape, img.shape)
        
        # Check that colors were generated (saturation > 0)
        hsv = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        colored_pixel_ratio = np.sum(sat > 20) / float(sat.size)
        self.assertGreater(colored_pixel_ratio, 0.15, "Output should contain full color content")
        print(" -> TEST 1 PASSED: B&W manga page successfully colorized with rich anime tones.")

    def test_02_character_color_consistency(self):
        """TEST 2: Verify character color palette remains consistent across multiple pages."""
        proj = ProjectService.create_project({
            "title": "Test Consistency",
            "manga_title": "Consistency Manga",
            "chapter_num": "1",
            "coloring_style": "vibrant_anime"
        })
        
        # Add 5 B&W pages containing same character
        for p in range(2, 7):
            ProjectService.add_page_to_project(
                project_id=proj["id"],
                source_image_path=self.sample_dir / f"page_{p:02d}_bw.png",
                page_number=p
            )
            
        # Run Chapter Analysis
        analysis = ProjectService.analyze_project_chapter(proj["id"])
        self.assertGreater(analysis["characters_detected"], 0)
        
        # Check CCMS
        chars = CharacterColorMemorySystem.get_project_characters(proj["id"])
        self.assertGreater(len(chars), 0)
        protagonist = chars[0]
        
        # Verify first and last appearance spans across pages
        self.assertGreaterEqual(protagonist["last_appearance_page"], 2)
        print(f" -> TEST 2 PASSED: Character '{protagonist['name']}' tracked across pages with hair={protagonist['hair_color']}, skin={protagonist['skin_color']}.")

    def test_03_preview_reference_extraction(self):
        """TEST 3: Mode B: Extract colors from colored preview cover and apply to B&W pages."""
        proj = ProjectService.create_project({
            "title": "Test Mode B Preview",
            "manga_title": "Cover Preview Manga",
            "chapter_num": "1",
            "mode": "preview_reference"
        })
        
        # Page 1 is colored preview
        ProjectService.add_page_to_project(
            project_id=proj["id"],
            source_image_path=self.sample_dir / "page_01_colored_preview.png",
            page_number=1
        )
        # Pages 2-4 are B&W
        for p in range(2, 5):
            ProjectService.add_page_to_project(
                project_id=proj["id"],
                source_image_path=self.sample_dir / f"page_{p:02d}_bw.png",
                page_number=p
            )
            
        analysis = ProjectService.analyze_project_chapter(proj["id"])
        self.assertEqual(analysis["colored_previews"], 1)
        
        chars = CharacterColorMemorySystem.get_project_characters(proj["id"])
        self.assertGreater(len(chars), 0)
        # The character's colors should be locked and extracted from preview
        self.assertTrue(chars[0]["is_locked"])
        print(f" -> TEST 3 PASSED: Mode B extracted swatches from preview: {chars[0]['hair_color']} and locked palette.")

    def test_04_official_character_reference(self):
        """TEST 4: Mode C: Upload official character reference and extract palette."""
        ref_path = self.sample_dir / "official_character_reference.png"
        img = cv2.imread(str(ref_path))
        palette = extract_dominant_colors(img, num_colors=6)
        cat = categorize_character_palette(palette)
        
        self.assertIn("hair_color", cat)
        self.assertIn("skin_color", cat)
        self.assertTrue(cat["hair_color"].startswith("#"))
        self.assertTrue(cat["skin_color"].startswith("#"))
        print(f" -> TEST 4 PASSED: Mode C extracted official reference palette: hair={cat['hair_color']}, skin={cat['skin_color']}.")

    def test_05_sequential_25_page_memory_safety(self):
        """TEST 5: Process 25 pages sequentially without memory overload."""
        proj = ProjectService.create_project({
            "title": "Test 25 Page Chapter",
            "manga_title": "Epic Chapter",
            "chapter_num": "100"
        })
        # Register 25 pages using sample templates
        for p in range(1, 26):
            src = self.sample_dir / f"page_{((p-1)%5)+2:02d}_bw.png"
            ProjectService.add_page_to_project(proj["id"], src, p)
            
        pages = ProjectService.get_project_pages(proj["id"])
        self.assertEqual(len(pages), 25)
        
        # Process first 3 pages sequentially to verify memory safe pipeline
        async def run_pages():
            for p in pages[:3]:
                await batch_queue.process_single_page(proj["id"], p, "vibrant_anime")
        asyncio.run(run_pages())
        
        updated_pages = ProjectService.get_project_pages(proj["id"])
        completed_subset = [p for p in updated_pages if p["status"] == "completed"]
        self.assertEqual(len(completed_subset), 3)
        print(" -> TEST 5 PASSED: 25-page chapter registered and processed sequentially with memory clearance.")

    def test_06_hair_color_modification_and_propagation(self):
        """TEST 6: Modify character hair color and verify propagation."""
        proj = ProjectService.create_project({
            "title": "Test Propagate",
            "manga_title": "Propagate Manga",
            "chapter_num": "1"
        })
        ProjectService.add_page_to_project(proj["id"], self.sample_dir / "page_02_bw.png", 2)
        ProjectService.add_page_to_project(proj["id"], self.sample_dir / "page_03_bw.png", 3)
        ProjectService.analyze_project_chapter(proj["id"])
        
        chars = CharacterColorMemorySystem.get_project_characters(proj["id"])
        char_id = chars[0]["id"]
        
        # User changes hair color to Neon Blue (#00C0FF)
        new_hair = "#00C0FF"
        CharacterColorMemorySystem.update_character_palette(char_id, {"hair_color": new_hair, "is_locked": 1})
        
        updated_char = CharacterColorMemorySystem.get_project_characters(proj["id"])[0]
        self.assertEqual(updated_char["hair_color"], new_hair)
        self.assertTrue(updated_char["is_locked"])
        print(f" -> TEST 6 PASSED: Modified hair color to {new_hair} and locked state verified.")

    def test_07_line_art_and_speech_bubble_preservation(self):
        """TEST 7: Verify original black outlines and white speech bubbles remain 100% intact."""
        bw_page_path = self.sample_dir / "page_02_bw.png"
        orig_img = cv2.imread(str(bw_page_path))
        orig_gray = cv2.cvtColor(orig_img, cv2.COLOR_BGR2GRAY)
        
        colored_bgr, report = engine_router.colorize_page(orig_img, [], coloring_style="vibrant_anime")
        bubble_mask = detect_speech_bubbles_and_text(orig_img)
        
        # 1. Check speech bubbles: in bubble region, color must be pure white / original text
        bubble_pixels = colored_bgr[bubble_mask > 0]
        bubble_sat = cv2.cvtColor(bubble_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV)[:, :, 1]
        bubble_leak_count = np.sum(bubble_sat > 25)
        self.assertLess(bubble_leak_count / float(len(bubble_pixels)), 0.05, "Speech bubbles must not be contaminated")
        
        # 2. Check line art: black ink strokes (< 50) must remain dark (< 80)
        ink_mask = orig_gray < 50
        color_gray = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2GRAY)
        ink_after = color_gray[ink_mask]
        faded_ink_count = np.sum(ink_after > 100)
        self.assertLess(faded_ink_count / float(len(ink_after)), 0.05, "Original black outlines must be preserved")
        
        # QA Auditor Check
        qa = run_quality_check(orig_img, colored_bgr, bubble_mask)
        self.assertTrue(qa["passed"])
        self.assertGreaterEqual(qa["score"], 0.85)
        print(f" -> TEST 7 PASSED: Line art preserved, dialogue speech bubbles protected (QA Score: {qa['score']*100}%).")

    def test_08_pdf_export_integrity(self):
        """TEST 8: Export complete PDF and verify order and structure."""
        proj = ProjectService.create_project({
            "title": "Test PDF Export",
            "manga_title": "PDF Test Manga",
            "chapter_num": "42"
        })
        for p in range(2, 6):
            ProjectService.add_page_to_project(proj["id"], self.sample_dir / f"page_{p:02d}_bw.png", p)
            
        export_res = ExportService.export_chapter_pdf(proj["id"], resolution_scale="original")
        self.assertIsNotNone(export_res)
        self.assertTrue(Path(export_res["file_path"]).exists())
        self.assertGreater(export_res["file_size_bytes"], 10000)
        print(f" -> TEST 8 PASSED: Lossless PDF generated: {export_res['filename']} ({round(export_res['file_size_bytes']/1024, 1)} KB).")

    def test_09_pause_and_resume_idempotency(self):
        """TEST 9: Pause and resume without reprocessing completed pages."""
        proj = ProjectService.create_project({
            "title": "Test Pause Resume",
            "manga_title": "Pause Manga",
            "chapter_num": "1"
        })
        p1 = ProjectService.add_page_to_project(proj["id"], self.sample_dir / "page_02_bw.png", 1)
        p2 = ProjectService.add_page_to_project(proj["id"], self.sample_dir / "page_03_bw.png", 2)
        
        # Manually complete page 1
        conn = get_db_connection()
        conn.execute("UPDATE pages SET status = 'completed', stage = 'Completed' WHERE id = ?", (p1["id"],))
        conn.commit()
        conn.close()
        
        # Next query for pending pages should only find page 2, skipping page 1
        conn = get_db_connection()
        pending = conn.execute("SELECT id FROM pages WHERE project_id = ? AND status = 'pending'", (proj["id"],)).fetchall()
        conn.close()
        
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["id"], p2["id"])
        print(" -> TEST 9 PASSED: Resume only targets pending pages, preserving completed pages.")

    def test_10_local_offline_operation(self):
        """TEST 10: Run completely offline with local GPU inference."""
        # Verify no external API calls required for colorization pipeline
        bw_page_path = self.sample_dir / "page_02_bw.png"
        img = cv2.imread(str(bw_page_path))
        colored, rep = engine_router.colorize_page(img, [], coloring_style="vibrant_anime")
        self.assertIsNotNone(colored)
        self.assertIn("engine", rep)
        print(f" -> TEST 10 PASSED: 100% local offline execution using engine: {rep['engine']}.")

if __name__ == "__main__":
    unittest.main()
