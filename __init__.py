"""Profiler extension for ComfyUI"""
import os
import logging

from .prestartup import inject_profiling, PROFILER_ENABLED  # Import but don't auto-inject
from . import server  # Register API routes

logger = logging.getLogger('ComfyUI-ProfilerX')
logger.setLevel(logging.ERROR)

# Set up web directory
WEB_DIRECTORY = "./web"

# Try to inject profiling hooks
if not inject_profiling():
    # If injection fails, remove the profiler node from available nodes
    logger.warning("Disabling profiler nodes due to initialization failure")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}


def setup_js():
    """Register web extension with profiler status"""
    return {
        "name": "ComfyUI-ProfilerX",
        "module": "index.js",
        "enabled": PROFILER_ENABLED,
        "status": "active" if PROFILER_ENABLED else "disabled"
    } 