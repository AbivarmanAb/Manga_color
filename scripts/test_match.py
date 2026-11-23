import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2, sqlite3
from backend.app.ai.character.detector import detect_character_regions
from backend.app.ai.character.memory import CharacterColorMemorySystem

conn = sqlite3.connect('storage/manga_studio.db')
page_id = conn.execute('SELECT id FROM pages WHERE project_id=? AND page_number=8', ('proj_f0afce218b',)).fetchone()[0]
conn.close()

img = cv2.imread('storage/projects/proj_f0afce218b/original/p0008_page_0008_fzImg0.jpg')
dets = detect_character_regions(img)
for i, d in enumerate(dets):
    m = CharacterColorMemorySystem.match_or_create_character('proj_f0afce218b', page_id, 8, d, 'vibrant_anime')
    print(f"Det {i}: Name={m.get('name')}, Hair={m.get('hair_color')}, Skin={m.get('skin_color')}, Outfit={m.get('primary_outfit_color')}, FaceBox={d.get('face_bbox')}")
