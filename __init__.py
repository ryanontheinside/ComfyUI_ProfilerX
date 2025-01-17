"""Profiler extension for ComfyUI"""
import os
import logging

# Configure logging before imports
logger = logging.getLogger('ComfyUI-ProfilerX')
logger.setLevel(logging.ERROR)  # Set to DEBUG level for maximum info

# Add console handler if not already added
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # Also set handler to DEBUG
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

logger.info("Initializing ComfyUI-ProfilerX...")

from .prestartup import inject_profiling, PROFILER_ENABLED  # Import but don't auto-inject
from . import server  # Register API routes

# Set up web directory
WEB_DIRECTORY = "./web"

# Try to inject profiling hooks
if not inject_profiling():
    # If injection fails, remove the profiler node from available nodes
    logger.warning("Disabling profiler nodes due to initialization failure")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
else:
    logger.info("ProfilerX initialization complete - profiler is enabled")
    # Add empty mappings to satisfy ComfyUI's import check
    NODE_CLASS_MAPPINGS = {
        "ProfilerX": type("ProfilerX", (), {
            "CATEGORY": "profiling",
            "RETURN_TYPES": tuple(),
            "FUNCTION": "noop",
            "OUTPUT_NODE": True,
            "INPUT_TYPES": lambda: {"required": {}}
        })
    }
    NODE_DISPLAY_NAME_MAPPINGS = {
        "ProfilerX": "ProfilerX"
    }

def setup_js():
    """Register web extension with profiler status"""
    logger.debug(f"Setting up web extension (enabled={PROFILER_ENABLED})")
    return {
        "name": "ComfyUI-ProfilerX",
        "module": "index.js",
        "enabled": PROFILER_ENABLED,
        "status": "active" if PROFILER_ENABLED else "disabled"
    }