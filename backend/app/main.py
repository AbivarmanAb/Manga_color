from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .database.connection import init_db
from .core.hardware import get_hardware_telemetry
from .ai.adapter import engine_router
from .api import hardware, projects, pages, characters, studio, queue, export

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Professional Local-First AI Manga Colorization Studio with Character Color Memory"
)

# Enable CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(hardware.router)
app.include_router(projects.router)
app.include_router(pages.router)
app.include_router(characters.router)
app.include_router(studio.router)
app.include_router(queue.router)
app.include_router(export.router)

@app.get("/api/models")
def get_models():
    """Lists modular AI colorization engines and active selection."""
    return engine_router.list_models()

@app.post("/api/models/select/{model_id}")
def select_model(model_id: str):
    """Switches the active colorization engine."""
    success = engine_router.set_active_adapter(model_id)
    return {"status": "success" if success else "error", "active_model": engine_router.active_adapter_id}

@app.get("/api/health")
def health_check():
    telemetry = get_hardware_telemetry()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "hardware": telemetry
    }

# Mount Frontend static distribution at the very end so API routes have absolute priority
frontend_dist = settings.base_dir / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

@app.on_event("startup")
def on_startup():
    init_db()
    print("==================================================")
    print("   MANGA AI COLORIZATION STUDIO BACKEND READY    ")
    print("==================================================")
    telemetry = get_hardware_telemetry()
    gpu = telemetry.get("gpu", {})
    if gpu.get("available"):
        print(f"  GPU: {gpu.get('device_name')} ({gpu.get('total_vram_mb')} MB VRAM)")
    else:
        print("  Running on CPU Fallback")
    print("==================================================")
