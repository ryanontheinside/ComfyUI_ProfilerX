"""Prestartup script to inject profiling hooks into ComfyUI's execution system"""
import logging
import sys
import os
import functools

# Add ComfyUI root to path
comfy_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
if comfy_path not in sys.path:
    sys.path.append(comfy_path)

import execution
import server
from .profiler_core import ProfilerManager
from .execution_core import ExecutionTracker

logger = logging.getLogger('ComfyUI-ProfilerX')
logger.setLevel(logging.ERROR)

# Store original functions
original_execute = execution.execute
original_ExecutionList_init = execution.ExecutionList.__init__
original_PromptExecutor_execute = execution.PromptExecutor.execute
original_PromptExecutor_init = execution.PromptExecutor.__init__
original_validate_prompt = execution.validate_prompt
original_validate_inputs = execution.validate_inputs
original_PromptQueue_put = execution.PromptQueue.put
original_PromptQueue_get = execution.PromptQueue.get
original_ExecutionList_stage_node_execution = execution.ExecutionList.stage_node_execution
original_ExecutionList_complete_node_execution = execution.ExecutionList.complete_node_execution
original_ExecutionList_unstage_node_execution = execution.ExecutionList.unstage_node_execution
original_ExecutionList_add_node = execution.ExecutionList.add_node
original_ExecutionList_add_strong_link = execution.ExecutionList.add_strong_link
original_ExecutionList_make_input_strong_link = execution.ExecutionList.make_input_strong_link
original_ExecutionList_is_empty = execution.ExecutionList.is_empty

# Global flag to track if profiler is enabled
PROFILER_ENABLED = False

def ExecutionList_init_with_profiling(self, *args, **kwargs):
    """Start profiling when a new execution begins"""
    original_ExecutionList_init(self, *args, **kwargs)

def PromptExecutor_execute_with_profiling(self, prompt, prompt_id, extra_data={}, execute_outputs=[]):
    """Start profiling when a new workflow begins"""
    if not PROFILER_ENABLED:
        return original_PromptExecutor_execute(self, prompt, prompt_id, extra_data, execute_outputs)
        
    logger.debug(f"Starting workflow profiling for new execution: {prompt_id}")
    profiler = ProfilerManager.get_instance()
    profiler.start_workflow(prompt_id)
    
    try:
        return original_PromptExecutor_execute(self, prompt, prompt_id, extra_data, execute_outputs)
    finally:
        logger.debug(f"Workflow complete, ending profiling for {prompt_id}")
        profiler.end_workflow(prompt_id)

