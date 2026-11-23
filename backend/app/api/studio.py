import cv2
import numpy as np
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse

from ..database.connection import get_db_connection
from ..models.schemas import StudioColorAction, ManualCorrectionSave
from ..ai.character.palette_extractor import hex_to_bgr
from ..ai.preprocessing.lineart import blend_color_with_line_art
from ..services.batch_queue import batch_queue
from ..services.export_service import ExportService

router = APIRouter(prefix="/api/studio", tags=["Colorization Studio"])

@router.post("/page/{page_id}/flood-fill")
def smart_flood_fill(page_id: str, action: StudioColorAction):
    """
    Intelligent boundary-aware flood fill for manga line art.
    Fills an enclosed region using original manga line art boundaries to prevent leaking!
    """
    conn = get_db_connection()
    page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    
    if not page or not page["processed_path"]:
        raise HTTPException(status_code=400, detail="Page must be processed before editing.")
        
    proc_path = Path(page["processed_path"])
    orig_path = Path(page["original_path"])
    
    colored_img = cv2.imread(str(proc_path))
    orig_img = cv2.imread(str(orig_path))
    
    if colored_img is None or orig_img is None:
        raise HTTPException(status_code=404, detail="Page image files missing on disk.")
        
    h, w = colored_img.shape[:2]
    x, y = int(action.x), int(action.y)
    
    if x < 0 or x >= w or y < 0 or y >= h:
        raise HTTPException(status_code=400, detail="Coordinates out of bounds.")
        
    fill_bgr = hex_to_bgr(action.color_hex)
    
    # Extract line art mask as strict boundary
    orig_gray = cv2.cvtColor(orig_img, cv2.COLOR_BGR2GRAY)
    _, ink_boundary = cv2.threshold(orig_gray, 75, 255, cv2.THRESH_BINARY_INV)
    
    # OpenCV floodFill requires a mask with 2 extra pixels in width and height
    mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    mask[1:h+1, 1:w+1] = np.where(ink_boundary > 0, 1, 0).astype(np.uint8)
    
    # Perform flood fill on the colored image bounded by line art
    flood_flags = 4 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY
    temp_fill_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    
    cv2.floodFill(
        colored_img.copy(), 
        mask, 
        (x, y), 
        fill_bgr, 
        (action.tolerance, action.tolerance, action.tolerance),
        (action.tolerance, action.tolerance, action.tolerance),
        cv2.FLOODFILL_FIXED_RANGE
    )
    
    # Apply new color where flood fill reached (excluding ink boundary)
    filled_region = (mask[1:h+1, 1:w+1] == 255)
    colored_img[filled_region] = fill_bgr
    
    # Re-blend with line art to keep crisp outlines 100% intact
    blended = blend_color_with_line_art(colored_img, orig_img)
    
    # Overwrite processed image
    cv2.imwrite(str(proc_path), blended)
    
    return {
        "status": "success",
        "processed_url": f"/api/pages/{page_id}/processed?t={np.random.randint(100000)}",
        "pixels_filled": int(np.sum(filled_region))
    }

@router.post("/page/{page_id}/save-layer")
def save_studio_layer(page_id: str, data: ManualCorrectionSave):
    """Saves user manual brush strokes or canvas edits back into the master colored page."""
    if not data.layer_base64_png:
        return {"status": "noop"}
        
    conn = get_db_connection()
    page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    
    if not page or not page["processed_path"]:
        raise HTTPException(status_code=400, detail="Page has not been processed.")
        
    try:
        # Decode base64 image layer
        header, encoded = data.layer_base64_png.split(",", 1) if "," in data.layer_base64_png else ("", data.layer_base64_png)
        img_bytes = base64.b64decode(encoded)
        layer_np = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
        
        proc_path = Path(page["processed_path"])
        orig_img = cv2.imread(page["original_path"])
        curr_proc = cv2.imread(str(proc_path))
        
        if layer_np is not None and layer_np.shape[2] == 4:
            # Composite RGBA layer over colored image
            alpha = (layer_np[:, :, 3].astype(np.float32) / 255.0)[:, :, np.newaxis]
            brush_bgr = layer_np[:, :, :3]
            
            merged = (brush_bgr.astype(np.float32) * alpha + curr_proc.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)
            # Re-blend line art
            final_art = blend_color_with_line_art(merged, orig_img)
            cv2.imwrite(str(proc_path), final_art)
            
        return {"status": "success", "processed_url": f"/api/pages/{page_id}/processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/page/{page_id}/reprocess")
async def reprocess_single_page(page_id: str):
    """Triggers instant re-colorization of a single page."""
    conn = get_db_connection()
    page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    if not page:
        conn.close()
        raise HTTPException(status_code=404, detail="Page not found")
        
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (page["project_id"],)).fetchone()
    conn.close()
    
    await batch_queue.process_single_page(page["project_id"], dict(page), project["coloring_style"])
    return {"status": "success", "page_id": page_id}

@router.get("/page/{page_id}/comparison")
def get_before_after_comparison(page_id: str):
    """Returns side-by-side comparison image."""
    try:
        comp_path = ExportService.generate_before_after_comparison(page_id)
        return FileResponse(str(comp_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
