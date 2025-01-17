declare const app: {
    registerExtension(extension: {
        name: string;
        setup(): Promise<void>;
    }): void;
};

declare const api: {
    fetchApi(path: string): Promise<Response>;
};

interface ComfyNode {
    id: number;
    type: string;
    pos: [number, number];
    size: [number, number];
    flags: Record<string, boolean>;
    properties: Record<string, any>;
    widgets_values: any[];
}

interface ComfyWorkflow {
    nodes: ComfyNode[];
    links: any[];
    groups: any[];
    config: Record<string, any>;
    extra: Record<string, any>;
} 