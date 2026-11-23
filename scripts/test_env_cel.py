import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

def test_atmospheric_panel_coloring(img_path: str, page_num: int):
    img_bgr = cv2.imread(img_path)
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Closed Line Art Segmentation (Flatting Mask)
    blur = cv2.bilateralFilter(gray, 5, 50, 50)
    _, dark_lines = cv2.threshold(blur, 68, 255, cv2.THRESH_BINARY_INV)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed_lines = cv2.morphologyEx(dark_lines, cv2.MORPH_CLOSE, kernel_close)
    non_lines = cv2.bitwise_not(closed_lines)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(non_lines, connectivity=8)

    # 2. Dialogue & Speech Bubble Mask
    bubble_mask = np.zeros((h, w), dtype=np.uint8)
    for idx in range(1, num_labels):
        area = stats[idx, cv2.CC_STAT_AREA]
        bx = stats[idx, cv2.CC_STAT_LEFT]
        by = stats[idx, cv2.CC_STAT_TOP]
        bw = stats[idx, cv2.CC_STAT_WIDTH]
        bh = stats[idx, cv2.CC_STAT_HEIGHT]
        region_gray = gray[labels == idx]
        mean_bright = np.mean(region_gray)
        if mean_bright > 220 and 400 < area < (w * h * 0.15) and (0.3 < bw / float(bh) < 3.0):
            bbox_gray = gray[by:by+bh, bx:bx+bw]
            dark_ratio = np.mean(bbox_gray < 70)
            if 0.03 < dark_ratio < 0.35:
                bubble_mask[labels == idx] = 255

    # 3. Detect White Margins & Gutters
    sobel = cv2.Sobel(gray, cv2.CV_32F, 1, 1)
    is_paper_white = (gray > 224) & (np.abs(sobel) < 14)
    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    gutters = cv2.morphologyEx(is_paper_white.astype(np.uint8), cv2.MORPH_OPEN, kernel_rect)

    # 4. Detect Panels
    _, panel_thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY_INV)
    h_lines = cv2.morphologyEx(panel_thresh, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1)))
    v_lines = cv2.morphologyEx(panel_thresh, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35)))
    grid_lines = h_lines | v_lines
    contours, _ = cv2.findContours(grid_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    panels = []
    for c in contours:
        px, py, pw, ph = cv2.boundingRect(c)
        if (w * 0.20 < pw) and (h * 0.08 < ph):
            panels.append((px, py, pw, ph))

    # Base canvas
    flats = np.full((h, w, 3), (240, 240, 240), dtype=np.uint8)

    # Palette bank (BGR)
    COLOR_SKY_LIGHT = np.array([225, 185, 105], dtype=np.uint8)   # Clear atmospheric cyan/blue
    COLOR_SKY_DEEP = np.array([210, 160, 75], dtype=np.uint8)     # Rich upper sky blue
    COLOR_RUINS_LIGHT = np.array([175, 195, 215], dtype=np.uint8) # Travertine sandstone
    COLOR_RUINS_DARK = np.array([135, 160, 185], dtype=np.uint8)  # Weathered masonry
    COLOR_EARTH = np.array([115, 145, 175], dtype=np.uint8)       # Ground rubble
    COLOR_SMOKE = np.array([215, 225, 235], dtype=np.uint8)       # Pale dust plume

    COLOR_SKIN = np.array([195, 222, 252], dtype=np.uint8)        # Anime warm skin
    COLOR_SANJI_HAIR = np.array([36, 195, 251], dtype=np.uint8)   # Golden blonde
    COLOR_SANJI_SUIT = np.array([32, 32, 38], dtype=np.uint8)     # Black suit
    COLOR_IVA_HAIR = np.array([205, 55, 120], dtype=np.uint8)     # Royal violet afro
    COLOR_IVA_CORSET = np.array([85, 22, 160], dtype=np.uint8)    # Magenta corset
    COLOR_CROWN = np.array([40, 185, 245], dtype=np.uint8)        # Gold crown

    for idx in range(1, num_labels):
        if bubble_mask[int(centroids[idx][1]), int(centroids[idx][0])] > 0:
            flats[labels == idx] = [255, 255, 255]
            continue
        if gutters[int(centroids[idx][1]), int(centroids[idx][0])] > 0 and stats[idx, cv2.CC_STAT_AREA] > 600:
            flats[labels == idx] = [255, 255, 255]
            continue

        cx, cy = centroids[idx]
        region_mean = np.mean(gray[labels == idx])

        # Page 8 specific character zones
        if page_num == 8:
            if (400 <= cx <= 1040) and (360 <= cy <= 960):
                if (600 <= cx <= 760) and (360 <= cy <= 450):
                    flats[labels == idx] = COLOR_CROWN
                elif (cy < 540 and not (620 <= cx <= 740 and cy > 460)) or (cx < 540) or (cx > 800 and cy < 750):
                    flats[labels == idx] = COLOR_IVA_HAIR
                elif (550 <= cx <= 790) and (470 <= cy <= 680) and region_mean > 120:
                    flats[labels == idx] = COLOR_SKIN
                elif (580 <= cx <= 770) and (590 <= cy <= 720):
                    flats[labels == idx] = [120, 80, 220] if region_mean > 160 else [80, 20, 160]
                elif cy > 720:
                    if (590 <= cx <= 760) and region_mean > 110:
                        flats[labels == idx] = COLOR_SKIN
                    else:
                        flats[labels == idx] = COLOR_IVA_CORSET
                continue

            elif (50 <= cx <= 460) and (950 <= cy <= 1450):
                if cy < 1180 and cx < 360 and region_mean > 100:
                    flats[labels == idx] = COLOR_SANJI_HAIR
                elif (1120 <= cy <= 1320) and (120 <= cx <= 380) and region_mean > 115:
                    flats[labels == idx] = COLOR_SKIN
                elif cy >= 1280:
                    flats[labels == idx] = COLOR_SANJI_SUIT
                else:
                    flats[labels == idx] = COLOR_RUINS_LIGHT
                continue

            elif cy < 380 and cx > 600:
                if cy < 220 and region_mean > 120:
                    flats[labels == idx] = COLOR_SANJI_HAIR
                elif (180 <= cy <= 320) and (680 <= cx <= 950) and region_mean > 115:
                    flats[labels == idx] = COLOR_SKIN
                else:
                    flats[labels == idx] = COLOR_SANJI_SUIT
                continue

        # Page 2 specific character zones
        elif page_num == 2:
            if cy > 1050:
                if (420 <= cx <= 580) and (1180 <= cy <= 1380):
                    flats[labels == idx] = COLOR_SANJI_SUIT
                    continue
                elif region_mean > 130:
                    flats[labels == idx] = COLOR_SKY_LIGHT
                    continue
            elif cx < 400 and cy < 500:
                if region_mean > 130 and (140 <= cx <= 360) and (120 <= cy <= 420):
                    flats[labels == idx] = COLOR_SKIN
                    continue
                elif region_mean < 80:
                    flats[labels == idx] = [32, 32, 38]
                    continue

        # General Environment / Background Assignment for any unassigned component:
        # Determine which panel this component belongs to
        comp_panel = None
        for (px, py, pw, ph) in panels:
            if px <= cx <= px + pw and py <= cy <= py + ph:
                comp_panel = (px, py, pw, ph)
                break
                
        if comp_panel:
            px, py, pw, ph = comp_panel
            rel_y = (cy - py) / float(ph)
            # Upper 35% of panel: Sky or high ruins
            if rel_y < 0.35 and region_mean > 130:
                flats[labels == idx] = COLOR_SKY_DEEP if rel_y < 0.18 else COLOR_SKY_LIGHT
            elif region_mean > 165:
                flats[labels == idx] = COLOR_SMOKE # light dust / highlight
            elif region_mean > 110:
                flats[labels == idx] = COLOR_RUINS_LIGHT # masonry
            else:
                flats[labels == idx] = COLOR_EARTH # shadow / ground
        else:
            if region_mean > 150:
                flats[labels == idx] = COLOR_RUINS_LIGHT
            else:
                flats[labels == idx] = COLOR_RUINS_DARK

    # CIELAB Shading
    lab = cv2.cvtColor(flats, cv2.COLOR_BGR2LAB)
    l_norm = gray.astype(np.float32) / 255.0
    l_curved = np.clip(np.power(l_norm, 1.10) * 255.0, 0, 255).astype(np.uint8)
    lab[:, :, 0] = l_curved
    shaded_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # S-Curve Boost
    hsv = cv2.cvtColor(shaded_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.45 + 10.0, 0, 255)
    hsv[:, :, 2] = np.clip(1.05 * (hsv[:, :, 2] - 128) + 128 + 2.0, 0, 255)
    enhanced_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # Clean white bubbles & gutters
    enhanced_bgr[bubble_mask > 0] = [255, 255, 255]
    enhanced_bgr[gutters > 0] = [255, 255, 255]

    # Jet black lines
    ink_mask = gray < 60
    enhanced_bgr[ink_mask] = img_bgr[ink_mask]

    out_file = f"storage/test_env_p{page_num}.jpg"
    cv2.imwrite(out_file, enhanced_bgr, [cv2.IMWRITE_JPEG_QUALITY, 96])
    hsv_res = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2HSV)
    print(f"Page {page_num} saved to {out_file}: Mean Sat={np.mean(hsv_res[:,:,1]):.1f}, Colored Coverage={np.mean(hsv_res[:,:,1] > 20)*100:.1f}%")

if __name__ == "__main__":
    test_atmospheric_panel_coloring("storage/projects/proj_f0afce218b/original/p0002_page_0002_fzImg0.jpg", 2)
    test_atmospheric_panel_coloring("storage/projects/proj_f0afce218b/original/p0008_page_0008_fzImg0.jpg", 8)
