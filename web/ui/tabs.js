// Tab interface component
import { updateTabContent } from '../utils/tabs.js';
export function createTabbedInterface(popupElement) {
    const tabContainer = document.createElement('div');
    tabContainer.className = 'profilerx-tabs';
    tabContainer.style.cssText = `
        display: flex;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 8px;
    `;
    const tabs = [
        { id: 'latest', label: 'Latest Run', icon: '⚡' },
        { id: 'history', label: 'Historical Trends', icon: '📈' },
        { id: 'nodes', label: 'Node Analytics', icon: '🔍' },
        { id: 'settings', label: 'Settings', icon: '⚙️' }
    ];
    tabs.forEach(tab => {
        const tabButton = document.createElement('button');
        tabButton.className = 'profilerx-tab';
        tabButton.dataset.tabId = tab.id;
        tabButton.innerHTML = `${tab.icon} ${tab.label}`;
        tabButton.style.cssText = `
            padding: 8px 12px;
            background: none;
            border: none;
            color: var(--descrip-text);
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        tabButton.addEventListener('mouseenter', () => tabButton.style.opacity = '1');
        tabButton.addEventListener('mouseleave', () => {
            if (!tabButton.classList.contains('active')) {
                tabButton.style.opacity = '0.7';
            }
        });
        tabButton.addEventListener('click', () => switchTab(tab.id));
        tabContainer.appendChild(tabButton);
    });
    return tabContainer;
}
export function switchTab(tabId) {
    const tabs = document.querySelectorAll('.profilerx-tab');
    const activeTab = document.querySelector(`.profilerx-tab[data-tab-id="${tabId}"]`);
    tabs.forEach(tab => {
        const tabElement = tab;
        tabElement.classList.remove('active');
        tabElement.style.opacity = '0.7';
        tabElement.style.borderBottom = 'none';
    });
    if (activeTab) {
        activeTab.classList.add('active');
        activeTab.style.opacity = '1';
        activeTab.style.borderBottom = '2px solid var(--descrip-text)';
    }
    updateTabContent(tabId);
}
