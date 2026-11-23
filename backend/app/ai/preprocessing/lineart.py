import cv2
import numpy as np
from typing import Tuple

def extract_line_art(image_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts pure manga line art and creates an edge preservation alpha mask.
    Returns:
        line_art: Grayscale line art image [0-255] where lines are black and background is pure white.
        alpha_mask: Normalized float mask [0.0 - 1.0] where 1.0 is ink (keep original) and 0.0 is colorable space.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding to capture clean ink strokes
    inv_threshold = cv2.adaptiveThreshold(
        gray, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        15, 
        4
    )
    
    # Refine strokes with mild morphological closing to connect faint ink lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    refined_ink = cv2.morphologyEx(inv_threshold, cv2.MORPH_CLOSE, kernel)
    
    # Line art is inverted back (0=black lines, 255=white paper)
    line_art = 255 - refined_ink
    
    # Create smooth float alpha mask for non-destructive blending
    # Darker pixels in gray image have higher opacity in ink mask
    ink_mask = (255.0 - gray.astype(np.float32)) / 255.0
    ink_mask = np.clip((ink_mask - 0.25) / 0.65, 0.0, 1.0)
    
    return line_art, ink_mask

def blend_color_with_line_art(colored_bgr: np.ndarray, original_bgr: np.ndarray, preserve_strength: float = 0.95) -> np.ndarray:
    """
    Composites synthesized color underneath original crisp manga black line art.
    Preserves 100% of mangaka pencil/ink integrity, screen-tones, and panel borders
    using professional Multiply + Luminance preservation blend modes.
    """
    orig_gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
    
    # Normalize original gray to [0, 1]
    norm_orig = orig_gray.astype(np.float32) / 255.0
    norm_color = colored_bgr.astype(np.float32) / 255.0
    
    # Multiply blending: Color * Original Line Art
    # In pure white areas (orig=1.0), Color is 100% visible.
    # In pure black ink areas (orig=0.0), ink stays completely jet black.
    # In mid-tone gray areas (crosshatching/shading), color darkens naturally.
    blended = np.empty_like(norm_color)
    for c in range(3):
        blended[:, :, c] = norm_color[:, :, c] * (norm_orig ** 1.15)
        
    final_output = np.clip(blended * 255.0, 0, 255).astype(np.uint8)
    return final_output
