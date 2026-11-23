import sqlite3, json, cv2
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.ai.character.detector import detect_character_regions

# Page 8: Ivankov is dets[0]
img8 = cv2.imread('storage/projects/proj_f0afce218b/original/p0008_page_0008_fzImg0.jpg')
dets8 = detect_character_regions(img8)
iva_sig = dets8[0]['signature']

# Page 8: Sanji is dets[3] [97, 1104, 291, 132] or dets[2] [808, 0, 146, 151]
sanji_sig = dets8[2]['signature']

# Page 1: Luffy
img1 = cv2.imread('storage/projects/proj_f0afce218b/original/p0001_page_0001_fzImg0.jpg')
dets1 = detect_character_regions(img1)
luffy_sig = dets1[0]['signature'] if dets1 else None

conn = sqlite3.connect('storage/manga_studio.db')
conn.execute('UPDATE characters SET features_json=?, updated_at=datetime("now") WHERE id=?', 
             (json.dumps(iva_sig), 'char_proj_f0afce218b_002'))
conn.execute('UPDATE characters SET features_json=?, updated_at=datetime("now") WHERE id=?', 
             (json.dumps(sanji_sig), 'char_proj_f0afce218b_001'))
if luffy_sig:
    conn.execute('UPDATE characters SET features_json=?, updated_at=datetime("now") WHERE id=?', 
                 (json.dumps(luffy_sig), 'char_proj_f0afce218b_003'))
conn.commit()
conn.close()
print("Updated canonical character signatures for Sanji, Ivankov, and Luffy!")
