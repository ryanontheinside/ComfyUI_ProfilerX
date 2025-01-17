// ComfyUI app module
declare module "../../scripts/app.js" {
    interface Node {
        onDrawBackground?(ctx: CanvasRenderingContext2D): void;
        widgets_start_y: number;
        setSize(size: [number, number]): void;
        addWidget(type: string, name: string, value: string, options: {
            getValue(): string;
            setValue(value: string): void;
            content: HTMLElement;
        }): void;
    }

    interface NodeDef {
        name: string;
        category: string;
        output: number;
        input: number;
        onNodeCreated?(node: Node): void;
    }

    interface App {
        registerExtension(extension: {
            name: string;
            setup(): Promise<void>;
        }): void;
        registerNodeDef(type: string, def: NodeDef): void;
    }

    export const app: App;
}

// Our internal modules
declare module "./utils" {
    export function createStyleSheet(id: string): HTMLStyleElement;
    export function formatBytes(bytes: number, decimals?: number): string;
    export function formatDuration(ms: number): string;
}

declare module "./types" {
    export interface NodeProfile {
        nodeId: string;
        nodeType: string;
        startTime: number;
        endTime: number;
        vramBefore: number;
        vramAfter: number;
        ramBefore: number;
        ramAfter: number;
        inputSizes: Record<string, number>;
        outputSizes: Record<string, number>;
        cacheHit: boolean;
        error?: string;
    }

    export interface WorkflowProfile {
        promptId: string;
        startTime: number;
        endTime: number;
        nodes: Record<string, NodeProfile>;
        executionOrder: string[];
        totalVramPeak: number;
        totalRamPeak: number;
        cacheHits: number;
        cacheMisses: number;
    }

    export interface WorkflowSummary {
        totalTime: number;
        nodeCount: number;
        avgNodeTime: number;
        maxNodeTime: number;
        cacheHitRatio: number;
        peakVram: number;
        peakRam: number;
    }

    export interface ChartData {
        labels: string[];
        datasets: {
            label: string;
            data: number[];
            borderColor?: string;
            backgroundColor?: string;
        }[];
    }

    export interface ProfilerSettings {
        showMemoryChart: boolean;
        showTimeChart: boolean;
        showCacheStats: boolean;
        refreshRate: number;
        maxDataPoints: number;
        chartHeight: number;
        chartWidth: number;
    }

    export interface ProfilerUIComponent {
        container: HTMLElement;
        settings: ProfilerSettings;
        render(): void;
        update(data: WorkflowProfile): void;
        destroy(): void;
    }
} 