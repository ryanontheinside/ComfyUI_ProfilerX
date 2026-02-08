// Performance monitor UI component
import { debug } from '../utils/debug.js';
import { updateMenuStats } from '../utils/tabs.js';
export function createPerformanceMonitor() {
    debug("Creating performance monitor UI");
    const container = document.createElement('div');
    container.className = 'comfyui-button-wrapper';
    container.style.position = 'relative';
    const button = document.createElement('button');
    button.className = 'comfyui-button primary popup-closed';
    button.title = 'Profiling Stats';
    button.setAttribute('aria-label', 'Profiling Stats');
    // Create icon
    const icon = document.createElement('i');
    icon.className = 'mdi mdi-chart-line';
    button.appendChild(icon);
    button.appendChild(document.createTextNode(''));
    container.appendChild(button);
    // Create detailed stats popup
    const popup = document.createElement('div');
    popup.className = 'comfyui-popup profilerx-stats-popup';
    popup.style.cssText = `
        display: none;
        position: fixed;
        background: var(--comfy-input-bg);
        color: var(--descrip-text);
        padding: 8px;
        border-radius: 4px;
        z-index: 9999;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border: 1px solid var(--border-color);
        min-width: 400px;
        max-width: 600px;
        font-size: 12px;
    `;
    container.appendChild(popup);

    function positionPopup() {
        const rect = button.getBoundingClientRect();
        // Position below button, right-aligned to button's right edge
        const top = rect.bottom + 4;
        let left = rect.right - popup.offsetWidth;
        // Keep within viewport
        if (left < 8) left = 8;
        popup.style.top = top + 'px';
        popup.style.left = left + 'px';
    }

    // Toggle popup on click
    button.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const isVisible = popup.style.display !== 'none';
        if (!isVisible) {
            popup.style.display = 'block';
            positionPopup();
            popup.classList.add('open');
            updateMenuStats(popup);
        } else {
            popup.classList.remove('open');
            popup.style.display = 'none';
        }
        button.classList.toggle('popup-opened', !isVisible);
        button.classList.toggle('popup-closed', isVisible);
    });
    // Close popup when clicking outside
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            popup.style.display = 'none';
            popup.classList.remove('open');
            button.classList.remove('popup-opened');
            button.classList.add('popup-closed');
        }
    });
    return {
        container,
        elements: {
            button,
            popup
        }
    };
}
