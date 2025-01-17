// Time range selector component

export interface TimeRangeOption {
    value: string;
    label: string;
}

export interface TimeRangeSelector {
    container: HTMLElement;
    select: HTMLSelectElement;
}

export function createTimeRangeSelector(): TimeRangeSelector {
    const container = document.createElement('div');
    container.style.cssText = `
        margin: 8px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    
    const label = document.createElement('label');
    label.textContent = 'Show data from last: ';
    
    const select = document.createElement('select');
    select.style.cssText = `
        background: var(--comfy-input-bg);
        color: var(--descrip-text);
        border: 1px solid var(--border-color);
        padding: 4px;
        border-radius: 4px;
    `;
    
    const options: TimeRangeOption[] = [
        { value: '1h', label: '1 hour' },
        { value: '6h', label: '6 hours' },
        { value: '24h', label: '24 hours' },
        { value: '7d', label: '7 days' },
        { value: 'all', label: 'All time' }
    ];
    
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        select.appendChild(option);
    });
    
    container.appendChild(label);
    container.appendChild(select);
    
    return { container, select };
}

export function filterHistoryByTimeRange(history: any[], timeRange: string): any[] {
    if (timeRange === 'all') return history;
    
    const now = Date.now();
    const ranges = {
        '1h': 60 * 60 * 1000,
        '6h': 6 * 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000,
        '7d': 7 * 24 * 60 * 60 * 1000
    };
    
    const cutoff = now - (ranges[timeRange as keyof typeof ranges] || 0);
    return history.filter(item => item.startTime > cutoff);
} 