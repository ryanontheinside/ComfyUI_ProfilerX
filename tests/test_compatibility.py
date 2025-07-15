#!/usr/bin/env python3
"""Test script for ProfilerX memory manager compatibility"""

import sys
import os

def main():
    """Main test function"""
    # Add ComfyUI root to path
    comfy_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    if comfy_path not in sys.path:
        sys.path.insert(0, comfy_path)
    
    # Add ProfilerX directory to path so we can import utilities module
    profilerx_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if profilerx_path not in sys.path:
        sys.path.insert(0, profilerx_path)

    # Change to ComfyUI directory to ensure proper imports
    original_cwd = os.getcwd()
    os.chdir(comfy_path)

    try:
        # Test basic imports
        import torch
        print(f"✅ PyTorch {torch.__version__} imported successfully")
        
        # Test device detection
        print(f"CUDA available: {torch.cuda.is_available()}")
        print(f"MPS available: {torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False}")
        print(f"MPS built: {torch.backends.mps.is_built() if hasattr(torch.backends, 'mps') else False}")
        
        # Test our memory manager directly (without importing ProfilerX's __init__.py)
        try:
            # Import just the memory manager
            from utilities.memory_manager import get_memory_manager
            
            memory_manager = get_memory_manager()
            print(f"✅ Memory manager initialized successfully")
            print(f"Device type: {memory_manager.device_type}")
            print(f"Device name: {memory_manager.device_name}")
            
            # Test memory functions
            allocated = memory_manager.memory_allocated()
            max_allocated = memory_manager.max_memory_allocated()
            print(f"Memory allocated: {allocated:,} bytes")
            print(f"Max memory allocated: {max_allocated:,} bytes")
            
            # Test reset function (should not throw error)
            memory_manager.reset_peak_memory_stats()
            print("✅ Memory reset completed without errors")
            
            # Test memory info
            info = memory_manager.memory_info()
            print("Memory info:", info)
            
        except Exception as e:
            print(f"❌ Memory manager test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test basic tensor operations on detected device
        try:
            if memory_manager.device_type == 'mps':
                device = torch.device('mps')
                x = torch.randn(100, 100, device=device)
                y = torch.randn(100, 100, device=device)
                z = torch.mm(x, y)
                print(f"✅ MPS tensor operations work correctly")
            elif memory_manager.device_type == 'cuda':
                device = torch.device('cuda')
                x = torch.randn(100, 100, device=device)
                y = torch.randn(100, 100, device=device)
                z = torch.mm(x, y)
                print(f"✅ CUDA tensor operations work correctly")
            else:
                print("✅ CPU mode - skipping GPU tensor test")
                
        except Exception as e:
            print(f"⚠️  GPU tensor test failed: {e}")
        
        print("\n🎉 Memory manager tests passed! The CUDA compatibility fix should work.")
        print("\nNext steps:")
        print("1. Try running ComfyUI: python main.py --preview-method auto")
        print("2. If ProfilerX still causes issues, disable it: mv custom_nodes/ComfyUI_ProfilerX custom_nodes/ComfyUI_ProfilerX.disabled")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the ComfyUI directory with the virtual environment activated")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
