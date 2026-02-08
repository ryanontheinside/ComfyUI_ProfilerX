"""Memory measurement utilities for ProfilerX — supports CUDA, MPS, and CPU-only."""
import psutil
import os

_process = psutil.Process(os.getpid())

# Detect GPU backend once at import time
_GPU_BACKEND = None  # 'cuda', 'mps', or None
try:
    import torch
    if torch.cuda.is_available():
        _GPU_BACKEND = 'cuda'
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        _GPU_BACKEND = 'mps'
except Exception:
    pass


def snapshot_memory():
    """Return (vram_bytes, ram_bytes) current allocation."""
    ram = _process.memory_info().rss
    vram = 0
    try:
        if _GPU_BACKEND == 'cuda':
            import torch
            vram = torch.cuda.memory_allocated()
        elif _GPU_BACKEND == 'mps':
            import torch
            vram = torch.mps.current_allocated_memory()
    except Exception:
        pass
    return vram, ram


def reset_peak():
    """Reset peak memory stats for the active GPU backend."""
    try:
        if _GPU_BACKEND == 'cuda':
            import torch
            torch.cuda.reset_peak_memory_stats()
        elif _GPU_BACKEND == 'mps':
            # MPS has no peak reset API; this is a no-op.
            pass
    except Exception:
        pass


def get_peak():
    """Return (vram_peak_bytes, ram_bytes). RAM peak is just current RSS."""
    ram = _process.memory_info().rss
    vram = 0
    try:
        if _GPU_BACKEND == 'cuda':
            import torch
            vram = torch.cuda.max_memory_allocated()
        elif _GPU_BACKEND == 'mps':
            # MPS has no peak tracking; return current allocation as best estimate.
            import torch
            vram = torch.mps.current_allocated_memory()
    except Exception:
        pass
    return vram, ram
