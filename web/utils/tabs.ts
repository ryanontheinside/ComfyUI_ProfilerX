// Tab content management utilities
import { api } from './api.js';
import { debug } from './debug.js';
import { createTabbedInterface } from '../ui/tabs.js';
import { showLatestRun } from '../views/latest.js';
import { showHistoricalTrends } from '../views/history.js';
import { showNodeAnalytics } from '../views/analytics.js';
import { showSettings } from '../views/settings.js';

export async function updateTabContent(tabId: string) {
    interface ProfilerStats {
        latest: any;
        history: any[];
        node_averages: Record<string, any>;
        workflow_averages: any;
    }

    const contentElement = document.querySelector('.profilerx-content') as HTMLElement;
    if (!contentElement) return;

    try {
        // Try up to 3 times with increasing delays
        let stats: ProfilerStats | null = null;
        for (let i = 0; i < 3; i++) {
            try {
                const response = await api.fetchApi('/profilerx/stats');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                stats = await response.json();
                break;
            } catch (error) {
                debug(`Attempt ${i + 1} failed to fetch stats:`, error);
                if (i < 2) {
                    await new Promise(resolve => setTimeout(resolve, 100 * Math.pow(2, i)));
                    continue;
                }
                throw error;
            }
        }

        if (!stats) {
            throw new Error('Failed to fetch stats after retries');
        }
    
        switch (tabId) {
            case 'latest':
                showLatestRun(contentElement, stats);
                break;
            case 'history':
                showHistoricalTrends(contentElement, stats);
                break;
            case 'nodes':
                showNodeAnalytics(contentElement, stats);
                break;
            case 'settings':
                showSettings(contentElement);
                break;
        }
    } catch (error) {
        debug('Error updating tab content:', error);
        contentElement.innerHTML = '<div style="padding: 20px; text-align: center;">Failed to load content. Please try refreshing.</div>';
    }
}

export function updateMenuStats(popupElement: HTMLElement) {
    debug("Updating menu stats with profile");
    if (!popupElement) {
        debug("Warning: No popup element provided");
        return;
    }

    // Only set up the tabs if they don't exist
    if (!popupElement.querySelector('.profilerx-tabs')) {
        // Add tabs
        const tabContainer = createTabbedInterface(popupElement);
        popupElement.appendChild(tabContainer);
        
        // Add content container
        const contentContainer = document.createElement('div');
        contentContainer.className = 'profilerx-content';
        popupElement.appendChild(contentContainer);
        
        // Show latest run by default
        updateTabContent('latest');
    } else {
        // Just update the current tab's content
        const activeTab = popupElement.querySelector('.profilerx-tab.active') as HTMLElement;
        if (activeTab?.dataset.tabId) {
            updateTabContent(activeTab.dataset.tabId);
        }
    }
} 