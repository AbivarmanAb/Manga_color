import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np

class ComfyUIClient:
    """
    Bridge client to local ComfyUI instance (http://127.0.0.1:8188).
    Enables deep generative ControlNet LineArt / Manga Colorization workflows
    using local RTX 5060 GPU acceleration.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.base_url = f"http://{host}:{port}"

    def is_alive(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/system_stats", headers={'User-Agent': 'MangaStudio'})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_system_stats(self) -> Dict[str, Any]:
        if not self.is_alive():
            return {"status": "offline", "url": self.base_url}
        try:
            req = urllib.request.Request(f"{self.base_url}/system_stats", headers={'User-Agent': 'MangaStudio'})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            return {"status": "error", "error": str(e)}

comfy_client = ComfyUIClient()
