import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config import settings

def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a connection to SQLite with WAL enabled and row dictionary factory."""
    conn = sqlite3.connect(str(settings.db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        manga_title TEXT NOT NULL,
        chapter_num TEXT NOT NULL,
        description TEXT,
        mode TEXT NOT NULL DEFAULT 'combined',
        coloring_style TEXT NOT NULL DEFAULT 'vibrant_anime',
        output_resolution TEXT NOT NULL DEFAULT 'original',
        status TEXT NOT NULL DEFAULT 'created',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS pages (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original_path TEXT NOT NULL,
        preview_path TEXT,
        processed_path TEXT,
        lineart_path TEXT,
        mask_path TEXT,
        width INTEGER NOT NULL,
        height INTEGER NOT NULL,
        is_colored_preview BOOLEAN NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        stage TEXT NOT NULL DEFAULT 'Uploaded',
        progress INTEGER NOT NULL DEFAULT 0,
        error_message TEXT,
        quality_report_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS characters (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        name TEXT NOT NULL,
        hair_color TEXT NOT NULL DEFAULT '#2A2A2A',
        skin_color TEXT NOT NULL DEFAULT '#FFE0BD',
        eye_color TEXT NOT NULL DEFAULT '#4A2E12',
        primary_outfit_color TEXT NOT NULL DEFAULT '#1E40AF',
        secondary_outfit_color TEXT NOT NULL DEFAULT '#E5E7EB',
        accent_color TEXT DEFAULT '#DC2626',
        confidence_score REAL NOT NULL DEFAULT 0.85,
        first_appearance_page INTEGER NOT NULL DEFAULT 1,
        last_appearance_page INTEGER NOT NULL DEFAULT 1,
        avatar_path TEXT,
        is_locked BOOLEAN NOT NULL DEFAULT 0,
        features_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS character_appearances (
        id TEXT PRIMARY KEY,
        character_id TEXT NOT NULL,
        page_id TEXT NOT NULL,
        panel_index INTEGER NOT NULL DEFAULT 0,
        bbox_json TEXT NOT NULL,
        confidence REAL NOT NULL DEFAULT 0.8,
        FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
        FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reference_images (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        character_id TEXT,
        file_path TEXT NOT NULL,
        extracted_colors_json TEXT,
        source_type TEXT NOT NULL DEFAULT 'preview_page',
        created_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS manual_corrections (
        id TEXT PRIMARY KEY,
        page_id TEXT NOT NULL,
        layer_png_path TEXT NOT NULL,
        strokes_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS export_records (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        export_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        resolution_scale TEXT NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_pages_project ON pages(project_id, page_number);
    CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
    CREATE INDEX IF NOT EXISTS idx_appearances_page ON character_appearances(page_id);
    """)

    conn.commit()
    conn.close()

# Auto-initialize database on import
init_db()
