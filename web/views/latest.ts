// Latest run view
import { ProfilerStats, NodeProfile } from '../types.js';
import { applyTableStyles, makeSortable } from '../ui/table.js';

export function showLatestRun(element: HTMLElement, stats: ProfilerStats) {
    if (!stats || !stats.latest) {
        element.innerHTML = '<div style="padding: 8px;">No profiling data available yet. Run a workflow to see stats.</div>';
        return;
    }

    const profile = stats.latest;
    const workflow_time = profile.endTime - profile.startTime;
    const workflow_avg = stats.workflow_averages || {};
    
    const html = [
        `<div style="padding: 8px;">`,
        `<h3>Latest Workflow Run</h3>`,
        `<div style="margin: 8px 0;">`,
        `  <div>Last Run: ${(workflow_time/1000).toFixed(2)}s</div>`,
        `  <div>Average: ${(workflow_avg.total_time/1000 || 0).toFixed(2)}s (${workflow_avg.count || 0} runs)</div>`,
        `  <div>VRAM Peak: ${(profile.totalVramPeak/1e9).toFixed(2)}GB</div>`,
        `  <div>RAM Peak: ${(profile.totalRamPeak/1e9).toFixed(2)}GB</div>`,
        `  <div>Cache: ${profile.cacheHits} hits / ${profile.cacheMisses} misses</div>`,
        `</div>`,
        `<div style="margin: 8px 0;">`,
        `<h4>Node Performance</h4>`,
        `<table>`,
        `  <thead>`,
        `    <tr>`,
        `      <th>Node Type</th>`,
        `      <th class="sort-numeric">Time (s)</th>`,
        `      <th class="sort-numeric">VRAM (GB)</th>`,
        `      <th class="sort-numeric">RAM (GB)</th>`,
        `      <th>Cache</th>`,
        `    </tr>`,
        `  </thead>`,
        `  <tbody>`
    ];

    // Sort nodes by execution time
    const nodeStats = Object.entries(profile.nodes)
        .map(([nodeId, node]: [string, NodeProfile]) => {
            const execution_time = node.endTime - node.startTime;
            const vram_used = node.vramAfter - node.vramBefore;
            const ram_used = node.ramAfter - node.ramBefore;
            return { 
                execution_time, 
                vram_used,
                ram_used,
                nodeId, 
                node 
            };
        })
        .sort((a, b) => b.execution_time - a.execution_time);

    // Add node stats as table rows
    nodeStats.forEach(({ execution_time, vram_used, ram_used, nodeId, node }) => {
        const cache_status = node.cacheHit ? '🟢' : '⚡';
        const row_style = node.cacheHit ? 'opacity: 0.7;' : '';

        html.push(`
            <tr style="border-top: 1px solid var(--border-color); ${row_style}">
                <td>
                    <div>${node.nodeType}</div>
                    <div style="opacity: 0.7; font-size: 10px;">(${nodeId})</div>
                </td>
                <td>${(execution_time/1000).toFixed(3)}</td>
                <td>${(vram_used/1e9).toFixed(2)}</td>
                <td>${(ram_used/1e9).toFixed(2)}</td>
                <td>${cache_status}</td>
            </tr>
        `);
    });

    html.push(`
            </tbody>
        </table>
        </div>
        </div>
    `);

    element.innerHTML = html.join('');

    // After setting innerHTML, make the table sortable and apply styles
    const table = element.querySelector('table');
    if (table) {
        applyTableStyles(table as HTMLTableElement);
        makeSortable(table as HTMLTableElement);
    }
} 