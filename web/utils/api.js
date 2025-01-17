// ComfyUI API access utilities
// Access ComfyUI's app and api instances
export const app = window.comfyAPI?.app?.app;
export const api = window.comfyAPI?.api?.api;
// Fetch profiler stats from the API
export async function fetchProfilerStats() {
    return await api.fetchApi('/profilerx/stats').then((r) => r.json());
}
