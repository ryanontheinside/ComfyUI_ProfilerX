"""Server routes for the profiler extension"""
import json
from aiohttp import web
from server import PromptServer
from .profiler_core import ProfilerManager

@PromptServer.instance.routes.get('/profilerx/stats')
async def get_stats(request):
    """Get the current profiling stats"""
    profiler = ProfilerManager.get_instance()
    stats = profiler.get_stats()
    return web.json_response(stats if stats else {})

@PromptServer.instance.routes.get('/profilerx/archives')
async def get_archives(request):
    """Get list of archived history files"""
    profiler = ProfilerManager.get_instance()
    archives = profiler.get_archives()
    return web.json_response(archives)

@PromptServer.instance.routes.post('/profilerx/archive')
async def create_archive(request):
    """Create a new archive of current history"""
    profiler = ProfilerManager.get_instance()
    archive_name = profiler.archive_history()
    if archive_name:
        return web.json_response({"success": True, "archive": archive_name})
    return web.json_response({"success": False, "error": "Failed to create archive"}, status=500)

@PromptServer.instance.routes.post('/profilerx/archive/{filename}/load')
async def load_archive(request):
    """Load an archived history file"""
    filename = request.match_info['filename']
    profiler = ProfilerManager.get_instance()
    success = profiler.load_archive(filename)
    if success:
        return web.json_response({"success": True})
    return web.json_response({"success": False, "error": f"Failed to load archive: {filename}"}, status=400)

@PromptServer.instance.routes.delete('/profilerx/archive/{filename}')
async def delete_archive(request):
    """Delete an archived history file"""
    filename = request.match_info['filename']
    profiler = ProfilerManager.get_instance()
    success = profiler.delete_archive(filename)
    if success:
        return web.json_response({"success": True})
    return web.json_response({"success": False, "error": f"Failed to delete archive: {filename}"}, status=400) 