def execute_with_profiling(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results):
    """Minimal wrapper around execute to collect profiling data"""
    if not PROFILER_ENABLED or not prompt_id:
        return original_execute(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

    try:
        node = dynprompt.get_node(current_item)
        node_id = dynprompt.get_real_node_id(current_item)
        node_type = node['class_type']
        inputs = node['inputs']
        logger.debug(f"Profiling node execution - id: {node_id}, type: {node_type}")
    except Exception as e:
        logger.error(f"Failed to get node info: {e}")
        return original_execute(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

    profiler = ProfilerManager.get_instance()
    try:
        # Start profiling this node
        profiler.start_node(prompt_id, node_id, node_type, inputs)
        cache_hit = caches.outputs.get(current_item) is not None
        logger.debug(f"Node {node_id} cache hit: {cache_hit}")

        # Execute node
        result = original_execute(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

        # End profiling
        outputs = caches.outputs.get(current_item)
        if outputs is None:
            outputs = {}
        profiler.end_node(prompt_id, node_id, outputs, cache_hit)

        return result

    except Exception as e:
        logger.error(f"Error during node execution: {e}")
        profiler.record_error(prompt_id, node_id, str(e))
        # Don't re-raise - let ComfyUI handle the error
        return original_execute(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

def inject_profiling():
    """Inject minimal profiling hook"""
    global PROFILER_ENABLED
    
    logger.info("Attempting to inject profiling hooks...")
    try:
        # Verify we can access all required ComfyUI internals
        if not hasattr(execution, 'execute') or not hasattr(execution, 'ExecutionList') or not hasattr(execution, 'PromptExecutor'):
            raise ImportError("Required ComfyUI execution components not found - incompatible ComfyUI version?")

        # Store originals and inject our wrapped versions
        execution.execute = execute_with_profiling
        execution.ExecutionList.__init__ = ExecutionList_init_with_profiling 
        execution.PromptExecutor.execute = PromptExecutor_execute_with_profiling
        
        PROFILER_ENABLED = True
        logger.info("✓ Profiling hooks injected successfully")
        return True
        
    except Exception as e:
        PROFILER_ENABLED = False
        logger.error(f"❌ Failed to inject profiling hooks: {str(e)}")
        logger.error("The profiler will be disabled for this session")
        return False

# Execution tracking functions
def ExecutionList_init_with_tracking(self, *args, **kwargs):
    """Track ExecutionList initialization"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("__init__", "ExecutionList")(original_ExecutionList_init)(self, *args, **kwargs)

def PromptExecutor_init_with_tracking(self, *args, **kwargs):
    """Track PromptExecutor initialization"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("__init__", "PromptExecutor")(original_PromptExecutor_init)(self, *args, **kwargs)

def execute_with_tracking(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results):
    """Track node execution while preserving profiling"""
    # First apply execution tracking
    tracker = ExecutionTracker.get_instance()
    tracked_func = tracker.track_method_call("execute")(original_execute)
    
    # Then apply profiling wrapper
    if not PROFILER_ENABLED or not prompt_id:
        return tracked_func(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

    try:
        node = dynprompt.get_node(current_item)
        node_id = dynprompt.get_real_node_id(current_item)
        node_type = node['class_type']
        inputs = node['inputs']
        logger.debug(f"Profiling node execution - id: {node_id}, type: {node_type}")
    except Exception as e:
        logger.error(f"Failed to get node info: {e}")
        return tracked_func(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

    profiler = ProfilerManager.get_instance()
    try:
        # Start profiling this node
        profiler.start_node(prompt_id, node_id, node_type, inputs)
        cache_hit = caches.outputs.get(current_item) is not None
        logger.debug(f"Node {node_id} cache hit: {cache_hit}")

        # Execute node with tracking
        result = tracked_func(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

        # End profiling
        outputs = caches.outputs.get(current_item)
        if outputs is None:
            outputs = {}
        profiler.end_node(prompt_id, node_id, outputs, cache_hit)

        return result

    except Exception as e:
        logger.error(f"Error during node execution: {e}")
        profiler.record_error(prompt_id, node_id, str(e))
        # Don't re-raise - let ComfyUI handle the error
        return tracked_func(server, dynprompt, caches, current_item, extra_data, executed, prompt_id, execution_list, pending_subgraph_results)

def PromptExecutor_execute_with_tracking(self, prompt, prompt_id, extra_data={}, execute_outputs=[]):
    """Track workflow execution while preserving profiling"""
    # First apply execution tracking
    tracker = ExecutionTracker.get_instance()
    tracker.start_execution(prompt_id)
    tracked_func = tracker.track_method_call("execute", "PromptExecutor")(original_PromptExecutor_execute)
    
    # Then apply profiling wrapper
    if not PROFILER_ENABLED:
        try:
            return tracked_func(self, prompt, prompt_id, extra_data, execute_outputs)
        finally:
            tracker.end_execution()
            
    logger.debug(f"Starting workflow profiling for new execution: {prompt_id}")
    profiler = ProfilerManager.get_instance()
    profiler.start_workflow(prompt_id)
    
    try:
        return tracked_func(self, prompt, prompt_id, extra_data, execute_outputs)
    finally:
        logger.debug(f"Workflow complete, ending profiling for {prompt_id}")
        profiler.end_workflow(prompt_id)
        tracker.end_execution()

def validate_prompt_with_tracking(prompt):
    """Track prompt validation"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("validate_prompt")(original_validate_prompt)(prompt)

def validate_inputs_with_tracking(prompt, item, validated):
    """Track input validation"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("validate_inputs")(original_validate_inputs)(prompt, item, validated)

def inject_tracking():
    """Inject execution tracking hooks"""
    logger.info("Attempting to inject execution tracking hooks...")
    try:
        # Verify we can access all required ComfyUI internals
        if not hasattr(execution, 'execute') or not hasattr(execution, 'ExecutionList') or not hasattr(execution, 'PromptExecutor'):
            raise ImportError("Required ComfyUI execution components not found - incompatible ComfyUI version?")

        # Store originals and inject our wrapped versions that preserve profiling
        execution.execute = execute_with_tracking
        execution.PromptExecutor.execute = PromptExecutor_execute_with_tracking
        
        # These don't conflict with profiling so can be wrapped directly
        execution.ExecutionList.__init__ = ExecutionList_init_with_tracking
        execution.PromptExecutor.__init__ = PromptExecutor_init_with_tracking
        execution.validate_prompt = validate_prompt_with_tracking
        execution.validate_inputs = validate_inputs_with_tracking
        
        # Add queue tracking
        execution.PromptQueue.put = PromptQueue_put_with_tracking
        execution.PromptQueue.get = PromptQueue_get_with_tracking
        
        # Add new ExecutionList method tracking
        execution.ExecutionList.stage_node_execution = ExecutionList_stage_node_execution_with_tracking
        execution.ExecutionList.complete_node_execution = ExecutionList_complete_node_execution_with_tracking
        execution.ExecutionList.unstage_node_execution = ExecutionList_unstage_node_execution_with_tracking
        execution.ExecutionList.add_node = ExecutionList_add_node_with_tracking
        execution.ExecutionList.add_strong_link = ExecutionList_add_strong_link_with_tracking
        execution.ExecutionList.make_input_strong_link = ExecutionList_make_input_strong_link_with_tracking
        execution.ExecutionList.is_empty = ExecutionList_is_empty_with_tracking
        
        # Enable tracking
        ExecutionTracker.enable()
        logger.info("✓ Execution tracking hooks injected successfully")
        return True
        
    except Exception as e:
        ExecutionTracker.disable()
        logger.error(f"❌ Failed to inject execution tracking hooks: {str(e)}")
        logger.error("Execution tracking will be disabled for this session")
        return False

def PromptQueue_put_with_tracking(self, item):
    """Track when items are added to queue"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("put", "PromptQueue")(original_PromptQueue_put)(self, item)

def PromptQueue_get_with_tracking(self, timeout=None):
    """Track when items are retrieved from queue"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("get", "PromptQueue")(original_PromptQueue_get)(self, timeout)

# Add new tracking functions
def ExecutionList_stage_node_execution_with_tracking(self):
    """Track node staging"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("stage_node_execution", "ExecutionList")(original_ExecutionList_stage_node_execution)(self)

def ExecutionList_complete_node_execution_with_tracking(self):
    """Track node completion"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("complete_node_execution", "ExecutionList")(original_ExecutionList_complete_node_execution)(self)

def ExecutionList_unstage_node_execution_with_tracking(self):
    """Track node unstaging"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("unstage_node_execution", "ExecutionList")(original_ExecutionList_unstage_node_execution)(self)

def ExecutionList_add_node_with_tracking(self, node_id):
    """Track node addition"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("add_node", "ExecutionList")(original_ExecutionList_add_node)(self, node_id)

def ExecutionList_add_strong_link_with_tracking(self, from_node_id, from_socket, to_node_id):
    """Track link addition"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("add_strong_link", "ExecutionList")(original_ExecutionList_add_strong_link)(self, from_node_id, from_socket, to_node_id)

def ExecutionList_make_input_strong_link_with_tracking(self, node_id, input_name):
    """Track input link creation"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("make_input_strong_link", "ExecutionList")(original_ExecutionList_make_input_strong_link)(self, node_id, input_name)

def ExecutionList_is_empty_with_tracking(self):
    """Track execution list empty checks"""
    tracker = ExecutionTracker.get_instance()
    return tracker.track_method_call("is_empty", "ExecutionList")(original_ExecutionList_is_empty)(self)

# Don't auto-inject on import anymore - let __init__.py control this 