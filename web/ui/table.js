// Table sorting and styling utilities
// Add table styling helper
export function applyTableStyles(table) {
    table.style.cssText = `
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        background: var(--comfy-input-bg);
        border-radius: 8px;
        overflow: hidden;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    `;
    // Style header cells
    table.querySelectorAll('thead th').forEach(th => {
        const header = th;
        header.style.cssText = `
            padding: 12px 8px;
            text-align: left;
            border-bottom: 2px solid var(--border-color);
            font-weight: 600;
            white-space: nowrap;
            color: var(--descrip-text);
            background: rgba(0, 0, 0, 0.2);
        `;
    });
    // Style body cells
    table.querySelectorAll('tbody td').forEach(td => {
        const cell = td;
        cell.style.cssText = `
            padding: 8px;
            border-bottom: 1px solid var(--border-color);
            transition: background-color 0.2s;
        `;
    });
    // Add hover effect to rows
    table.querySelectorAll('tbody tr').forEach(tr => {
        const row = tr;
        row.style.transition = 'background-color 0.2s';
        row.addEventListener('mouseenter', () => {
            row.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
        });
        row.addEventListener('mouseleave', () => {
            row.style.backgroundColor = '';
        });
    });
    // Add alternating row colors
    table.querySelectorAll('tbody tr:nth-child(even)').forEach(tr => {
        const row = tr;
        row.style.backgroundColor = 'rgba(0, 0, 0, 0.1)';
    });
}
// Add utility functions for sorting
export function makeSortable(table) {
    const headers = table.querySelectorAll('th');
    const tbody = table.querySelector('tbody');
    headers.forEach((header, index) => {
        const th = header;
        if (th.classList.contains('no-sort'))
            return;
        th.style.cssText = `
            cursor: pointer;
            user-select: none;
            position: relative;
            padding: 8px 24px 8px 8px;
            text-align: left;
            border-bottom: 2px solid var(--border-color);
            transition: background-color 0.2s;
            font-weight: 600;
            color: var(--descrip-text);
        `;
        // Add sort indicator
        const indicator = document.createElement('span');
        indicator.className = 'sort-indicator';
        indicator.style.cssText = `
            position: absolute;
            right: 8px;
            opacity: 0.5;
        `;
        indicator.textContent = '⇅';
        th.appendChild(indicator);
        th.addEventListener('mouseenter', () => {
            th.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
        });
        th.addEventListener('mouseleave', () => {
            if (!th.classList.contains('sort-asc') && !th.classList.contains('sort-desc')) {
                th.style.backgroundColor = '';
            }
        });
        th.addEventListener('click', () => {
            if (!tbody)
                return;
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAscending = th.classList.contains('sort-asc');
            // Clear previous sort indicators
            headers.forEach(h => {
                const header = h;
                header.style.backgroundColor = '';
                header.classList.remove('sort-asc', 'sort-desc');
                const ind = header.querySelector('.sort-indicator');
                if (ind)
                    ind.textContent = '⇅';
            });
            // Sort rows
            rows.sort((a, b) => {
                const aCell = a.children[index];
                const bCell = b.children[index];
                if (!aCell || !bCell)
                    return 0;
                let aValue;
                let bValue;
                // Handle different column types
                if (th.classList.contains('sort-numeric')) {
                    // Extract numeric value, handling units like GB, MB, s, ms
                    const aText = aCell.textContent?.trim() || '0';
                    const bText = bCell.textContent?.trim() || '0';
                    // Convert to base unit (bytes for memory, ms for time)
                    const convertToBaseUnit = (text) => {
                        const num = parseFloat(text.replace(/[^\d.-]/g, '')) || 0;
                        if (text.includes('GB'))
                            return num * 1024 * 1024 * 1024;
                        if (text.includes('MB'))
                            return num * 1024 * 1024;
                        if (text.includes('KB'))
                            return num * 1024;
                        if (text.includes('s') && !text.includes('ms'))
                            return num * 1000;
                        return num;
                    };
                    aValue = convertToBaseUnit(aText);
                    bValue = convertToBaseUnit(bText);
                }
                else if (th.classList.contains('sort-time')) {
                    // Special handling for time values
                    const parseTime = (cell) => {
                        // First try to get timestamp from data attribute
                        const timestamp = cell.getAttribute('data-timestamp');
                        if (timestamp) {
                            return parseInt(timestamp);
                        }
                        // Fallback to parsing time string
                        const timeStr = cell.textContent?.trim() || '';
                        const timeParts = timeStr.split(':');
                        if (timeParts.length === 3) {
                            const [hours, minutes, seconds] = timeParts.map(Number);
                            return hours * 3600000 + minutes * 60000 + seconds * 1000;
                        }
                        return 0;
                    };
                    aValue = parseTime(aCell);
                    bValue = parseTime(bCell);
                }
                else {
                    // Text sorting - handle nested content
                    const getMainContent = (cell) => {
                        // For cells with nested divs (like Node Type column), get only the first div's content
                        const firstDiv = cell.querySelector('div');
                        if (firstDiv) {
                            return firstDiv.textContent || '';
                        }
                        return cell.textContent || '';
                    };
                    aValue = getMainContent(aCell).trim().toLowerCase();
                    bValue = getMainContent(bCell).trim().toLowerCase();
                }
                if (typeof aValue === 'string' && typeof bValue === 'string') {
                    return isAscending ?
                        aValue.localeCompare(bValue) :
                        bValue.localeCompare(aValue);
                }
                else {
                    const numA = Number(aValue);
                    const numB = Number(bValue);
                    return isAscending ? numA - numB : numB - numA;
                }
            });
            // Update sort indicator
            th.classList.toggle('sort-asc', !isAscending);
            th.classList.toggle('sort-desc', isAscending);
            th.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            const indicator = th.querySelector('.sort-indicator');
            if (indicator) {
                indicator.textContent = isAscending ? '⇓' : '⇑';
                indicator.style.opacity = '1';
            }
            // Reorder rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}
