import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from backend.app.services.project_service import ProjectService
from backend.app.services.batch_queue import batch_queue
from backend.app.services.export_service import ExportService

async def reprocess_all():
    project_id = "proj_f0afce218b"
    pages = ProjectService.get_project_pages(project_id)
    print(f"Reprocessing all {len(pages)} pages with High-Resolution Neural Manga Colorizer...")
    
    success_count = 0
    for page in pages:
        p_num = page['page_number']
        try:
            await batch_queue.process_single_page(project_id, page, "vibrant_anime")
            print(f" [OK] Page {p_num:02d} ({page['filename']}) colorized successfully.")
            success_count += 1
        except Exception as e:
            print(f" [FAIL] Page {p_num:02d} failed: {e}")

    print(f"\nFinished: {success_count}/{len(pages)} pages colorized successfully!")
    
    # Regenerate exports
    print("Regenerating PDF and ZIP exports...")
    pdf = ExportService.export_chapter_pdf(project_id, 'original')
    print("PDF export ready:", pdf['filename'], f"{pdf['file_size_bytes'] / (1024*1024):.1f} MB")
    zip_exp = ExportService.export_chapter_zip(project_id, 'original')
    print("ZIP export ready:", zip_exp['filename'], f"{zip_exp['file_size_bytes'] / (1024*1024):.1f} MB")

if __name__ == "__main__":
    asyncio.run(reprocess_all())
