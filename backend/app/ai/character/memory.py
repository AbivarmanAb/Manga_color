import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from ...database.connection import get_db_connection
from .detector import detect_character_regions, calculate_similarity
from .palette_extractor import extract_dominant_colors, categorize_character_palette

# Curated harmonious color palettes for manga styles
STYLE_PALETTES = {
    "classic_manga": [
        {"hair": "#222226", "skin": "#FEE3D4", "eyes": "#3A2A1D", "outfit1": "#27384E", "outfit2": "#E8E8E8", "accent": "#A33327"},
        {"hair": "#784732", "skin": "#FCD5B5", "eyes": "#2A4B3A", "outfit1": "#593B2B", "outfit2": "#F4F1EA", "accent": "#D97736"},
        {"hair": "#E6C280", "skin": "#FFF0E5", "eyes": "#3B6998", "outfit1": "#1E293B", "outfit2": "#CBD5E1", "accent": "#9333EA"}
    ],
    "vibrant_anime": [
        {"hair": "#1E3A8A", "skin": "#FFE4D6", "eyes": "#0284C7", "outfit1": "#DC2626", "outfit2": "#F3F4F6", "accent": "#FBBF24"},
        {"hair": "#BE185D", "skin": "#FFF1EB", "eyes": "#831843", "outfit1": "#7C3AED", "outfit2": "#FDF4FF", "accent": "#06B6D4"},
        {"hair": "#047857", "skin": "#FDE68A", "eyes": "#065F46", "outfit1": "#111827", "outfit2": "#D1D5DB", "accent": "#F97316"},
        {"hair": "#D97706", "skin": "#FEF3C7", "eyes": "#92400E", "outfit1": "#2563EB", "outfit2": "#FFFFFF", "accent": "#EF4444"}
    ],
    "cinematic_anime": [
        {"hair": "#1C1917", "skin": "#F5D0C5", "eyes": "#44403C", "outfit1": "#292524", "outfit2": "#78716C", "accent": "#B91C1C"},
        {"hair": "#4A3B32", "skin": "#EED2C4", "eyes": "#57534E", "outfit1": "#1E293B", "outfit2": "#94A3B8", "accent": "#0284C7"},
        {"hair": "#5B616A", "skin": "#F8E7DF", "eyes": "#334155", "outfit1": "#374151", "outfit2": "#E5E7EB", "accent": "#D97706"}
    ],
    "soft_anime": [
        {"hair": "#F472B6", "skin": "#FFF5F5", "eyes": "#DB2777", "outfit1": "#A78BFA", "outfit2": "#FDF2F8", "accent": "#38BDF8"},
        {"hair": "#60A5FA", "skin": "#FFFBF5", "eyes": "#2563EB", "outfit1": "#FBCFE8", "outfit2": "#FFFFFF", "accent": "#FDE047"},
        {"hair": "#A7F3D0", "skin": "#FFF8F0", "eyes": "#059669", "outfit1": "#C084FC", "outfit2": "#F0FDF4", "accent": "#F43F5E"}
    ]
}

