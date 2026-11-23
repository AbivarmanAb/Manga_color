import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

def detect_speech_bubbles_and_text(image_bgr: np.ndarray) -> np.ndarray:
    """
    Detects manga speech bubbles and speech text to generate a strict protection mask.
    Only enclosed convex/oval speech bubbles are protected, preventing open background
    or panel regions from being falsely flagged as speech bubbles.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # 1. White region detection
    _, white_thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    # 2. Dialogue text detection inside bubbles
    _, text_thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    
    # Find candidate contours using two-level hierarchy
    contours, _ = cv2.findContours(white_thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    bubble_mask = np.zeros((h, w), dtype=np.uint8)
    min_area = (h * w) * 0.002   # At least 0.2% of page
    max_area = (h * w) * 0.16    # At most 16% of page (prevents taking whole panels)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area < area < max_area:
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = area / float(hull_area)
                # Speech bubbles are rounded or oval, possessing high solidity (> 0.80)
                if solidity > 0.80:
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    aspect = bw / float(bh)
                    if 0.30 < aspect < 3.2:
                        text_roi = text_thresh[y:y+bh, x:x+bw]
                        text_density = np.sum(text_roi > 0) / float(bw * bh)
                        # Must contain dialogue lettering
                        if 0.015 < text_density < 0.40:
                            cv2.drawContours(bubble_mask, [cnt], -1, 255, thickness=cv2.FILLED)
                    
    # Refine bubble mask edges
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    bubble_mask = cv2.dilate(bubble_mask, kernel, iterations=1)
    
    # Protect both white background of bubbles and black text strokes
    protected_mask = np.where((bubble_mask > 0) & (gray > 220), 255, 0).astype(np.uint8)
    protected_mask = np.where((bubble_mask > 0) & (text_thresh > 0), 255, protected_mask).astype(np.uint8)
    
    return protected_mask

def protect_speech_bubbles(colored_bgr: np.ndarray, original_bgr: np.ndarray, protection_mask: np.ndarray) -> np.ndarray:
    """
    Ensures that detected speech bubbles and manga dialogue text 
    remain completely pristine without any color contamination.
    """
    result = colored_bgr.copy()
    mask_3c = cv2.cvtColor(protection_mask, cv2.COLOR_GRAY2BGR)
    np.copyto(result, original_bgr, where=(mask_3c > 0))
    return result
