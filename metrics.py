"""Memory measurement utilities for ProfilerX"""
import psutil
import os

_process = psutil.Process(os.getpid())

def _has_cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False

def snapshot_memory():
    """Return (vram_bytes, ram_bytes) current allocation."""
    ram = _process.memory_info().rss
    if _has_cuda():
        import torch
        vram = torch.cuda.memory_allocated()
    else:
        vram = 0
    return vram, ram

def reset_peak():
    """Reset CUDA peak memory stats."""
    if _has_cuda():
        import torch
        torch.cuda.reset_peak_memory_stats()

def get_peak():
    """Return (vram_peak_bytes, ram_bytes). RAM peak is just current RSS (no true peak without sampling)."""
    ram = _process.memory_info().rss
    if _has_cuda():
        import torch
        vram = torch.cuda.max_memory_allocated()
    else:
        vram = 0
    return vram, ram
