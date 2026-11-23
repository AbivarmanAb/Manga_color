import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple
from pathlib import Path

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB integers to a hex color string."""
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Converts hex color string to RGB tuple."""
    hex_clean = hex_str.lstrip('#')
    return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))

def hex_to_bgr(hex_str: str) -> Tuple[int, int, int]:
    """Converts hex color string to BGR tuple for OpenCV."""
    r, g, b = hex_to_rgb(hex_str)
    return (b, g, r)

def is_skin_tone(h: float, s: float, v: float) -> bool:
    """Heuristic for human/anime skin tone detection in HSV space (H: 0-180, S: 0-255, V: 0-255)."""
    # Typical skin range in OpenCV HSV: H in [0, 25], S in [20, 180], V in [80, 255]
    return (0 <= h <= 25 or 170 <= h <= 180) and (20 <= s <= 180) and (80 <= v <= 255)

def extract_dominant_colors(image_bgr: np.ndarray, num_colors: int = 8) -> List[Dict[str, Any]]:
    """
    Extracts dominant color clusters from an image using K-Means in CIELAB space.
    Filters out background white and line-art black to capture true character hues.
    """
    # Downsample for fast clustering
    small = cv2.resize(image_bgr, (256, 256), interpolation=cv2.INTER_AREA)
    pixels = small.reshape(-1, 3).astype(np.float32)
    
    # Filter out near-pure-white paper and near-pure-black ink
    luminance = 0.299 * pixels[:, 2] + 0.587 * pixels[:, 1] + 0.114 * pixels[:, 0]
    valid_mask = (luminance > 25) & (luminance < 240)
    
    valid_pixels = pixels[valid_mask]
    if len(valid_pixels) < 100:
        valid_pixels = pixels  # Fallback if image is extreme
        
    # K-Means criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.2)
    k = min(num_colors, len(valid_pixels))
    
    _, labels, centers = cv2.kmeans(valid_pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    # Count frequency of each cluster
    unique_labels, counts = np.unique(labels, return_counts=True)
    total_count = len(labels)
    
    palette = []
    for lbl, count in zip(unique_labels, counts):
        bgr = centers[lbl]
        b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
        hex_code = rgb_to_hex(r, g, b)
        weight = float(count) / total_count
        
        # Determine semantic candidate
        hsv_pixel = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = hsv_pixel[0], hsv_pixel[1], hsv_pixel[2]
        
        is_skin = is_skin_tone(h, s, v)
        palette.append({
            "hex": hex_code,
            "bgr": [b, g, r],
            "rgb": [r, g, b],
            "weight": round(weight, 3),
            "is_skin_candidate": is_skin,
            "saturation": int(s),
            "brightness": int(v)
        })
        
    # Sort by prominence
    palette.sort(key=lambda x: x["weight"], reverse=True)
    return palette

def categorize_character_palette(palette: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Intelligently assigns extracted color swatches into character anatomy categories:
    Skin, Hair, Eyes, Primary Outfit, Secondary Outfit, Accent.
    """
    skin_candidates = [c for c in palette if c.get("is_skin_candidate")]
    other_candidates = [c for c in palette if not c.get("is_skin_candidate")]
    
    # 1. Skin Color
    if skin_candidates:
        skin_color = skin_candidates[0]["hex"]
    else:
        skin_color = "#FFE0BD" # Default fair anime skin tone
        
    # 2. Hair Color (often prominent high contrast or unique hue)
    if other_candidates:
        hair_color = other_candidates[0]["hex"]
    else:
        hair_color = "#2E2A27" # Default dark brown / anime black
        
    # 3. Primary Outfit
    if len(other_candidates) > 1:
        outfit_1 = other_candidates[1]["hex"]
    else:
        outfit_1 = "#1E3A8A" # Royal navy
        
    # 4. Secondary Outfit
    if len(other_candidates) > 2:
        outfit_2 = other_candidates[2]["hex"]
    else:
        outfit_2 = "#E5E7EB" # Clean white/silver
        
    # 5. Eye & Accent
    if len(other_candidates) > 3:
        eye_color = other_candidates[3]["hex"]
    else:
        eye_color = hair_color
        
    accent_color = other_candidates[4]["hex"] if len(other_candidates) > 4 else "#EF4444"
    
    return {
        "skin_color": skin_color,
        "hair_color": hair_color,
        "eye_color": eye_color,
        "primary_outfit_color": outfit_1,
        "secondary_outfit_color": outfit_2,
        "accent_color": accent_color
    }
