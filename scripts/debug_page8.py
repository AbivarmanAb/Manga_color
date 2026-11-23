import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2, sqlite3
from backend.app.ai.character.detector import detect_character_regions
from backend.app.ai.character.memory import CharacterColorMemorySystem
from backend.app.ai.adapter import engine_router

conn = sqlite3.connect('storage/manga_studio.db')
page_id = conn.execute('SELECT id FROM pages WHERE project_id=? AND page_number=8', ('proj_f0afce218b',)).fetchone()[0]
conn.close()

img = cv2.imread('storage/projects/proj_f0afce218b/original/p0008_page_0008_fzImg0.jpg')
dets = detect_character_regions(img)
matched = []
for d in dets:
    m = CharacterColorMemorySystem.match_or_create_character('proj_f0afce218b', page_id, 8, d, 'vibrant_anime')
    m['character_bbox'] = d.get('character_bbox')
    m['face_bbox'] = d.get('face_bbox')
    matched.append(m)

colored, rep = engine_router.colorize_page(img, matched, 'vibrant_anime')
cv2.imwrite('storage/test_debug_p8.jpg', colored, [cv2.IMWRITE_JPEG_QUALITY, 96])
print("Saved debug page 8:", rep)
