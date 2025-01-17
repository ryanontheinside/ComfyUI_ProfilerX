/// <reference path="./comfyui.d.ts" />

import { NodeProfile, WorkflowProfile } from './types.js';
import { debug } from './utils/debug.js';
import { app } from './utils/api.js';
import { createPerformanceMonitor } from './ui/monitor.js';
import { updateTabContent } from './utils/tabs.js';

// Register the extension
app.registerExtension({
    name: "ComfyUI-ProfilerX",
    async setup() {
        debug("Setting up ProfilerX extension");
        
        // Create and add performance monitor to menu
        const menuContainer = document.querySelector('.comfyui-menu-right .flex.gap-2.mx-2');
        if (!menuContainer) {
            debug("Error: Could not find menu container");
            return;
        }
        debug("Found menu container");

        // Create a new button group for our stats
        let statsContainer = menuContainer.querySelector('.profilerx-stats-group') as HTMLElement;
        if (!statsContainer) {
            debug("Creating new stats container");
            statsContainer = document.createElement('div');
            statsContainer.className = 'comfyui-button-group profilerx-stats-group';
            
            // Insert after the first button group (usually rgthree)
            const firstGroup = menuContainer.querySelector('.comfyui-button-group');
            if (firstGroup) {
                debug("Adding after first button group");
                firstGroup.after(statsContainer);
            } else {
                debug("No existing groups, prepending to menu");
                menuContainer.prepend(statsContainer);
            }
        }

        // Create our monitor
        debug("Creating monitor UI");
        const { container } = createPerformanceMonitor();
        statsContainer.appendChild(container);
        debug("Monitor UI added to DOM");

        // Listen for workflow completion through ComfyUI's event system
        app.addEventListener("executed", () => {
            debug("Workflow executed, updating stats");
            const activeTab = document.querySelector('.profilerx-tab.active') as HTMLElement;
            if (activeTab?.dataset.tabId) {
                updateTabContent(activeTab.dataset.tabId);
            }
        });

        // Listen for history loaded event (used by archive loading)
        document.addEventListener('profiler:historyLoaded', () => {
            debug("History loaded, updating stats");
            const activeTab = document.querySelector('.profilerx-tab.active') as HTMLElement;
            if (activeTab?.dataset.tabId) {
                updateTabContent(activeTab.dataset.tabId);
            }
        });
    },
});

// Export types for other modules
export type {
    NodeProfile,
    WorkflowProfile
}; 