import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from ...config import settings
from ..preprocessing.screentone import remove_screentones
from ..preprocessing.lineart import blend_color_with_line_art
from ..preprocessing.layout import detect_speech_bubbles_and_text, protect_speech_bubbles
from ..character.palette_extractor import hex_to_bgr

class NeuralMangaColorizer:
    """
    State-of-the-Art Deep Neural Manga Colorization Engine.
    Uses dedicated convolutional manga colorizer weights (manga-colorize-fp16.onnx)
    specifically trained on thousands of black & white manga pages.
    
    Supports:
    - Zero-shot automatic manga colorization without stripes or banding.
    - Reference & character-hint guided colorization via CCMS character profiles.
    - Speech bubble and dialogue text protection.
    - Mangaka line art preservation.
    """
    _instance: Optional['NeuralMangaColorizer'] = None
    _session: Optional[ort.InferenceSession] = None
    _model_path: Optional[Path] = None

    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            model_path = settings.checkpoints_dir / "manga-colorize-fp16.onnx"
        self.model_path = model_path
        self._ensure_session()

    def _ensure_session(self):
        if self._session is None and self.model_path.exists():
            options = ort.SessionOptions()
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            options.intra_op_num_threads = 4
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            try:
                self._session = ort.InferenceSession(str(self.model_path), options, providers=providers)
            except Exception:
                self._session = ort.InferenceSession(str(self.model_path), options, providers=['CPUExecutionProvider'])

    def is_available(self) -> bool:
        return self.model_path.exists()

    def colorize(
        self,
        image_bgr: np.ndarray,
        character_profiles: List[Dict[str, Any]] = None,
        coloring_style: str = "vibrant_anime"
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        self._ensure_session()
        if self._session is None:
            raise RuntimeError("Manga colorizer neural network model is not available.")

        orig_h, orig_w = image_bgr.shape[:2]

        # 1. Clean screentones and isolate native luminance
        cleaned = remove_screentones(image_bgr, strength=1)
        gray_native = cv2.cvtColor(cleaned, cv2.COLOR_BGR2GRAY)

        # 2. Optimal Neural Processing Dimensions (Max 960 to prevent memory allocation spikes)
        max_dim = 960.0
        if max(orig_h, orig_w) > max_dim:
            scale = max_dim / float(max(orig_h, orig_w))
            proc_h = int(round(orig_h * scale / 32.0)) * 32
            proc_w = int(round(orig_w * scale / 32.0)) * 32
            gray_proc = cv2.resize(gray_native, (proc_w, proc_h), interpolation=cv2.INTER_AREA)
        else:
            pad_h = (32 - (orig_h % 32)) % 32
            pad_w = (32 - (orig_w % 32)) % 32
            proc_h = orig_h + pad_h
            proc_w = orig_w + pad_w
            if pad_h > 0 or pad_w > 0:
                gray_proc = cv2.copyMakeBorder(gray_native, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
            else:
                gray_proc = gray_native

        scale_y = proc_h / float(orig_h)
        scale_x = proc_w / float(orig_w)

        # Ch 0: Grayscale image normalized 0..1
        gray_tensor = (gray_proc.astype(np.float32) / 255.0)[np.newaxis, np.newaxis, :, :]

        # Ch 1-3: Color hints, Ch 4: Hint mask
        # We supply a clean canvas to prevent geometric circle blotching or bleeding
        hints = np.zeros((1, 3, proc_h, proc_w), dtype=np.float32)
        hint_mask = np.zeros((1, 1, proc_h, proc_w), dtype=np.float32)

        input_tensor = np.concatenate([gray_tensor, hints, hint_mask], axis=1)

        # 3. Neural inference
        output = self._session.run(['rgb'], {'input': input_tensor})[0]

        # 4. Convert RGB tensor [1, 3, H, W] to BGR uint8 and upsample to native manga resolution
        rgb_proc = np.clip(output[0] * 255.0, 0, 255).astype(np.uint8)
        rgb_proc = np.transpose(rgb_proc, (1, 2, 0))
        
        # High-fidelity Lanczos4 upsampling back to original dimensions
        rgb_full = cv2.resize(rgb_proc, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)
        bgr_full = cv2.cvtColor(rgb_full, cv2.COLOR_RGB2BGR)

        # 5. Semantic Cel-Shading & Flatting Harmonization
        # Combines the neural base with line-art flatting, character palette injection,
        # CIELAB luminance modulation, gutter whitening, and line-art preservation.
        from .semantic_cel import harmonize_semantic_cel_shading
        final_bgr, bubble_mask, report = harmonize_semantic_cel_shading(
            original_bgr=image_bgr,
            neural_bgr=bgr_full,
            character_profiles=character_profiles,
            coloring_style=coloring_style
        )

        return final_bgr, bubble_mask, report

neural_manga_colorizer = NeuralMangaColorizer()