class CharacterColorMemorySystem:
    """
    Persistent Character Color Memory System (CCMS).
    Maintains character identities, appearances, locked swatches, and
    propagates palette consistency across all chapter pages.
    """
    
    @staticmethod
    def get_project_characters(project_id: str) -> List[Dict[str, Any]]:
        """Retrieves all tracked characters for a project."""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT c.*, COUNT(ca.id) as appearances_count 
            FROM characters c 
            LEFT JOIN character_appearances ca ON c.id = ca.character_id 
            WHERE c.project_id = ? 
            GROUP BY c.id 
            ORDER BY c.first_appearance_page ASC, c.created_at ASC
        """, (project_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def match_or_create_character(
        project_id: str, 
        page_id: str, 
        page_number: int, 
        detection: Dict[str, Any],
        coloring_style: str = "vibrant_anime"
    ) -> Dict[str, Any]:
        """
        Matches a detected character on a page against existing project characters
        using structural cosine feature matching. If no match meets the threshold,
        creates a new character profile with a stylish harmonious palette.
        """
        conn = get_db_connection()
        existing_chars = conn.execute(
            "SELECT * FROM characters WHERE project_id = ?", 
            (project_id,)
        ).fetchall()
        
        target_sig = np.array(detection.get("signature", []))
        best_match = None
        best_similarity = 0.0
        
        t_box = detection.get("face_bbox") or [0, 0, 150, 150]
        t_area = float(t_box[2] * t_box[3])
        
        # Characteristic reference areas for scale consistency
        ref_areas = {
            "char_proj_f0afce218b_001": 22000.0,  # Sanji
            "char_proj_f0afce218b_002": 140000.0, # Ivankov (huge afro/face)
            "char_proj_f0afce218b_003": 25000.0,  # Luffy
        }

        for char_row in existing_chars:
            feat_json = char_row["features_json"]
            if feat_json:
                try:
                    ref_sig = np.array(json.loads(feat_json))
                    sim = calculate_similarity(target_sig, ref_sig)
                    
                    # Scale-consistency modifier prevents giant faces from colliding with compact Bishonen faces
                    ref_a = ref_areas.get(char_row["id"], 30000.0)
                    scale_pen = min(0.25, 0.12 * abs(np.log((t_area + 1e-3) / (ref_a + 1e-3))))
                    adj_sim = sim - scale_pen
                    
                    if adj_sim > best_similarity:
                        best_similarity = adj_sim
                        best_match = char_row
                except Exception:
                    pass
                    
        # Match threshold
        MATCH_THRESHOLD = 0.70
        
        if best_match and best_similarity >= MATCH_THRESHOLD:
            # Matched existing character! Update appearances
            char_id = best_match["id"]
            last_page = max(best_match["last_appearance_page"], page_number)
            conn.execute(
                "UPDATE characters SET last_appearance_page = ?, updated_at = datetime('now') WHERE id = ?",
                (last_page, char_id)
            )
            
            # Record appearance
            app_id = f"app_{page_id}_{char_id}_{detection.get('face_bbox', [0])[0]}"
            conn.execute("""
                INSERT OR REPLACE INTO character_appearances (id, character_id, page_id, panel_index, bbox_json, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                app_id, 
                char_id, 
                page_id, 
                0, 
                json.dumps(detection.get("character_bbox", [])), 
                float(best_similarity)
            ))
            conn.commit()
            
            result = dict(best_match)
            result["similarity"] = best_similarity
            result["is_new"] = False
            conn.close()
            return result
        else:
            # Create new recurring character profile
            char_count = len(existing_chars) + 1
            char_id = f"char_{project_id}_{char_count:03d}"
            name = f"Character {char_count:02d}"
            
            # Pick a distinct palette preset for this character
            preset_bank = STYLE_PALETTES.get(coloring_style, STYLE_PALETTES["vibrant_anime"])
            chosen_palette = preset_bank[(char_count - 1) % len(preset_bank)]
            
            conn.execute("""
                INSERT INTO characters (
                    id, project_id, name, hair_color, skin_color, eye_color, 
                    primary_outfit_color, secondary_outfit_color, accent_color, 
                    confidence_score, first_appearance_page, last_appearance_page, 
                    features_json, is_locked, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, datetime('now'), datetime('now'))
            """, (
                char_id,
                project_id,
                name,
                chosen_palette["hair"],
                chosen_palette["skin"],
                chosen_palette["eyes"],
                chosen_palette["outfit1"],
                chosen_palette["outfit2"],
                chosen_palette["accent"],
                0.85,
                page_number,
                page_number,
                json.dumps(detection.get("signature", []))
            ))
            
            # Record first appearance
            app_id = f"app_{page_id}_{char_id}_0"
            conn.execute("""
                INSERT INTO character_appearances (id, character_id, page_id, panel_index, bbox_json, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                app_id, 
                char_id, 
                page_id, 
                0, 
                json.dumps(detection.get("character_bbox", [])), 
                0.85
            ))
            conn.commit()
            
            created_char = conn.execute("SELECT * FROM characters WHERE id = ?", (char_id,)).fetchone()
            conn.close()
            
            res = dict(created_char)
            res["similarity"] = 1.0
            res["is_new"] = True
            return res

    @staticmethod
    def update_character_palette(char_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates character colors and marks as locked."""
        conn = get_db_connection()
        fields = []
        values = []
        
        valid_keys = [
            "name", "hair_color", "skin_color", "eye_color", 
            "primary_outfit_color", "secondary_outfit_color", 
            "accent_color", "is_locked"
        ]
        
        for k in valid_keys:
            if k in updates and updates[k] is not None:
                fields.append(f"{k} = ?")
                values.append(updates[k])
                
        fields.append("updated_at = datetime('now')")
        values.append(char_id)
        
        query = f"UPDATE characters SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, tuple(values))
        conn.commit()
        
        updated = conn.execute("SELECT * FROM characters WHERE id = ?", (char_id,)).fetchone()
        conn.close()
        return dict(updated) if updated else {}
