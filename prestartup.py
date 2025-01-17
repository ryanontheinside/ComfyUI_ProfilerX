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

logger = logging.getLogger('ComfyUI-ProfilerX')
logger.setLevel(logging.ERROR)
# Store original functions
original_execute = execution.execute
original_ExecutionList_init = execution.ExecutionList.__init__
original_PromptExecutor_execute = execution.PromptExecutor.execute

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

# Don't auto-inject on import anymore - let __init__.py control this 