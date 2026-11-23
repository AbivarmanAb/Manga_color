import os
import shutil
import psutil
import warnings
from typing import Dict, Any, Optional

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

def get_hardware_telemetry() -> Dict[str, Any]:
    """Retrieve comprehensive system, CPU, and NVIDIA GPU telemetry for the studio dashboard."""
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath("."))
    
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True)
    
    telemetry = {
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count
        },
        "ram": {
            "total_gb": round(ram.total / (1024 ** 3), 2),
            "used_gb": round(ram.used / (1024 ** 3), 2),
            "free_gb": round(ram.available / (1024 ** 3), 2),
            "percent": ram.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        },
        "gpu": {
            "available": False,
            "device_name": "No GPU detected (CPU Fallback)",
            "total_vram_mb": 0,
            "used_vram_mb": 0,
            "free_vram_mb": 0,
            "utilization_percent": 0,
            "cuda_version": "N/A",
            "device_count": 0
        }
    }
    
    if NVML_AVAILABLE:
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                total_mb = round(mem.total / (1024 ** 2), 1)
                used_mb = round(mem.used / (1024 ** 2), 1)
                free_mb = round(mem.free / (1024 ** 2), 1)
                
                telemetry["gpu"] = {
                    "available": True,
                    "device_name": str(name),
                    "total_vram_mb": total_mb,
                    "used_vram_mb": used_mb,
                    "free_vram_mb": free_mb,
                    "utilization_percent": util.gpu,
                    "device_count": device_count
                }
            pynvml.nvmlShutdown()
        except Exception as e:
            # Fallback to PyTorch telemetry if NVML error
            if TORCH_AVAILABLE and torch.cuda.is_available():
                try:
                    current_device = torch.cuda.current_device()
                    gpu_name = torch.cuda.get_device_name(current_device)
                    total_vram = torch.cuda.get_device_properties(current_device).total_memory / (1024 ** 2)
                    allocated_vram = torch.cuda.memory_allocated(current_device) / (1024 ** 2)
                    reserved_vram = torch.cuda.memory_reserved(current_device) / (1024 ** 2)
                    used_vram = max(allocated_vram, reserved_vram)
                    free_vram = max(0.0, total_vram - used_vram)
                    
                    telemetry["gpu"] = {
                        "available": True,
                        "device_name": gpu_name,
                        "total_vram_mb": round(total_vram, 1),
                        "used_vram_mb": round(used_vram, 1),
                        "free_vram_mb": round(free_vram, 1),
                        "utilization_percent": round((used_vram / total_vram) * 100, 1) if total_vram > 0 else 0,
                        "device_count": torch.cuda.device_count()
                    }
                except Exception:
                    pass
                    
    return telemetry

def clear_vram():
    """Aggressively release unallocated and cached PyTorch VRAM."""
    if TORCH_AVAILABLE and torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        except Exception:
            pass
