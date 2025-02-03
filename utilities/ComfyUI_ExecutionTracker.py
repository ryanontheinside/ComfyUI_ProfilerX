"""
Dedicated execution tracking for ComfyUI using cProfile

Drop this into your custom nodes folder and restart ComfyUI. 
You may or may not need to disable ProfilerX to use this, as they may conflict with one another.

"""
import os
import sys
import cProfile
import logging
import threading
from pathlib import Path

# Add ComfyUI root to path
comfy_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if comfy_path not in sys.path:
    sys.path.append(comfy_path)

import execution

logger = logging.getLogger('ComfyUI-ExecutionTracker')
logger.setLevel(logging.ERROR)

class ExecutionTracker:
    """Tracks ComfyUI's internal method execution using cProfile"""
    _instance = None
    _lock = threading.Lock()
    ENABLED = True
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.profiler = None
        self._current_prompt_id = None

    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start_execution(self, prompt_id: str):
        """Start profiling a new execution"""
        if not self.ENABLED:
            return
            
        with self._lock:
            self._current_prompt_id = prompt_id
            self.profiler = cProfile.Profile()
            self.profiler.enable()

    def end_execution(self):
        """End profiling current execution"""
        if not self.ENABLED or not self.profiler:
            return
            
        with self._lock:
            self.profiler.disable()
            # Save as .prof file that snakeviz can read
            output_file = os.path.join(self.data_dir, f"execution_{self._current_prompt_id}.prof")
            self.profiler.dump_stats(output_file)
            self.profiler = None
            self._current_prompt_id = None

# Store original PromptExecutor.execute to wrap it with profiling
original_execute = execution.PromptExecutor.execute

def execute_with_profiling(self, prompt, prompt_id, extra_data={}, execute_outputs=[]):
    """Profile workflow execution"""
    tracker = ExecutionTracker.get_instance()
    tracker.start_execution(prompt_id)
    try:
        return original_execute(self, prompt, prompt_id, extra_data, execute_outputs)
    finally:
        tracker.end_execution()

def inject_tracking():
    """Inject profiling hook into PromptExecutor.execute"""
    logger.info("Verifying ComfyUI components...")
    try:
        if not hasattr(execution, 'PromptExecutor'):
            raise ImportError("Required ComfyUI components not found - incompatible ComfyUI version?")
        
        # Only need to wrap the main execute method
        execution.PromptExecutor.execute = execute_with_profiling
        
        logger.info("✓ Profiling hook injected successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to inject profiling hook: {str(e)}")
        logger.error("Execution tracking will be disabled for this session")
        return False

# Dummy node for ComfyUI
class ExecutionTrackerNode:
    """Dummy node to satisfy ComfyUI's node requirements"""
    
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    
    RETURN_TYPES = ()
    FUNCTION = "noop"
    OUTPUT_NODE = True
    CATEGORY = "profiling"

    def noop(self):
        return {}

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "ExecutionTracker": ExecutionTrackerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExecutionTracker": "Execution Tracker"
}

# Inject tracking on import if enabled
if ExecutionTracker.ENABLED:
    inject_tracking() 
