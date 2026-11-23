import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

from ..preprocessing.layout import detect_speech_bubbles_and_text, protect_speech_bubbles
from ..preprocessing.lineart import blend_color_with_line_art
from ..character.palette_extractor import hex_to_bgr

def harmonize_semantic_cel_shading(
    original_bgr: np.ndarray,
    neural_bgr: np.ndarray,
    character_profiles: List[Dict[str, Any]] = None,
    coloring_style: str = "vibrant_anime"
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Pristine Manga Cel-Shading Harmonizer.
    
    Combines the organic scene understanding of deep convolutional colorization
    with strict manga line-art preservation and zero color overflow:
    1. Base Canvas: Organic neural colorization (scene-aware sky, earth, sparks, outfits).
    2. Localized Character Anchor: Refines hair and skin tones strictly within anatomical bounds.
    3. Gutter & Margin Normalization: Locks unprinted margins and panel gutters to pure #FFFFFF.
    4. Speech Bubble Lock: 100% pure white interior with razor-sharp black lettering.
    5. Mangaka Line Art Integrity: Restores 100% jet-black ink lines across all panels.
    """
    h, w = original_bgr.shape[:2]
    gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Closed Line Art Segmentation
    blur = cv2.bilateralFilter(gray, 5, 50, 50)
    _, dark_lines = cv2.threshold(blur, 68, 255, cv2.THRESH_BINARY_INV)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed_lines = cv2.morphologyEx(dark_lines, cv2.MORPH_CLOSE, kernel_close)
    non_lines = cv2.bitwise_not(closed_lines)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(non_lines, connectivity=8)

    # 2. Strict Speech Bubble Detection (solidity & text-density gated)
    bubble_mask = detect_speech_bubbles_and_text(original_bgr)

    # 3. Base Flats initialized from Neural Colorizer (continuous, contextual)
    flats = neural_bgr.copy()

    # 4. Localized Character Palette Injection (Zero-Overflow Guarded)
    if character_profiles:
        for char in character_profiles:
            face_box = char.get("face_bbox")
            char_box = char.get("character_bbox")
            skin_hex = char.get("skin_color")
            hair_hex = char.get("hair_color")
            
            # Guard: Only apply to compact, genuine character figures to prevent panel flooding
            if face_box:
                fx, fy, fw, fh = face_box
                if fw < (w * 0.38) and fh < (h * 0.28):
                    skin_bgr = hex_to_bgr(skin_hex) if skin_hex else None
                    hair_bgr = hex_to_bgr(hair_hex) if hair_hex else None
                    
                    for idx in range(1, num_labels):
                        cx, cy = centroids[idx]
                        area = stats[idx, cv2.CC_STAT_AREA]
                        
                        # Skin components: compact cells within the lower face
                        if skin_bgr and (fx <= cx <= fx + fw) and (fy + fh * 0.20 <= cy <= fy + fh * 0.95):
                            if area < (fw * fh * 0.40) and bubble_mask[int(cy), int(cx)] == 0:
                                if np.mean(gray[labels == idx]) > 100:
                                    flats[labels == idx] = skin_bgr

                        # Hair components: compact cells atop the face
                        if hair_bgr and (fx - fw * 0.20 <= cx <= fx + fw * 1.20) and (fy - fh * 0.45 <= cy <= fy + fh * 0.30):
                            if area < (fw * fh * 0.50) and bubble_mask[int(cy), int(cx)] == 0:
                                if np.mean(gray[labels == idx]) > 80:
                                    flats[labels == idx] = hair_bgr

    # 5. Composite Flats with Native CIELAB Luminance Modulation
    lab_flats = cv2.cvtColor(flats, cv2.COLOR_BGR2LAB)
    l_norm = gray.astype(np.float32) / 255.0
    l_curved = np.clip(np.power(l_norm, 1.08) * 255.0, 0, 255).astype(np.uint8)
    lab_flats[:, :, 0] = l_curved
    cel_shaded = cv2.cvtColor(lab_flats, cv2.COLOR_LAB2BGR)

    # 6. Dynamic S-Curve Vibrancy Boost
    hsv = cv2.cvtColor(cel_shaded, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    valid_chroma = (val > 35) & (val < 250) & (sat > 10)
    
    if coloring_style == "vibrant_anime":
        hsv[:, :, 1] = np.where(valid_chroma, np.clip(sat * 1.35 + 8.0, 0, 255), sat)
        hsv[:, :, 2] = np.clip(1.04 * (val - 128) + 128 + 2.0, 0, 255)
    elif coloring_style == "classic_manga":
        hsv[:, :, 1] = np.where(valid_chroma, np.clip(sat * 1.05, 0, 255), sat)
    else:
        hsv[:, :, 1] = np.where(valid_chroma, np.clip(sat * 1.20 + 4.0, 0, 255), sat)
        
    graded_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # 7. Pure Paper-White Gutter & Margin Normalization
    sobel = cv2.Sobel(gray, cv2.CV_32F, 1, 1)
    is_paper_white = (gray > 224) & (np.abs(sobel) < 14)
    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    paper_white_mask = cv2.morphologyEx(is_paper_white.astype(np.uint8), cv2.MORPH_OPEN, kernel_rect)
    graded_bgr[paper_white_mask > 0] = [255, 255, 255]

    # 8. Dialogue Speech Bubble Protection (Zero-Leak Guard)
    text_in_bubble = (bubble_mask > 0) & (gray < 165)
    graded_bgr[bubble_mask > 0] = [255, 255, 255]
    graded_bgr[text_in_bubble] = original_bgr[text_in_bubble]

    # 9. Pure Jet-Black Mangaka Line Art Compositing
    ink_mask = gray < 65
    graded_bgr[ink_mask] = original_bgr[ink_mask]

    final_bgr = graded_bgr

    hsv_final = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2HSV)
    sat_final = hsv_final[:, :, 1]
    
    report = {
        "engine": "semantic_cel_harmonizer",
        "segmented_regions": num_labels,
        "mean_saturation": round(float(np.mean(sat_final)), 2),
        "colored_coverage_pct": round(float(np.mean(sat_final > 20) * 100), 2),
        "speech_bubbles_protected": int(np.sum(bubble_mask > 0)),
    }

    return final_bgr, bubble_mask, report
