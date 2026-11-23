from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from ..database.connection import get_db_connection

router = APIRouter(prefix="/api/pages", tags=["Pages"])

@router.get("/{page_id}")
def get_page_details(page_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Page not found")
    d = dict(row)
    d["original_url"] = f"/api/pages/{d['id']}/original"
    d["processed_url"] = f"/api/pages/{d['id']}/processed" if d.get("processed_path") else None
    return d

@router.get("/{page_id}/original")
def get_page_original_image(page_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT original_path FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    if not row or not row["original_path"] or not Path(row["original_path"]).exists():
        raise HTTPException(status_code=404, detail="Original image not found")
    return FileResponse(row["original_path"])

@router.get("/{page_id}/processed")
def get_page_processed_image(page_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT processed_path, original_path FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Page not found")
        
    target_path = row["processed_path"] if row["processed_path"] and Path(row["processed_path"]).exists() else row["original_path"]
    if not target_path or not Path(target_path).exists():
        raise HTTPException(status_code=404, detail="Page image file not found")
    return FileResponse(target_path)

@router.get("/{page_id}/preview")
def get_page_preview_image(page_id: str):
    """Serves preview thumbnail: uses colored processed image if available, else original."""
    conn = get_db_connection()
    row = conn.execute("SELECT processed_path, original_path FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Page not found")
        
    target_path = row["processed_path"] if row["processed_path"] and Path(row["processed_path"]).exists() else row["original_path"]
    if not target_path or not Path(target_path).exists():
        raise HTTPException(status_code=404, detail="Preview image file not found")
    return FileResponse(target_path)

@router.get("/{page_id}/download")
def download_single_page(page_id: str):
    """Triggers direct browser download for this specific colorized page."""
    conn = get_db_connection()
    row = conn.execute("SELECT processed_path, original_path, filename, page_number FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Page not found")
        
    target_path = row["processed_path"] if row["processed_path"] and Path(row["processed_path"]).exists() else row["original_path"]
    if not target_path or not Path(target_path).exists():
        raise HTTPException(status_code=404, detail="Image file not found")
        
    ext = Path(target_path).suffix or ".png"
    download_name = f"page_{row['page_number']:04d}_color{ext}"
    return FileResponse(
        target_path, 
        filename=download_name, 
        media_type="image/png"
    )

@router.delete("/{page_id}")
def delete_page(page_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT original_path, processed_path FROM pages WHERE id = ?", (page_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Remove files if needed
    for p_str in [row["original_path"], row["processed_path"]]:
        if p_str and Path(p_str).exists():
            try:
                Path(p_str).unlink()
            except Exception:
                pass
                
    conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Page deleted."}
