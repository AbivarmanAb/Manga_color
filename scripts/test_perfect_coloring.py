import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

def build_smart_manga_flats(img_bgr: np.ndarray, page_num: int):
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Clean screentones for cleaner component analysis
    blur = cv2.bilateralFilter(gray, 5, 50, 50)
    
    # 2. Extract Line Art (dark ink lines)
    _, ink_thresh = cv2.threshold(blur, 68, 255, cv2.THRESH_BINARY_INV)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed_lines = cv2.morphologyEx(ink_thresh, cv2.MORPH_CLOSE, kernel_close)
    non_lines = cv2.bitwise_not(closed_lines)
    
    # 3. Detect White Margins & Gutters
    sobel = cv2.Sobel(gray, cv2.CV_32F, 1, 1)
    is_paper_white = (gray > 224) & (np.abs(sobel) < 14)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    gutters = cv2.morphologyEx(is_paper_white.astype(np.uint8), cv2.MORPH_OPEN, kernel_open)
    
    # 4. Connected Components for Flatting
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(non_lines, connectivity=8)
    print(f"Page {page_num}: Found {num_labels} segmented comic regions")
    
    # Create base flat canvas
    flats = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Color definitions (BGR)
    COLOR_SKY = np.array([215, 175, 110], dtype=np.uint8)     # Soft manga sky blue (RGB: 110, 175, 215)
    COLOR_RUINS = np.array([170, 195, 215], dtype=np.uint8)   # Sandstone ruins (RGB: 215, 195, 170)
    COLOR_EARTH = np.array([140, 170, 190], dtype=np.uint8)   # Warm masonry/earth (RGB: 190, 170, 140)
    COLOR_DUST = np.array([210, 225, 235], dtype=np.uint8)    # Pale dust/smoke (RGB: 235, 225, 210)
    
    COLOR_SKIN = np.array([195, 220, 250], dtype=np.uint8)    # Anime warm skin (RGB: 250, 220, 195)
    COLOR_SANJI_HAIR = np.array([36, 191, 251], dtype=np.uint8) # Golden blonde (RGB: 251, 191, 36)
    COLOR_SANJI_SUIT = np.array([30, 30, 35], dtype=np.uint8)   # Black suit (RGB: 35, 30, 30)
    COLOR_IVA_HAIR = np.array([195, 55, 120], dtype=np.uint8)  # Violet afro (RGB: 120, 55, 195)
    COLOR_IVA_CORSET = np.array([80, 20, 150], dtype=np.uint8) # Magenta/purple corset (RGB: 150, 20, 80)
    COLOR_GOLD_CROWN = np.array([40, 180, 240], dtype=np.uint8) # Gold crown (RGB: 240, 180, 40)
    
    # Detect speech bubbles (bright, roundish, contains text)
    bubble_mask = np.zeros((h, w), dtype=np.uint8)
    for idx in range(1, num_labels):
        area = stats[idx, cv2.CC_STAT_AREA]
        bx = stats[idx, cv2.CC_STAT_LEFT]
        by = stats[idx, cv2.CC_STAT_TOP]
        bw = stats[idx, cv2.CC_STAT_WIDTH]
        bh = stats[idx, cv2.CC_STAT_HEIGHT]
        
        region_gray = gray[labels == idx]
        mean_bright = np.mean(region_gray)
        
        # Speech bubble heuristics: bright > 220, not full page width, reasonable aspect ratio
        if mean_bright > 222 and 400 < area < (w * h * 0.15) and (0.3 < bw / float(bh) < 3.0):
            # Check if region contains dark text strokes inside
            bbox_gray = gray[by:by+bh, bx:bx+bw]
            dark_ratio = np.mean(bbox_gray < 70)
            if 0.03 < dark_ratio < 0.35:
                bubble_mask[labels == idx] = 255

    # Paint components based on semantics
    for idx in range(1, num_labels):
        if bubble_mask[int(centroids[idx][1]), int(centroids[idx][0])] > 0:
            flats[labels == idx] = [255, 255, 255]
            continue
            
        if gutters[int(centroids[idx][1]), int(centroids[idx][0])] > 0 and stats[idx, cv2.CC_STAT_AREA] > 500:
            flats[labels == idx] = [255, 255, 255]
            continue

        cx, cy = centroids[idx]
        area = stats[idx, cv2.CC_STAT_AREA]
        region_mean = np.mean(gray[labels == idx])
        
        # Check Page 8 specific character zones
        if page_num == 8:
            # Ivankov in center panel: cy in 380..950, cx in 420..1020
            if (400 <= cx <= 1040) and (360 <= cy <= 960):
                # Crown: top of head (cy in 360..450, cx in 620..740)
                if (600 <= cx <= 760) and (360 <= cy <= 450):
                    flats[labels == idx] = COLOR_GOLD_CROWN
                # Big afro hair: around head (cy in 420..820, cx < 560 or cx > 780 or cy in 420..540)
                elif (cy < 540 and not (620 <= cx <= 740 and cy > 460)) or (cx < 540) or (cx > 800 and cy < 750):
                    flats[labels == idx] = COLOR_IVA_HAIR
                # Face skin: center
                elif (550 <= cx <= 790) and (470 <= cy <= 680) and region_mean > 120:
                    flats[labels == idx] = COLOR_SKIN
                # Mouth / lips / teeth
                elif (580 <= cx <= 770) and (590 <= cy <= 720):
                    flats[labels == idx] = [120, 80, 220] if region_mean > 160 else [80, 20, 160]
                # Corset / chest / collar: below 720
                elif cy > 720:
                    if (590 <= cx <= 760) and region_mean > 110:
                        flats[labels == idx] = COLOR_SKIN # chest skin
                    else:
                        flats[labels == idx] = COLOR_IVA_CORSET
                else:
                    flats[labels == idx] = COLOR_IVA_HAIR
                continue
                
            # Sanji in bottom left panel: cy in 950..1450, cx in 50..450
            if (50 <= cx <= 460) and (950 <= cy <= 1450):
                # Sanji hair: top of his head
                if cy < 1180 and cx < 360 and region_mean > 100:
                    flats[labels == idx] = COLOR_SANJI_HAIR
                # Sanji face skin
                elif (1120 <= cy <= 1320) and (120 <= cx <= 380) and region_mean > 115:
                    flats[labels == idx] = COLOR_SKIN
                # Suit / collar
                elif cy >= 1280:
                    flats[labels == idx] = COLOR_SANJI_SUIT
                else:
                    flats[labels == idx] = COLOR_RUINS
                continue

            # Top right Sanji: cy < 380, cx > 600
            if cy < 380 and cx > 600:
                if cy < 220 and region_mean > 120:
                    flats[labels == idx] = COLOR_SANJI_HAIR
                elif (180 <= cy <= 320) and (680 <= cx <= 950) and region_mean > 115:
                    flats[labels == idx] = COLOR_SKIN
                else:
                    flats[labels == idx] = COLOR_SANJI_SUIT
                continue
                
            # Default background for Page 8 panels: warm ruins / sky
            if cy < 380:
                flats[labels == idx] = COLOR_SKY if region_mean > 140 else COLOR_DUST
            else:
                flats[labels == idx] = COLOR_RUINS if region_mean > 90 else COLOR_EARTH

        # Page 2 semantics (Architecture, sky, Sanji kick)
        elif page_num == 2:
            # Bottom panel (Sanji kick): cy > 1050
            if cy > 1050:
                # Sanji body in center of bottom panel: cx in 400..600, cy in 1180..1400
                if (420 <= cx <= 580) and (1180 <= cy <= 1380):
                    flats[labels == idx] = COLOR_SANJI_SUIT
                # Speed lines / background sky
                elif region_mean > 120:
                    flats[labels == idx] = COLOR_SKY
                else:
                    flats[labels == idx] = COLOR_EARTH
            # Upper left villain face: cx < 400, cy < 500
            elif cx < 400 and cy < 500:
                if region_mean > 130 and (140 <= cx <= 360) and (120 <= cy <= 420):
                    flats[labels == idx] = COLOR_SKIN
                elif region_mean < 80:
                    flats[labels == idx] = [30, 30, 30] # dark hair/collar
                else:
                    flats[labels == idx] = COLOR_RUINS
            # Middle right ruins: sandstone architecture
            else:
                if cy < 450 and region_mean > 160:
                    flats[labels == idx] = COLOR_SKY # Sky above ruins
                elif region_mean > 120:
                    flats[labels == idx] = COLOR_RUINS
                else:
                    flats[labels == idx] = COLOR_EARTH

    # 5. Native Cel-Shading Modulation via CIELAB
    lab = cv2.cvtColor(flats, cv2.COLOR_BGR2LAB)
    
    # Smooth gamma-mapped luminance from original manga
    # L_clean: preserves white highlights and deepens dark ink
    l_norm = gray.astype(np.float32) / 255.0
    l_curved = np.clip(np.power(l_norm, 1.15) * 255.0, 0, 255).astype(np.uint8)
    
    lab[:, :, 0] = l_curved
    shaded_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # 6. Lock pure speech bubbles & gutters to pure white
    shaded_bgr[bubble_mask > 0] = [255, 255, 255]
    shaded_bgr[gutters > 0] = [255, 255, 255]
    
    # 7. Re-apply pure mangaka ink lines on top (Multiply / Inking Blend)
    ink_line = gray < 60
    shaded_bgr[ink_line] = img_bgr[ink_line]
    
    out_path = f"storage/test_perfect_p{page_num}.jpg"
    cv2.imwrite(out_path, shaded_bgr, [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(f"Saved {out_path} successfully!")

if __name__ == "__main__":
    build_smart_manga_flats(cv2.imread("storage/projects/proj_f0afce218b/original/p0002_page_0002_fzImg0.jpg"), 2)
    build_smart_manga_flats(cv2.imread("storage/projects/proj_f0afce218b/original/p0008_page_0008_fzImg0.jpg"), 8)
