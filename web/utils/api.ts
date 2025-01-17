// ComfyUI API access utilities

// Access ComfyUI's app and api instances
export const app = (window as any).comfyAPI?.app?.app;
export const api = (window as any).comfyAPI?.api?.api;

// Fetch profiler stats from the API
export async function fetchProfilerStats() {
    return await api.fetchApi('/profilerx/stats').then((r: Response) => r.json());
} 