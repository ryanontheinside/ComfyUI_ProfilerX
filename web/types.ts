// Type definitions for ProfilerX

export interface NodeProfile {
    nodeType: string;
    startTime: number;
    endTime: number;
    vramBefore: number;
    vramAfter: number;
    ramBefore: number;
    ramAfter: number;
    cacheHit: boolean;
}

export interface WorkflowProfile {
    startTime: number;
    endTime: number;
    nodes: Record<string, NodeProfile>;
    totalVramPeak: number;
    totalRamPeak: number;
    cacheHits: number;
    cacheMisses: number;
}

export interface ProfilerStats {
    latest: WorkflowProfile;
    history: WorkflowProfile[];
    node_averages: Record<string, {
        total_time: number;
        vram_usage: number;
        ram_usage: number;
        count: number;
        cache_hits: number;
    }>;
    workflow_averages: {
        total_time: number;
        vram_peak: number;
        ram_peak: number;
        count: number;
    };
}

export interface Archive {
    filename: string;
    created: number;
    size: number;
} 