import os
import re
import zipfile
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any
from PIL import Image
import numpy as np
import cv2

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from ..config import settings

def natural_sort_key(s: str) -> List[Any]:
    """Provides natural alphanumeric sorting key (e.g. page_1, page_2, ..., page_10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def is_safe_zip_path(target_dir: Path, path: str) -> bool:
    """Protects against zip path traversal attacks (Zip Slip)."""
    resolved_target = target_dir.resolve()
    resolved_path = (target_dir / path).resolve()
    return resolved_path.is_relative_to(resolved_target)

def detect_is_colored_image(image_path: Path, saturation_threshold: float = 24.0, color_pixel_ratio_threshold: float = 0.035) -> bool:
    """
    Intelligently determines whether an image is a colored preview/cover page or a black-and-white page.
    Analyzes HSV color space saturation and detects chromatic content vs grayscale/screentones.
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return False
        
        # Check standard channels
        if len(img.shape) < 3 or img.shape[2] == 1:
            return False
            
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        
        # Calculate percentage of pixels with non-trivial saturation
        colored_pixels = np.sum(sat > saturation_threshold)
        total_pixels = sat.size
        ratio = colored_pixels / float(total_pixels)
        
        return ratio > color_pixel_ratio_threshold
    except Exception as e:
        print(f"Error checking color for {image_path}: {e}")
        return False

def extract_zip_archive(zip_file_path: Path, output_dir: Path) -> List[Path]:
    """Safely extracts images from a ZIP archive and returns sorted image paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_images = []
    
    with zipfile.ZipFile(zip_file_path, 'r') as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            
            # Check for path traversal security
            if not is_safe_zip_path(output_dir, member.filename):
                raise ValueError(f"Dangerous path detected in ZIP: {member.filename}")
                
            filename = Path(member.filename).name
            ext = Path(filename).suffix.lower()
            if ext in ['.png', '.jpg', '.jpeg', '.webp']:
                target_path = output_dir / filename
                with archive.open(member) as source, open(target_path, 'wb') as dest:
                    shutil.copyfileobj(source, dest)
                extracted_images.append(target_path)
                
    extracted_images.sort(key=lambda p: natural_sort_key(p.name))
    return extracted_images

def extract_pdf_document(pdf_file_path: Path, output_dir: Path) -> List[Path]:
    """Extracts pages from a PDF document as high-resolution images preserving page order."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_images = []
    
    # Try pypdf / pypdfium / pdf2image if installed, or fallback to rasterizing images inside pdf
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(pdf_file_path))
        for i in range(len(pdf)):
            page = pdf[i]
            image = page.render(scale=2.0).to_pil()
            target_path = output_dir / f"page_{i+1:04d}.png"
            image.save(target_path, "PNG")
            extracted_images.append(target_path)
        return extracted_images
    except Exception:
        pass

    # Standard pypdf extraction fallback
    if PYPDF_AVAILABLE:
        try:
            reader = pypdf.PdfReader(str(pdf_file_path))
            page_idx = 1
            for page in reader.pages:
                for img_obj in page.images:
                    filename = f"page_{page_idx:04d}_{img_obj.name}"
                    target_path = output_dir / filename
                    with open(target_path, "wb") as fp:
                        fp.write(img_obj.data)
                    extracted_images.append(target_path)
                    page_idx += 1
            extracted_images.sort(key=lambda p: natural_sort_key(p.name))
            return extracted_images
        except Exception as e:
            print(f"pypdf extraction error: {e}")

    return extracted_images

def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    """Gets width and height of an image file."""
    with Image.open(image_path) as img:
        return img.width, img.height
