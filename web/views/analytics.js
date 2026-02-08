import { applyTableStyles, makeSortable } from '../ui/table.js';
import { createTimeRangeSelector, filterHistoryByTimeRange } from '../ui/timerange.js';
export function showNodeAnalytics(element, stats) {
    const { container: rangeSelector, select: timeSelect } = createTimeRangeSelector();
    function updateContent() {
        // Filter history by time range
        const history = filterHistoryByTimeRange(stats.history || [], timeSelect.value);
        // Calculate node averages + stddev from filtered history (Welford's algorithm)
        const nodeAverages = {};
        history.forEach(run => {
            const nodes = Object.values(run.nodes);
            nodes.forEach(node => {
                const nodeType = node.nodeType;
                if (!nodeAverages[nodeType]) {
                    nodeAverages[nodeType] = {
                        total_time: 0, vram_usage: 0, ram_usage: 0,
                        _m2_time: 0, _m2_vram: 0, _m2_ram: 0,
                        std_time: 0, std_vram: 0, std_ram: 0,
                        count: 0, cache_hits: 0
                    };
                }
                const s = nodeAverages[nodeType];
                s.count++;
                const n = s.count;
                const time_val = (node.endTime || 0) - (node.startTime || 0);
                const vram_val = (node.vramAfter || 0) - (node.vramBefore || 0);
                const ram_val = (node.ramAfter || 0) - (node.ramBefore || 0);
                // Welford update for each metric
                for (const [key, val, m2key, stdkey] of [
                    ['total_time', time_val, '_m2_time', 'std_time'],
                    ['vram_usage', vram_val, '_m2_vram', 'std_vram'],
                    ['ram_usage', ram_val, '_m2_ram', 'std_ram'],
                ]) {
                    const delta = val - s[key];
                    s[key] += delta / n;
                    const delta2 = val - s[key];
                    s[m2key] += delta * delta2;
                    s[stdkey] = n > 1 ? Math.sqrt(s[m2key] / n) : 0;
                }
                if (node.cacheHit) s.cache_hits++;
            });
        });
        // Convert to array for sorting
        const nodeStats = Object.entries(nodeAverages).map(([nodeType, s]) => ({
            nodeType, ...s
        }));
        nodeStats.sort((a, b) => b.total_time - a.total_time);
        const contentDiv = element.querySelector('.node-analytics-content');
        if (!contentDiv) return;
        const html = [`
            <div style="margin: 8px 0;">
                <table>
                    <thead>
                        <tr>
                            <th>Node Type</th>
                            <th class="sort-numeric">Avg Time (s)</th>
                            <th class="sort-numeric">\u00b1 Time (s)</th>
                            <th class="sort-numeric">Avg VRAM (GB)</th>
                            <th class="sort-numeric">\u00b1 VRAM (GB)</th>
                            <th class="sort-numeric">Runs</th>
                            <th class="sort-numeric">Cache Hit %</th>
                        </tr>
                    </thead>
                    <tbody>
        `];
        nodeStats.forEach(node => {
            const avgTime = (node.total_time / 1000).toFixed(3);
            const stdTime = (node.std_time / 1000).toFixed(3);
            const avgVram = (node.vram_usage / 1e9).toFixed(2);
            const stdVram = (node.std_vram / 1e9).toFixed(2);
            const cacheHitRate = ((node.cache_hits / node.count) * 100).toFixed(1);
            html.push(`
                <tr>
                    <td>${node.nodeType}</td>
                    <td>${avgTime}s</td>
                    <td>${stdTime}s</td>
                    <td>${avgVram}GB</td>
                    <td>${stdVram}GB</td>
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
            applyTableStyles(table);
            makeSortable(table);
        }
    }
    // Set up the main container
    element.innerHTML = `
        <div style="padding: 8px;">
            <h3>Node Performance Analytics</h3>
            <div class="node-analytics-content"></div>
        </div>
    `;
    const heading = element.querySelector('h3');
    if (heading) heading.after(rangeSelector);
    timeSelect.addEventListener('change', updateContent);
    updateContent();
}
