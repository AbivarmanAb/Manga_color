from fastapi import APIRouter
from ..core.hardware import get_hardware_telemetry, clear_vram

router = APIRouter(prefix="/api/hardware", tags=["Hardware"])

@router.get("/telemetry")
def read_telemetry():
    """Returns real-time GPU (RTX 5060), VRAM, RAM, and CPU telemetry."""
    return get_hardware_telemetry()

@router.post("/clear-vram")
def trigger_clear_vram():
    """Forces PyTorch and driver VRAM garbage collection."""
    clear_vram()
    return {"status": "ok", "message": "VRAM cache cleared successfully."}
