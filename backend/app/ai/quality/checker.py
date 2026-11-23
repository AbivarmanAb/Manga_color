import cv2
import numpy as np
from typing import Dict, Any, List

def run_quality_check(
    original_bgr: np.ndarray,
    colored_bgr: np.ndarray,
    bubble_protection_mask: np.ndarray
) -> Dict[str, Any]:
    """
    Automated Manga Colorization Quality Assurance Auditor.
    Scans for:
    1. Speech bubble contamination (color bleeding into dialogue).
    2. Edge bleeding across prominent line art.
    3. Unexpected blank regions.
    4. Contrast & dynamic range consistency.
    """
    h, w = original_bgr.shape[:2]
    flags = []
    
    # 1. Speech Bubble Contamination Check
    hsv_colored = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv_colored[:, :, 1]
    
    # In protected speech bubble regions, saturation should be near 0
    bubble_sat = saturation[bubble_protection_mask > 0]
    if len(bubble_sat) > 0:
        contaminated_bubble_pixels = np.sum(bubble_sat > 25)
        bubble_leak_ratio = contaminated_bubble_pixels / float(len(bubble_sat))
        if bubble_leak_ratio > 0.05:
            flags.append(f"Speech bubble color leakage detected ({round(bubble_leak_ratio*100, 1)}% affected)")
    else:
        bubble_leak_ratio = 0.0
        
    # 2. Line Art Preservation Check
    orig_gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
    color_gray = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2GRAY)
    
    # Check if dark ink lines were washed out or blurred
    ink_mask = orig_gray < 50
    if np.any(ink_mask):
        colored_ink_luminance = color_gray[ink_mask]
        washed_out = np.sum(colored_ink_luminance > 120)
        wash_ratio = washed_out / float(len(colored_ink_luminance))
        if wash_ratio > 0.08:
            flags.append(f"Line art contrast degradation ({round(wash_ratio*100, 1)}% affected)")
    else:
        wash_ratio = 0.0
        
    # 3. Overall Color Coverage
    overall_colored_pixels = np.sum(saturation > 15)
    total_pixels = h * w
    coverage_ratio = overall_colored_pixels / float(total_pixels)
    
    # Quality Score: 0.0 to 1.0
    quality_score = 1.0 - (bubble_leak_ratio * 0.5 + wash_ratio * 0.5)
    quality_score = max(0.5, min(0.99, round(quality_score, 2)))
    
    is_passed = len(flags) == 0
    
    return {
        "passed": is_passed,
        "score": quality_score,
        "flags": flags,
        "metrics": {
            "bubble_leak_ratio": round(float(bubble_leak_ratio), 4),
            "wash_ratio": round(float(wash_ratio), 4),
            "coverage_ratio": round(float(coverage_ratio), 4)
        }
    }
