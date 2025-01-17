// Historical trends view
import { ProfilerStats } from '../types.js';
import { applyTableStyles, makeSortable } from '../ui/table.js';
import { createTimeRangeSelector, filterHistoryByTimeRange } from '../ui/timerange.js';

export function showHistoricalTrends(element: HTMLElement, stats: ProfilerStats) {
    const { container: rangeSelector, select: timeSelect } = createTimeRangeSelector();
    
    function updateContent() {
        const history = filterHistoryByTimeRange(stats.history || [], timeSelect.value);
        const workflow_avg = stats.workflow_averages || {};
        
        const contentDiv = element.querySelector('.history-content') as HTMLElement;
        if (!contentDiv) return;
        
        const html = [`
            <div style="margin: 8px 0;">
                <strong>Overall Averages:</strong>
                <div style="margin: 8px 0; padding: 12px; background: var(--comfy-input-bg); border-radius: 4px;">
                    <div>Execution Time: ${(workflow_avg.total_time/1000).toFixed(2)}s</div>
                    <div>VRAM Peak: ${(workflow_avg.vram_peak/1e9).toFixed(2)}GB</div>
                    <div>RAM Peak: ${(workflow_avg.ram_peak/1e9).toFixed(2)}GB</div>
                    <div>Total Runs: ${workflow_avg.count || 0}</div>
                </div>
            </div>
            <div style="margin: 8px 0;">
                <strong>Recent Runs:</strong>
                <table>
                    <thead>
                        <tr>
                            <th class="sort-time">Time</th>
                            <th class="sort-numeric">Duration (s)</th>
                            <th class="sort-numeric">VRAM (GB)</th>
                            <th class="sort-numeric">Cache Hit %</th>
                        </tr>
                    </thead>
                    <tbody>
        `];

        history.slice().reverse().forEach(run => {
            const date = new Date(run.startTime).toLocaleTimeString();
            const duration = ((run.endTime - run.startTime)/1000).toFixed(2);
            const vram = (run.totalVramPeak/1e9).toFixed(2);
            const cacheRate = run.cacheHits / (run.cacheHits + run.cacheMisses);
            
            html.push(`
                <tr>
                    <td data-timestamp="${run.startTime}">${date}</td>
                    <td>${duration}</td>
                    <td>${vram}</td>
                    <td>${(cacheRate * 100).toFixed(1)}</td>
                </tr>
            `);
        });

        html.push(`
                    </tbody>
                </table>
            </div>
        `);

        contentDiv.innerHTML = html.join('');
        const table = contentDiv.querySelector('table');
        if (table) {
            applyTableStyles(table as HTMLTableElement);
            makeSortable(table as HTMLTableElement);
        }
    }
    
    // Set up the main container
    element.innerHTML = `
        <div style="padding: 8px;">
            <h3>Workflow Performance Trends</h3>
            <div class="history-content"></div>
        </div>
    `;
    
    // Insert range selector after heading
    const heading = element.querySelector('h3');
    if (heading) heading.after(rangeSelector);
    
    // Update when time range changes
    timeSelect.addEventListener('change', updateContent);
    
    // Initial content update
    updateContent();
} 