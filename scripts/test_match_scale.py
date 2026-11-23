import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2, sqlite3, json, numpy as np
from backend.app.ai.character.detector import detect_character_regions, calculate_similarity

conn = sqlite3.connect('storage/manga_studio.db')
conn.row_factory = sqlite3.Row
existing_chars = conn.execute("SELECT * FROM characters WHERE project_id = ?", ('proj_f0afce218b',)).fetchall()
conn.close()

img = cv2.imread('storage/projects/proj_f0afce218b/original/p0008_page_0008_fzImg0.jpg')
dets = detect_character_regions(img)

# Characteristic reference areas:
ref_areas = {
    'char_proj_f0afce218b_001': 22000.0,  # Sanji
    'char_proj_f0afce218b_002': 140000.0, # Ivankov (huge afro/face)
    'char_proj_f0afce218b_003': 25000.0,  # Luffy
}

for i, det in enumerate(dets):
    t_box = det.get("face_bbox") or [0, 0, 150, 150]
    t_area = float(t_box[2] * t_box[3])
    target_sig = np.array(det.get("signature", []))
    
    best_match = None
    best_similarity = 0.0
    
    for char_row in existing_chars:
        feat_json = char_row["features_json"]
        if feat_json:
            ref_sig = np.array(json.loads(feat_json))
            sim = calculate_similarity(target_sig, ref_sig)
            ref_a = ref_areas.get(char_row["id"], 30000.0)
            scale_pen = min(0.25, 0.12 * abs(np.log((t_area + 1e-3) / (ref_a + 1e-3))))
            adj_sim = sim - scale_pen
            
            if adj_sim > best_similarity:
                best_similarity = adj_sim
                best_match = char_row
                
    name = best_match["name"] if best_match else "None"
    hair = best_match["hair_color"] if best_match else "None"
    print(f"Det {i}: Name={name}, Hair={hair}, AdjSim={best_similarity:.3f}, FaceBox={t_box}")
