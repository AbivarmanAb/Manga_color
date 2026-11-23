import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def create_screentone_pattern(h: int, w: int, spacing: int = 6, radius: int = 1) -> np.ndarray:
    """Generates authentic manga halftone screentone dot matrix."""
    tone = np.full((h, w), 255, dtype=np.uint8)
    for y in range(0, h, spacing):
        for x in range(0, w, spacing):
            cv2.circle(tone, (x, y), radius, 120, -1)
    return tone

def draw_manga_face(img: np.ndarray, center_x: int, center_y: int, scale: float = 1.0, is_colored: bool = False, hair_color=(40, 40, 40)):
    """Draws a classic stylized anime/manga character face, hair, and outlines."""
    # Jawline / Chin
    pts_jaw = np.array([
        [center_x - int(55 * scale), center_y - int(10 * scale)],
        [center_x - int(45 * scale), center_y + int(35 * scale)],
        [center_x, center_y + int(65 * scale)], # Chin tip
        [center_x + int(45 * scale), center_y + int(35 * scale)],
        [center_x + int(55 * scale), center_y - int(10 * scale)],
    ], np.int32)
    
    if is_colored:
        # Fill skin tone
        skin_bgr = (195, 225, 255) # Light peach in BGR
        cv2.fillPoly(img, [pts_jaw], skin_bgr)
    else:
        cv2.fillPoly(img, [pts_jaw], (255, 255, 255))
        
    cv2.polylines(img, [pts_jaw], False, (15, 15, 15), max(2, int(2.5 * scale)))
    
    # Large Anime Eyes
    eye_y = center_y + int(5 * scale)
    left_eye_x = center_x - int(25 * scale)
    right_eye_x = center_x + int(25 * scale)
    
    for ex in [left_eye_x, right_eye_x]:
        # Upper eyelid arc
        cv2.ellipse(img, (ex, eye_y), (int(14 * scale), int(16 * scale)), 0, 190, 350, (15, 15, 15), max(2, int(3 * scale)))
        # Pupil
        if is_colored:
            cv2.circle(img, (ex, eye_y + int(2 * scale)), int(7 * scale), (200, 100, 30), -1) # Blue iris
        cv2.circle(img, (ex, eye_y + int(2 * scale)), int(4 * scale), (15, 15, 15), -1) # Pupil
        cv2.circle(img, (ex + int(3 * scale), eye_y - int(2 * scale)), int(2 * scale), (255, 255, 255), -1) # Catchlight
        # Lower lash
        cv2.line(img, (ex - int(7 * scale), eye_y + int(10 * scale)), (ex + int(7 * scale), eye_y + int(10 * scale)), (30, 30, 30), max(1, int(1.5 * scale)))

    # Eyebrows
    cv2.line(img, (left_eye_x - int(12 * scale), eye_y - int(16 * scale)), (left_eye_x + int(12 * scale), eye_y - int(12 * scale)), (15, 15, 15), max(2, int(2.5 * scale)))
    cv2.line(img, (right_eye_x - int(12 * scale), eye_y - int(12 * scale)), (right_eye_x + int(12 * scale), eye_y - int(16 * scale)), (15, 15, 15), max(2, int(2.5 * scale)))
    
    # Nose
    cv2.line(img, (center_x, center_y + int(25 * scale)), (center_x - int(3 * scale), center_y + int(32 * scale)), (15, 15, 15), max(1, int(2 * scale)))
    
    # Mouth
    cv2.ellipse(img, (center_x, center_y + int(46 * scale)), (int(10 * scale), int(4 * scale)), 0, 10, 170, (15, 15, 15), max(2, int(2 * scale)))
    
    # Spiky Anime Hair
    hair_spikes = [
        [center_x - int(65 * scale), center_y - int(5 * scale)],
        [center_x - int(80 * scale), center_y - int(35 * scale)],
        [center_x - int(55 * scale), center_y - int(45 * scale)],
        [center_x - int(65 * scale), center_y - int(75 * scale)],
        [center_x - int(30 * scale), center_y - int(65 * scale)],
        [center_x - int(25 * scale), center_y - int(95 * scale)], # Top spike
        [center_x, center_y - int(75 * scale)],
        [center_x + int(25 * scale), center_y - int(90 * scale)], # Top right spike
        [center_x + int(35 * scale), center_y - int(65 * scale)],
        [center_x + int(65 * scale), center_y - int(70 * scale)],
        [center_x + int(55 * scale), center_y - int(40 * scale)],
        [center_x + int(75 * scale), center_y - int(30 * scale)],
        [center_x + int(60 * scale), center_y - int(5 * scale)],
        # Forehead bangs
        [center_x + int(35 * scale), center_y - int(18 * scale)],
        [center_x + int(20 * scale), center_y - int(3 * scale)],
        [center_x, center_y - int(18 * scale)],
        [center_x - int(20 * scale), center_y - int(5 * scale)],
        [center_x - int(35 * scale), center_y - int(18 * scale)],
    ]
    pts_hair = np.array(hair_spikes, np.int32)
    
    if is_colored:
        cv2.fillPoly(img, [pts_hair], hair_color)
    else:
        cv2.fillPoly(img, [pts_hair], (240, 240, 240))
        
    cv2.polylines(img, [pts_hair], True, (15, 15, 15), max(2, int(2.5 * scale)))
    
    # Collar / Shoulders
    collar_pts = np.array([
        [center_x - int(40 * scale), center_y + int(60 * scale)],
        [center_x - int(80 * scale), center_y + int(130 * scale)],
        [center_x + int(80 * scale), center_y + int(130 * scale)],
        [center_x + int(40 * scale), center_y + int(60 * scale)],
    ], np.int32)
    
    if is_colored:
        cv2.fillPoly(img, [collar_pts], (160, 45, 30)) # Crimson jacket
    else:
        cv2.fillPoly(img, [collar_pts], (220, 220, 220))
        
    cv2.polylines(img, [collar_pts], True, (15, 15, 15), max(2, int(2.5 * scale)))

