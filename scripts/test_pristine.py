import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

def build_pristine_page(original_bgr: np.ndarray, neural_bgr: np.ndarray, output_path: str):
    h, w = original_bgr.shape[:2]
    gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Start from the neural colorizer (which produces gorgeous, contextual anime color)
    result = neural_bgr.copy()
    
    # 2. Strict Speech Bubble Detection via layout analysis
    from backend.app.ai.preprocessing.layout import detect_speech_bubbles_and_text
    bubble_mask = detect_speech_bubbles_and_text(original_bgr)
    
    # 3. Detect White Margins & Gutters
    sobel = cv2.Sobel(gray, cv2.CV_32F, 1, 1)
    is_paper_white = (gray > 224) & (np.abs(sobel) < 14)
    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    gutters = cv2.morphologyEx(is_paper_white.astype(np.uint8), cv2.MORPH_OPEN, kernel_rect)
    
    # 4. Lock gutters to pure #FFFFFF
    result[gutters > 0] = [255, 255, 255]
    
    # 5. Lock speech bubbles: pure #FFFFFF background + 100% original sharp text
    text_in_bubble = (bubble_mask > 0) & (gray < 165)
    result[bubble_mask > 0] = [255, 255, 255]
    result[text_in_bubble] = original_bgr[text_in_bubble]
    
    # 6. Composite pure jet-black mangaka ink lines across the entire page
    ink_mask = gray < 65
    result[ink_mask] = original_bgr[ink_mask]
    
    cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 96])
    print(f"Saved pristine page to {output_path}!")

if __name__ == "__main__":
    orig = cv2.imread("storage/projects/proj_f0afce218b/original/p0005_page_0005_fzImg0.jpg")
    neural = cv2.imread("storage/test_p5_neural_only.jpg")
    build_pristine_page(orig, neural, "storage/test_p5_pristine.jpg")
