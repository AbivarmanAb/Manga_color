import cv2
import numpy as np
from PIL import Image
from pathlib import Path

def remove_screentones(image: np.ndarray, strength: int = 1) -> np.ndarray:
    """
    Suppresses manga screentones (halftones, hatching, dot matrix patterns) 
    while strictly preserving sharp line art and panel borders.
    Uses multi-scale bilateral filtering and edge-preserving smoothing.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # Bilateral filter smooths dot patterns while keeping sharp gradient edges
    d = 7 + (strength * 2)
    sigma_color = 50 + (strength * 15)
    sigma_space = 50 + (strength * 15)
    
    smoothed = cv2.bilateralFilter(gray, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    
    # Adaptive median filtering to eliminate residual dot grid frequencies
    median = cv2.medianBlur(smoothed, 3)
    
    # Edge-guided blend to ensure high-contrast line art is untouched
    edges = cv2.Canny(gray, 80, 180)
    kernel = np.ones((2, 2), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)
    
    result = np.where(dilated_edges > 0, gray, median)
    
    if len(image.shape) == 3:
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    return result

def normalize_manga_image(image_path: Path) -> np.ndarray:
    """Loads and standardizes an image into high-quality BGR format."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Unable to read image at {image_path}")
    return img
