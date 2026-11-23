import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from backend.app.services.project_service import ProjectService
from backend.app.services.batch_queue import batch_queue

async def reprocess_remaining():
    project_id = "proj_f0afce218b"
    pages = ProjectService.get_project_pages(project_id)
    print(f"Total pages: {len(pages)}")
    
    # Process pages from page 4 (index 3) to 16 (index 15)
    for page in pages[3:]:
        p_num = page['page_number']
        print(f"Starting neural colorization for Page {p_num}...")
        await batch_queue.process_single_page(project_id, page, "vibrant_anime")
        print(f" -> Completed Page {p_num}!")
        
    print("All remaining pages reprocessed with Neural Manga Colorizer!")

if __name__ == "__main__":
    asyncio.run(reprocess_remaining())
