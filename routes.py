"""REST API endpoints for ProfilerX"""
from aiohttp import web
from server import PromptServer
from .storage import StorageManager


def register_routes(storage, handler=None):
    routes = PromptServer.instance.routes

    @routes.get('/profilerx/stats')
    async def get_stats(request):
        # Flush any in-progress run data before returning stats
        if handler is not None:
            handler.flush()
        stats = storage.get_stats()
        return web.json_response(stats if stats else {})

    @routes.get('/profilerx/archives')
    async def get_archives(request):
        return web.json_response(storage.get_archives())

    @routes.post('/profilerx/archive')
    async def create_archive(request):
        name = storage.archive_history()
        if name:
            return web.json_response({"success": True, "archive": name})
        return web.json_response({"success": False, "error": "Failed to create archive"}, status=500)

    @routes.post('/profilerx/archive/{filename}/load')
    async def load_archive(request):
        filename = request.match_info['filename']
        if storage.load_archive(filename):
            return web.json_response({"success": True})
        return web.json_response({"success": False, "error": f"Failed to load archive: {filename}"}, status=400)

    @routes.delete('/profilerx/archive/{filename}')
    async def delete_archive(request):
        filename = request.match_info['filename']
        if storage.delete_archive(filename):
            return web.json_response({"success": True})
        return web.json_response({"success": False, "error": f"Failed to delete archive: {filename}"}, status=400)
