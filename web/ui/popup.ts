// Popup UI component for detailed stats display

import { debug } from '../utils/debug.js';

interface PopupElements {
    button: HTMLButtonElement;
    popup: HTMLDivElement;
}

export function createPopup(): { container: HTMLDivElement, elements: PopupElements } {
    const container = document.createElement('div');
    container.className = 'comfyui-button-wrapper';
    container.style.position = 'relative';
    
    const button = document.createElement('button');
    button.className = 'comfyui-button primary popup-closed';
    button.title = 'Profiling Stats';
    button.style.cssText = `
        background: var(--comfy-input-bg);
        &:hover {
            background: var(--comfy-input-bg);
            filter: brightness(1.2);
        }
    `;

    // Create icon
    const icon = document.createElement('i');
    icon.className = 'mdi mdi-chart-line';
    button.appendChild(icon);

    container.appendChild(button);

    // Create detailed stats popup with proper positioning
    const popup = document.createElement('div');
    popup.className = 'comfyui-popup profilerx-stats-popup left';
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
        min-width: 300px;
        font-size: 12px;
    `;
    container.appendChild(popup);

    setupPopupEvents(container, button, popup);

    return {
        container,
        elements: { button, popup }
    };
}

function setupPopupEvents(container: HTMLDivElement, button: HTMLButtonElement, popup: HTMLDivElement) {
    // Toggle popup on click
    button.addEventListener('click', (e) => {
        debug("Button clicked!");
        e.preventDefault();
        e.stopPropagation();
        const isVisible = popup.style.display !== 'none';
        debug("Current popup visibility:", popup.style.display, "isVisible:", isVisible);

        if (!isVisible) {
            // Position the popup relative to the button
            const rect = button.getBoundingClientRect();
            popup.style.setProperty('--left', `${rect.left}px`);
            popup.style.setProperty('--top', `${rect.bottom}px`);
            popup.style.setProperty('--limit', `${rect.bottom}px`);
            popup.classList.add('open');
            popup.style.display = 'block';
        } else {
            popup.classList.remove('open');
            popup.style.display = 'none';
        }

        debug("New popup display:", popup.style.display);
        button.classList.toggle('popup-opened', !isVisible);
        button.classList.toggle('popup-closed', isVisible);
        debug("Button classes after toggle:", button.className);
    });

    // Close popup when clicking outside
    document.addEventListener('click', (e) => {
        debug("Document clicked, checking if outside container");
        if (!container.contains(e.target as Node)) {
            debug("Click was outside container, closing popup");
            popup.style.display = 'none';
            popup.classList.remove('open');
            button.classList.remove('popup-opened');
            button.classList.add('popup-closed');
        } else {
            debug("Click was inside container");
        }
    });
} 