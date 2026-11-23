import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
PROJECTS_DIR = STORAGE_DIR / "projects"
MODELS_DIR = BASE_DIR / "models"
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
DB_PATH = STORAGE_DIR / "manga_studio.db"

# Ensure essential directories exist
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "Manga AI Colorization Studio"
    version: str = "1.0.0"
    base_dir: Path = BASE_DIR
    storage_dir: Path = STORAGE_DIR
    projects_dir: Path = PROJECTS_DIR
    models_dir: Path = MODELS_DIR
    checkpoints_dir: Path = CHECKPOINTS_DIR
    db_path: Path = DB_PATH
    
    # Hardware defaults for RTX 5060 & 16GB RAM
    device_preference: str = "cuda"
    max_image_dimension: int = 2400
    tiled_threshold: int = 1800
    max_batch_vram_mb: int = 7000
    default_style: str = "vibrant_anime"

settings = Settings()
