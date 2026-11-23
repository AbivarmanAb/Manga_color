from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..services.batch_queue import batch_queue
from ..database.connection import get_db_connection

router = APIRouter(prefix="/api/queue", tags=["Processing Queue"])

@router.get("/status")
async def get_queue_status():
    return {
        "is_running": batch_queue.is_running,
        "is_paused": batch_queue.is_paused,
        "current_project_id": batch_queue.current_project_id,
        "current_page_id": batch_queue.current_page_id
    }

@router.post("/{project_id}/start")
async def start_queue(project_id: str):
    batch_queue.start_project_processing(project_id)
    return {"status": "started", "project_id": project_id}

@router.post("/pause")
async def pause_queue():
    batch_queue.pause_processing()
    return {"status": "paused"}

@router.post("/resume")
async def resume_queue():
    batch_queue.resume_processing()
    return {"status": "resumed"}

@router.post("/stop")
async def stop_queue():
    batch_queue.stop_processing()
    return {"status": "stopped"}

@router.post("/page/{page_id}/retry")
async def retry_page(page_id: str):
    conn = get_db_connection()
    conn.execute(
        "UPDATE pages SET status = 'retry', stage = 'Queued for Retry', error_message = NULL WHERE id = ?", 
        (page_id,)
    )
    conn.commit()
    row = conn.execute("SELECT project_id FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    
    if row and not batch_queue.is_running:
        batch_queue.start_project_processing(row["project_id"])
        
    return {"status": "queued_retry", "page_id": page_id}
