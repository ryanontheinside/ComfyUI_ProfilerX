"""Core execution tracking for ComfyUI's internal methods"""
import logging
import time
import json
import os
import threading
from typing import Dict, List, Optional
from collections import defaultdict
import functools

logger = logging.getLogger('ComfyUI-ExecutionTracker')
logger.setLevel(logging.ERROR)

class ExecutionTracker:
    _instance = None
    _lock = threading.Lock()
    ENABLED = False #this is a global variable that controls whether the execution tracker is enabled or not
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.trace_file = os.path.join(self.data_dir, "method_traces.json")
        
        # Load existing traces if any
        self.traces = self._load_traces()
        
        # Track current execution
        self.call_stack = []
        self.current_execution = None

    def _load_traces(self) -> Dict:
        """Load existing traces from file"""
        if os.path.exists(self.trace_file):
            try:
                with open(self.trace_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load traces: {e}")
        return {
            "executions": [],
            "method_stats": defaultdict(lambda: {
                "total_calls": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "avg_time": 0
            })
        }

    def _save_traces(self):
        """Save traces to file"""
        try:
            with open(self.trace_file, 'w') as f:
                # Convert defaultdict to regular dict for JSON serialization
                traces_copy = {
                    "executions": self.traces["executions"],
                    "method_stats": {
                        k: dict(v) for k, v in self.traces["method_stats"].items()
                    }
                }
                json.dump(traces_copy, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save traces: {e}")

    @classmethod
    def get_instance(cls) -> 'ExecutionTracker':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def enable(cls):
        """Enable execution tracking"""
        cls.ENABLED = True
        logger.info("ComfyUI method call tracking enabled")

    @classmethod
    def disable(cls):
        """Disable execution tracking"""
        cls.ENABLED = False
        logger.info("ComfyUI method call tracking disabled")

    def start_execution(self, prompt_id: str):
        """Start tracking a new execution"""
        if not self.ENABLED:
            return
            
        with self._lock:
            self.current_execution = {
                "prompt_id": prompt_id,
                "start_time": time.time() * 1000,
                "method_calls": [],
                "total_time": 0
            }

    def end_execution(self):
        """End tracking current execution"""
        if not self.ENABLED or not self.current_execution:
            return
            
        with self._lock:
            self.current_execution["end_time"] = time.time() * 1000
            self.current_execution["total_time"] = (
                self.current_execution["end_time"] - self.current_execution["start_time"]
            )
            self.traces["executions"].append(self.current_execution)
            self._save_traces()
            self.current_execution = None

    def track_method_call(self, method_name: str, class_name: str = None):
        """Decorator to track method execution time"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.ENABLED:
                    return func(*args, **kwargs)

                full_name = f"{class_name}.{method_name}" if class_name else method_name
                start_time = time.time() * 1000

                try:
                    with self._lock:
                        self.call_stack.append(full_name)
                    
                    result = func(*args, **kwargs)
                    
                    return result
                finally:
                    end_time = time.time() * 1000
                    duration = end_time - start_time
                    
                    with self._lock:
                        # Pop from call stack
                        if self.call_stack:
                            self.call_stack.pop()
                        
                        # Update method stats
                        stats = self.traces["method_stats"][full_name]
                        stats["total_calls"] += 1
                        stats["total_time"] += duration
                        stats["min_time"] = min(stats.get("min_time", float('inf')), duration)
                        stats["max_time"] = max(stats.get("max_time", 0), duration)
                        stats["avg_time"] = stats["total_time"] / stats["total_calls"]
                        
                        # Record call in current execution with enhanced context
                        if self.current_execution:
                            # Get queue size if available
                            queue_size = None
                            try:
                                import execution
                                if hasattr(execution, 'PromptServer') and hasattr(execution.PromptServer.instance, 'prompt_queue'):
                                    queue = execution.PromptServer.instance.prompt_queue.queue
                                    queue_size = len(queue) if queue else 0
                            except:
                                pass

                            # Determine if operation was cached
                            is_cache_hit = False
                            if 'caches' in kwargs and 'current_item' in kwargs:
                                try:
                                    is_cache_hit = kwargs['caches'].outputs.get(kwargs['current_item']) is not None
                                except:
                                    pass

                            call_info = {
                                "method": full_name,
                                "start_time": start_time,
                                "duration": duration,
                                "stack_depth": len(self.call_stack) + 1,  # +1 since we already popped
                                "parent": self.call_stack[-1] if self.call_stack else None,
                                "queue_size": queue_size,
                                "is_cache_hit": is_cache_hit
                            }
                            self.current_execution["method_calls"].append(call_info)
            return wrapper
        return decorator

    def get_method_stats(self) -> Dict:
        """Get statistics for all tracked methods"""
        return dict(self.traces["method_stats"]) if self.ENABLED else {} 