// Node analytics view
import { ProfilerStats, NodeProfile } from '../types.js';
import { applyTableStyles, makeSortable } from '../ui/table.js';
import { createTimeRangeSelector, filterHistoryByTimeRange } from '../ui/timerange.js';

export function showNodeAnalytics(element: HTMLElement, stats: ProfilerStats) {
    const { container: rangeSelector, select: timeSelect } = createTimeRangeSelector();
    
    function updateContent() {
        // Filter history by time range
        const history = filterHistoryByTimeRange(stats.history || [], timeSelect.value);
        
        // Calculate node averages from filtered history
        const nodeAverages: Record<string, any> = {};
        
        history.forEach(run => {
            const nodes = Object.values(run.nodes) as NodeProfile[];
            nodes.forEach(node => {
                const nodeType = node.nodeType;
                if (!nodeAverages[nodeType]) {
                    nodeAverages[nodeType] = {
                        total_time: 0,
                        vram_usage: 0,
                        ram_usage: 0,
                        count: 0,
                        cache_hits: 0
                    };
                }
                
                const stats = nodeAverages[nodeType];
                stats.count++;
                stats.total_time = (stats.total_time * (stats.count - 1) + (node.endTime - node.startTime)) / stats.count;
                stats.vram_usage = (stats.vram_usage * (stats.count - 1) + (node.vramAfter - node.vramBefore)) / stats.count;
                stats.ram_usage = (stats.ram_usage * (stats.count - 1) + (node.ramAfter - node.ramBefore)) / stats.count;
                if (node.cacheHit) stats.cache_hits++;
            });
        });
        
        // Convert to array for sorting
        const nodeStats = Object.entries(nodeAverages).map(([nodeType, stats]) => ({
            nodeType,
            ...stats
        }));

        // Sort by execution time by default
        nodeStats.sort((a, b) => b.total_time - a.total_time);

        const contentDiv = element.querySelector('.node-analytics-content') as HTMLElement;
        if (!contentDiv) return;

        const html = [`
            <div style="margin: 8px 0;">
                <table>
                    <thead>
                        <tr>
                            <th>Node Type</th>
                            <th class="sort-numeric">Avg Time (s)</th>
                            <th class="sort-numeric">Avg VRAM (GB)</th>
                            <th class="sort-numeric">Runs</th>
                            <th class="sort-numeric">Cache Hit %</th>
                        </tr>
                    </thead>
                    <tbody>
        `];

        nodeStats.forEach(node => {
            const avgTime = (node.total_time/1000).toFixed(3);
            const avgVram = (node.vram_usage/1e9).toFixed(2);
            const cacheHitRate = ((node.cache_hits / node.count) * 100).toFixed(1);
            
            html.push(`
                <tr>
                    <td>${node.nodeType}</td>
                    <td>${avgTime}s</td>
                    <td>${avgVram}GB</td>
                    <td>${node.count}</td>
                    <td>${cacheHitRate}%</td>
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
            <h3>Node Performance Analytics</h3>
            <div class="node-analytics-content"></div>
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