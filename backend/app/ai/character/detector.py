import cv2
import numpy as np
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

def get_face_cascade() -> Optional[Any]:
    """Loads OpenCV face cascade classifier."""
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            return cv2.CascadeClassifier(cascade_path)
    except Exception:
        pass
    return None

def compute_character_visual_signature(crop_bgr: np.ndarray) -> np.ndarray:
    """
    Computes a normalized structural feature vector (HOG + intensity distribution)
    for character identity matching across pages.
    """
    resized = cv2.resize(crop_bgr, (64, 64))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
    
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    
    bins = np.int32(ang / 45.0) % 8
    hist = np.zeros(8, dtype=np.float32)
    for i in range(8):
        hist[i] = np.sum(mag[bins == i])
        
    grid = cv2.resize(gray, (4, 4)).flatten().astype(np.float32) / 255.0
    feature = np.concatenate([hist / (np.linalg.norm(hist) + 1e-6), grid])
    feature = feature / (np.linalg.norm(feature) + 1e-6)
    return feature

def calculate_similarity(sig1: np.ndarray, sig2: np.ndarray) -> float:
    """Calculates cosine similarity between two character feature signatures."""
    if sig1 is None or sig2 is None or len(sig1) == 0 or len(sig2) == 0:
        return 0.0
    dot = np.dot(sig1, sig2)
    norm = (np.linalg.norm(sig1) * np.linalg.norm(sig2))
    if norm < 1e-6:
        return 0.0
    return float(np.clip(dot / norm, 0.0, 1.0))

def detect_character_regions(image_bgr: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detects character faces, heads, and bodies across all manga panels.
    Combines cascade detection with contour saliency to ensure anime characters are never missed.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    cascade = get_face_cascade()
    
    detections = []
    
    # 1. Cascade classifier detection
    if cascade is not None:
        faces = cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=4, 
            minSize=(int(w * 0.04), int(h * 0.04))
        )
        for (x, y, fw, fh) in faces:
            top = max(0, int(y - fh * 0.4))
            bottom = min(h, int(y + fh * 1.8))
            left = max(0, int(x - fw * 0.2))
            right = min(w, int(x + fw * 1.2))
            
            crop = image_bgr[top:bottom, left:right]
            sig = compute_character_visual_signature(crop)
            
            detections.append({
                "face_bbox": [int(x), int(y), int(fw), int(fh)],
                "character_bbox": [int(left), int(top), int(right - left), int(bottom - top)],
                "signature": sig.tolist(),
                "confidence": 0.88
            })
            
    # 2. Multi-panel contour saliency scanner (detects anime characters where cascade misses)
    _, thresh = cv2.threshold(gray, 205, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        # Bounded area prevents whole-panel speedline meshes from hallucinating as characters
        if (h * w * 0.005) < area < (h * w * 0.12):
            bx, by, bw, bh = cv2.boundingRect(c)
            # Character figure must not span entire panel width or height
            if bw < (w * 0.48) and bh < (h * 0.42):
                aspect = bh / float(bw)
                if 0.65 < aspect < 3.2:
                    # Check overlap with existing cascade detections
                    is_duplicate = False
                    for d in detections:
                        dx, dy, dw, dh = d["character_bbox"]
                        overlap_x = max(0, min(bx + bw, dx + dw) - max(bx, dx))
                        overlap_y = max(0, min(by + bh, dy + dh) - max(by, dy))
                        if (overlap_x * overlap_y) > 0.4 * min(bw * bh, dw * dh):
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        candidates.append((bx, by, bw, bh, area))
                    
    candidates.sort(key=lambda x: x[4], reverse=True)
    for bx, by, bw, bh, _ in candidates[:5]:
        crop = image_bgr[by:by+bh, bx:bx+bw]
        sig = compute_character_visual_signature(crop)
        
        fw, fh = int(bw * 0.6), int(bh * 0.35)
        fx, fy = bx + int(bw * 0.2), by
        
        detections.append({
            "face_bbox": [fx, fy, fw, fh],
            "character_bbox": [bx, by, bw, bh],
            "signature": sig.tolist(),
            "confidence": 0.76
        })
        
    return detections