def draw_speech_bubble(img: np.ndarray, x: int, y: int, w: int, h: int, text: str):
    """Draws an authentic manga speech bubble with clear dialog lettering."""
    # White ellipse bubble
    center = (x + w // 2, y + h // 2)
    axes = (w // 2, h // 2)
    cv2.ellipse(img, center, axes, 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(img, center, axes, 0, 0, 360, (15, 15, 15), 3)
    
    # Pointer tail
    tail_pts = np.array([
        [center[0] - 15, y + h - 4],
        [center[0] - 35, y + h + 28],
        [center[0] + 5, y + h - 4]
    ], np.int32)
    cv2.fillPoly(img, [tail_pts], (255, 255, 255))
    cv2.polylines(img, [tail_pts], False, (15, 15, 15), 3)
    
    # Clean up tail interior
    cv2.line(img, (center[0] - 14, y + h - 3), (center[0] + 4, y + h - 3), (255, 255, 255), 5)
    
    # Text lettering
    lines = text.split("\n")
    start_y = center[1] - (len(lines) * 11)
    for i, line in enumerate(lines):
        text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)[0]
        text_x = center[0] - text_size[0] // 2
        text_y = start_y + (i * 24)
        cv2.putText(img, line, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 0.45, (15, 15, 15), 1, cv2.LINE_AA)

def generate_manga_page(page_num: int, is_colored: bool = False) -> np.ndarray:
    """Generates a complete multi-panel manga page."""
    W, H = 800, 1150
    page = np.full((H, W, 3), 255, dtype=np.uint8)
    
    # Outer page margin
    margin = 35
    
    # Panel layout: Top panel (wide), Bottom left panel, Bottom right panel
    top_panel = (margin, margin, W - 2*margin, 460)
    bot_left = (margin, margin + 480, (W - 2*margin) // 2 - 10, 560)
    bot_right = (margin + (W - 2*margin) // 2 + 10, margin + 480, (W - 2*margin) // 2 - 10, 560)
    
    # Draw background screentones in top panel
    screentone = create_screentone_pattern(top_panel[3], top_panel[2], spacing=8, radius=1)
    page[top_panel[1]:top_panel[1]+top_panel[3], top_panel[0]:top_panel[0]+top_panel[2]] = cv2.cvtColor(screentone, cv2.COLOR_GRAY2BGR)
    
    # Draw panel borders (thick black lines)
    for p in [top_panel, bot_left, bot_right]:
        cv2.rectangle(page, (p[0], p[1]), (p[0] + p[2], p[1] + p[3]), (15, 15, 15), 3)

    # Hair color for protagonist (Mode B uses golden blonde hair in color preview)
    char_hair_bgr = (35, 180, 240) if is_colored else (40, 40, 40) # Bright golden blonde in color preview

    # Top panel: Protagonist prominent appearance
    draw_manga_face(
        page, 
        center_x=top_panel[0] + 250, 
        center_y=top_panel[1] + 230, 
        scale=1.5, 
        is_colored=is_colored,
        hair_color=char_hair_bgr
    )
    
    # Dialog bubble in top panel
    speech_text = f"CHAPTER 1 - PAGE {page_num}\nI WILL COLORIZE\nTHIS ENTIRE MANGA!" if page_num == 1 else f"PAGE {page_num}: THE POWER\nOF COLOR MEMORY\nIS UNMATCHED!"
    draw_speech_bubble(page, top_panel[0] + 460, top_panel[1] + 60, 200, 110, speech_text)
    
    # Bottom Left Panel: Speedlines & action pose
    for angle in range(-40, 40, 6):
        x1 = bot_left[0]
        y1 = bot_left[1] + 280 + int(angle * 4)
        x2 = bot_left[0] + 160
        y2 = bot_left[1] + 280
        cv2.line(page, (x1, y1), (x2, y2), (60, 60, 60), 1)
        
    draw_manga_face(
        page, 
        center_x=bot_left[0] + 220, 
        center_y=bot_left[1] + 280, 
        scale=1.1, 
        is_colored=is_colored,
        hair_color=char_hair_bgr
    )
    draw_speech_bubble(page, bot_left[0] + 40, bot_left[1] + 40, 160, 90, "SUGOI!\nIT IS ALIVE!")

    # Bottom Right Panel: Close-up expression
    draw_manga_face(
        page, 
        center_x=bot_right[0] + 170, 
        center_y=bot_right[1] + 290, 
        scale=1.3, 
        is_colored=is_colored,
        hair_color=char_hair_bgr
    )
    draw_speech_bubble(page, bot_right[0] + 130, bot_right[1] + 50, 170, 95, "LINE ART REMAINS\n100% PRESERVED!")
    
    return page

def main():
    print(f"Generating sample manga test suite in {SAMPLE_DIR}...")
    
    # 1. Mode B Colored Preview Cover Page (Page 1 is colored)
    cover_page = generate_manga_page(1, is_colored=True)
    cv2.imwrite(str(SAMPLE_DIR / "page_01_colored_preview.png"), cover_page)
    print(" -> Created page_01_colored_preview.png (Mode B Preview Page)")
    
    # 2. Black & White Pages (Pages 2 through 6)
    for p in range(2, 7):
        bw_page = generate_manga_page(p, is_colored=False)
        cv2.imwrite(str(SAMPLE_DIR / f"page_{p:02d}_bw.png"), bw_page)
        print(f" -> Created page_{p:02d}_bw.png (B&W Manga Page)")
        
    # 3. Mode C Official Character Reference Sheet
    ref_img = np.full((600, 500, 3), 250, dtype=np.uint8)
    draw_manga_face(ref_img, 250, 280, scale=1.8, is_colored=True, hair_color=(35, 180, 240))
    cv2.putText(ref_img, "OFFICIAL CHARACTER REFERENCE", (40, 50), cv2.FONT_HERSHEY_DUPLEX, 0.6, (20, 20, 20), 2)
    cv2.putText(ref_img, "PROTAGONIST: GOLDEN HAIR / CRIMSON COAT", (35, 80), cv2.FONT_HERSHEY_DUPLEX, 0.45, (80, 80, 80), 1)
    cv2.imwrite(str(SAMPLE_DIR / "official_character_reference.png"), ref_img)
    print(" -> Created official_character_reference.png (Mode C Official Art Reference)")

    # 4. Create sample ZIP archive for drag-and-drop test
    import zipfile
    zip_path = SAMPLE_DIR / "sample_manga_chapter.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(SAMPLE_DIR / "page_01_colored_preview.png", "page_01_colored_preview.png")
        for p in range(2, 7):
            zf.write(SAMPLE_DIR / f"page_{p:02d}_bw.png", f"page_{p:02d}_bw.png")
    print(" -> Created sample_manga_chapter.zip (Multi-page chapter archive)")
    print("Sample test suite generation complete!")

if __name__ == "__main__":
    main()
