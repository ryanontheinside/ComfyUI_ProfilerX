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