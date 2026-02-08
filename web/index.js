/// <reference path="./comfyui.d.ts" />
import { debug } from './utils/debug.js';
import { app, api } from './utils/api.js';
import { createPerformanceMonitor } from './ui/monitor.js';
import { updateTabContent } from './utils/tabs.js';
// Register the extension
app.registerExtension({
    name: "ComfyUI-ProfilerX",
    async setup() {
        debug("Setting up ProfilerX extension");
        // Create our monitor button + popup
        const { container } = createPerformanceMonitor();
        // Wrap in a toolbar group so it matches ComfyUI's menu styling
        const wrapper = document.createElement('div');
        wrapper.className = 'comfyui-button-group profilerx-stats-group';
        wrapper.appendChild(container);
        // Insert before the settings group in the top menu bar (modern API)
        if (app.menu?.settingsGroup?.element) {
            app.menu.settingsGroup.element.before(wrapper);
            debug("Inserted ProfilerX button before settings group");
        } else {
            // Fallback: append to body as floating button
            debug("Warning: Could not find menu settingsGroup, using fallback");
            wrapper.style.cssText = 'position:fixed;top:8px;right:80px;z-index:9999;';
            document.body.appendChild(wrapper);
        }
        // Listen for workflow completion through ComfyUI's event system
        // Use api.addEventListener (not app) — this is the correct modern API
        api.addEventListener("executed", () => {
            debug("Node executed event received, updating stats");
            const activeTab = document.querySelector('.profilerx-tab.active');
            if (activeTab?.dataset.tabId) {
                updateTabContent(activeTab.dataset.tabId);
            }
        });
        // Listen for history loaded event (used by archive loading)
        document.addEventListener('profiler:historyLoaded', () => {
            debug("History loaded, updating stats");
            const activeTab = document.querySelector('.profilerx-tab.active');
            if (activeTab?.dataset.tabId) {
                updateTabContent(activeTab.dataset.tabId);
            }
        });
    },
});
