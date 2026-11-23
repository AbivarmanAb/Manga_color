import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import cv2
import numpy as np

from backend.app.database.connection import get_db_connection
from backend.app.services.batch_queue import batch_queue
from backend.app.services.project_service import ProjectService

async def reprocess_user_manga():
    project_id = "proj_f0afce218b"
    print(f"Reprocessing project {project_id} with upgraded BD Manga Colorization Engine...")
    
    pages = ProjectService.get_project_pages(project_id)
    print(f"Total pages to reprocess: {len(pages)}")
    
    for page in pages:
        await batch_queue.process_single_page(project_id, page, "vibrant_anime")
        print(f" -> Processed page {page['page_number']}: {page['filename']}")
        
    print("Reprocessing completed successfully!")
    
    # Check sample page metrics
    proc_path = Path(f"storage/projects/{project_id}/processed/color_p0002_page_0002_fzImg0.jpg")
    if proc_path.exists():
        img = cv2.imread(str(proc_path))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        colored_pct = np.mean(hsv[:, :, 1] > 20) * 100
        print(f"Page 2 Colored Coverage: {colored_pct:.2f}% (Vibrant BD Colorization)")

if __name__ == "__main__":
    asyncio.run(reprocess_user_manga())
