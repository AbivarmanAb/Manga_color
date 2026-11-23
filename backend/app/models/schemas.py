from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    title: str
    manga_title: str
    chapter_num: str = "1"
    description: Optional[str] = ""
    mode: str = "combined"  # new_manga, preview_reference, character_reference, combined
    coloring_style: str = "vibrant_anime"
    output_resolution: str = "original"

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    manga_title: Optional[str] = None
    chapter_num: Optional[str] = None
    description: Optional[str] = None
    mode: Optional[str] = None
    coloring_style: Optional[str] = None
    output_resolution: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    title: str
    manga_title: str
    chapter_num: str
    description: Optional[str] = None
    mode: str
    coloring_style: str
    output_resolution: str
    status: str
    created_at: str
    updated_at: str
    page_count: Optional[int] = 0
    completed_page_count: Optional[int] = 0
    character_count: Optional[int] = 0

# --- Page Schemas ---
class PageResponse(BaseModel):
    id: str
    project_id: str
    page_number: int
    filename: str
    original_url: str
    preview_url: Optional[str] = None
    processed_url: Optional[str] = None
    width: int
    height: int
    is_colored_preview: bool
    status: str
    stage: str
    progress: int
    error_message: Optional[str] = None
    quality_report: Optional[Dict[str, Any]] = None

# --- Character Schemas ---
class CharacterColorPalette(BaseModel):
    hair_color: str = "#2A2A2A"
    skin_color: str = "#FFE0BD"
    eye_color: str = "#4A2E12"
    primary_outfit_color: str = "#1E40AF"
    secondary_outfit_color: str = "#E5E7EB"
    accent_color: Optional[str] = "#DC2626"

class CharacterCreate(BaseModel):
    name: str
    hair_color: str = "#2A2A2A"
    skin_color: str = "#FFE0BD"
    eye_color: str = "#4A2E12"
    primary_outfit_color: str = "#1E40AF"
    secondary_outfit_color: str = "#E5E7EB"
    accent_color: Optional[str] = "#DC2626"
    confidence_score: float = 0.85
    first_appearance_page: int = 1
    last_appearance_page: int = 1
    is_locked: bool = False

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    hair_color: Optional[str] = None
    skin_color: Optional[str] = None
    eye_color: Optional[str] = None
    primary_outfit_color: Optional[str] = None
    secondary_outfit_color: Optional[str] = None
    accent_color: Optional[str] = None
    is_locked: Optional[bool] = None

class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    hair_color: str
    skin_color: str
    eye_color: str
    primary_outfit_color: str
    secondary_outfit_color: str
    accent_color: Optional[str] = None
    confidence_score: float
    first_appearance_page: int
    last_appearance_page: int
    avatar_url: Optional[str] = None
    is_locked: bool
    appearances_count: Optional[int] = 0

# --- Reference Schemas ---
class ReferenceResponse(BaseModel):
    id: str
    project_id: str
    character_id: Optional[str] = None
    image_url: str
    extracted_colors: List[str] = []
    source_type: str
    created_at: str

# --- Studio & Correction Schemas ---
class ManualCorrectionSave(BaseModel):
    strokes_json: Optional[str] = None
    layer_base64_png: Optional[str] = None

class StudioColorAction(BaseModel):
    action_type: str  # 'flood_fill', 'recolor_region', 'apply_character_swatch'
    x: int
    y: int
    color_hex: str
    tolerance: int = 32
    target_character_id: Optional[str] = None

# --- Export Schemas ---
class ExportRequest(BaseModel):
    export_type: str = "pdf"  # pdf, zip, png_single, comparison
    resolution_scale: str = "original"  # original, 2x, 4x
    page_ids: Optional[List[str]] = None

class ExportResponse(BaseModel):
    id: str
    project_id: str
    export_type: str
    download_url: str
    file_size_bytes: int
    created_at: str
