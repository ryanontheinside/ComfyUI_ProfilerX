"""Cross-platform memory management for ProfilerX"""
import torch
import platform
import logging

logger = logging.getLogger('ComfyUI-ProfilerX')

class MemoryManager:
    """Cross-platform memory management for CUDA, MPS, and CPU"""
    
    def __init__(self):
        self.device_type = self._detect_device()
        self.device_name = self._get_device_name()
        logger.debug(f"Detected device: {self.device_type} - {self.device_name}")
    
    def _detect_device(self):
        """Detect the available device type"""
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        else:
            return 'cpu'
    
    def _get_device_name(self):
        """Get device name across platforms"""
        if self.device_type == 'cuda':
            return torch.cuda.get_device_name()
        elif self.device_type == 'mps':
            return f"Apple Silicon GPU (MPS) - {platform.machine()}"
        else:
            return f"CPU - {platform.processor()}"
    
    def memory_allocated(self):
        """Get currently allocated memory"""
        if self.device_type == 'cuda':
            return torch.cuda.memory_allocated()
        elif self.device_type == 'mps':
            # MPS memory functions available in newer PyTorch versions
            if hasattr(torch.mps, 'current_allocated_memory'):
                return torch.mps.current_allocated_memory()
            else:
                # Fallback: return 0 for older PyTorch versions
                return 0
        else:
            return 0
    
    def max_memory_allocated(self):
        """Get peak allocated memory"""
        if self.device_type == 'cuda':
            return torch.cuda.max_memory_allocated()
        elif self.device_type == 'mps':
            # MPS doesn't have max_memory_allocated, so we track it manually
            if hasattr(self, '_mps_peak_memory'):
                return self._mps_peak_memory
            else:
                return self.memory_allocated()
        else:
            return 0
    
    def reset_peak_memory_stats(self):
        """Reset peak memory statistics"""
        if self.device_type == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        elif self.device_type == 'mps':
            # MPS doesn't have reset_peak_memory_stats
            # We simulate it by storing current memory as baseline
            self._mps_peak_memory = self.memory_allocated()
        # CPU doesn't need memory stats reset
    
    def empty_cache(self):
        """Empty memory cache"""
        if self.device_type == 'cuda':
            torch.cuda.empty_cache()
        elif self.device_type == 'mps':
            if hasattr(torch.mps, 'empty_cache'):
                torch.mps.empty_cache()
        # CPU doesn't have cache to empty
    
    def memory_info(self):
        """Get memory information"""
        if self.device_type == 'cuda':
            return {
                'allocated': self.memory_allocated(),
                'max_allocated': self.max_memory_allocated(),
                'device_name': self.device_name,
                'device_type': self.device_type
            }
        elif self.device_type == 'mps':
            return {
                'allocated': self.memory_allocated(),
                'max_allocated': self.max_memory_allocated(),
                'device_name': self.device_name,
                'device_type': self.device_type
            }
        else:
            return {
                'allocated': 0,
                'max_allocated': 0,
                'device_name': self.device_name,
                'device_type': self.device_type
            }

# Global instance
_memory_manager = None

def get_memory_manager():
    """Get the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
