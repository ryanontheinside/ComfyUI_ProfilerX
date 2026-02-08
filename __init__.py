"""ComfyUI_ProfilerX — workflow profiling via ProgressHandler API"""
import logging

logger = logging.getLogger('ComfyUI-ProfilerX')

from comfy_execution import progress
import execution
from .handler import ProfilerXProgressHandler
from .storage import StorageManager
from .routes import register_routes

# Initialize storage and handler
storage = StorageManager()
handler = ProfilerXProgressHandler(storage)

# Patch reset_progress_state to re-inject our handler after each reset.
# This is the only monkey-patch needed: ComfyUI creates a fresh ProgressRegistry
# on every execution, which blows away all handlers. We re-add ours each time.
_original_reset = progress.reset_progress_state

def _patched_reset(prompt_id, dynprompt):
    _original_reset(prompt_id, dynprompt)
    progress.add_progress_handler(handler)

# Patch both the module-level function and the imported reference in execution.py
progress.reset_progress_state = _patched_reset
execution.reset_progress_state = _patched_reset

# Register REST API routes
register_routes(storage, handler)

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
