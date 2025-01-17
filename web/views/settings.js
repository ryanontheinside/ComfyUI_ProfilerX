import { api } from '../utils/api.js';
export function showSettings(element) {
    let selectedArchive = null;
    // Set up the main container
    element.innerHTML = `
        <div style="padding: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <button id="archiveBtn" class="comfyui-button">Archive Current History</button>
                <a href="https://github.com/RyanOnTheInside/ComfyUI_ProfilerX" target="_blank" rel="noopener" 
                   class="comfyui-button" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
                    <i class="mdi mdi-github" style="font-size: 1.2em;"></i>
                    Star on GitHub
                </a>
            </div>

            <div style="margin: 16px 0;">
                <h4>History Archives</h4>
                <table id="archivesTable">
                    <thead>
                        <tr>
                            <th>Filename</th>
                            <th>Created</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="3" style="text-align: center; padding: 16px;">Loading archives...</td>
                        </tr>
                    </tbody>
                </table>

                <div style="margin-top: 8px; display: flex; gap: 8px;">
                    <button id="loadBtn" class="comfyui-button" disabled>Load Selected</button>
                    <button id="deleteBtn" class="comfyui-button" disabled>Delete Selected</button>
                </div>
            </div>

            <div style="position: absolute; bottom: 8px; right: 8px; opacity: 0.8;">
                Created by <a href="https://github.com/RyanOnTheInside" target="_blank" rel="noopener" 
                style="color: var(--comfy-color-accent); text-decoration: underline;">RyanOnTheInside</a>
            </div>
        </div>
    `;
    const loadBtn = element.querySelector('#loadBtn');
    const deleteBtn = element.querySelector('#deleteBtn');
    // Add styles for the table
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
        .comfyui-button {
            background-color: var(--comfy-input-bg);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 4px 8px;
            color: var(--descrip-text);
            cursor: pointer;
        }
        .comfyui-button:hover {
            background-color: var(--comfy-input-bg-hover);
            border-color: var(--border-color-hover);
        }
        .comfyui-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        #archivesTable {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            background: var(--comfy-input-bg);
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }
        #archivesTable th,
        #archivesTable td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        #archivesTable th {
            background: rgba(0, 0, 0, 0.2);
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }
        #archivesTable tbody tr {
            cursor: pointer;
            transition: background-color 0.2s;
            background-color: transparent;
        }
        #archivesTable tbody tr:hover {
            background-color: var(--comfy-input-bg-hover);
        }
        #archivesTable tbody tr.selected {
            background-color: var(--comfy-color-selected);
        }
        #archivesTable tbody tr.selected:hover {
            background-color: var(--comfy-color-selected-hover);
        }
        .filename-cell {
            font-family: var(--comfy-font-mono);
        }
    `;
    // Remove any existing ProfilerX styles to prevent duplicates
    const existingStyles = document.querySelectorAll('style[data-profilerx-settings]');
    existingStyles.forEach(style => style.remove());
    // Add identifier to our stylesheet
    styleSheet.setAttribute('data-profilerx-settings', '');
    document.head.appendChild(styleSheet);
    // Set up archive button
    const archiveBtn = element.querySelector('#archiveBtn');
    archiveBtn.onclick = async () => {
        if (!confirm('Are you sure you want to archive the current history? This will save the current history to an archive file and clear the current history.')) {
            return;
        }
        try {
            const response = await api.fetchApi('/profilerx/archive', { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                refreshArchives();
                // Refresh main view since history was cleared
                document.dispatchEvent(new CustomEvent('profiler:historyLoaded'));
            }
        }
        catch (error) {
            console.error('Failed to create archive:', error);
        }
    };
    // Set up load button
    loadBtn.onclick = async () => {
        if (!selectedArchive)
            return;
        if (!confirm('Loading this archive will save your current history to a new archive first. Continue?')) {
            return;
        }
        try {
            loadBtn.disabled = true;
            deleteBtn.disabled = true;
            const response = await api.fetchApi(`/profilerx/archive/${selectedArchive.filename}/load`, { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                // Wait a moment for the server to process the archive
                await new Promise(resolve => setTimeout(resolve, 100));
                // Refresh everything
                await refreshArchives();
                document.dispatchEvent(new CustomEvent('profiler:historyLoaded'));
            }
            else {
                console.error('Failed to load archive:', result.error);
                alert('Failed to load archive. Please check the console for details.');
            }
        }
        catch (error) {
            console.error('Failed to load archive:', error);
            alert('Failed to load archive. Please check the console for details.');
        }
        finally {
            loadBtn.disabled = false;
            deleteBtn.disabled = false;
        }
    };
    // Set up delete button
    deleteBtn.onclick = async () => {
        if (!selectedArchive)
            return;
        if (!confirm('Are you sure you want to delete this archive? This cannot be undone.')) {
            return;
        }
        try {
            const response = await api.fetchApi(`/profilerx/archive/${selectedArchive.filename}`, { method: 'DELETE' });
            const result = await response.json();
            if (result.success) {
                refreshArchives();
            }
        }
        catch (error) {
            console.error('Failed to delete archive:', error);
        }
    };
    // Function to refresh archives list
    async function refreshArchives() {
        const tbody = element.querySelector('#archivesTable tbody');
        try {
            const response = await api.fetchApi('/profilerx/archives');
            const archives = await response.json();
            tbody.innerHTML = '';
            selectedArchive = null;
            loadBtn.disabled = true;
            deleteBtn.disabled = true;
            if (archives.length === 0) {
                const row = tbody.insertRow();
                const cell = row.insertCell();
                cell.colSpan = 3;
                cell.textContent = 'No archives found';
                cell.style.textAlign = 'center';
                cell.style.padding = '16px';
                return;
            }
            archives.forEach((archive) => {
                const row = tbody.insertRow();
                const date = new Date(archive.created * 1000).toLocaleString();
                const size = Math.round(archive.size / 1024);
                row.innerHTML = `
                    <td class="filename-cell">${archive.filename}</td>
                    <td>${date}</td>
                    <td>${size}KB</td>
                `;
                row.onclick = () => {
                    // Clear previous selection
                    tbody.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));
                    // Set new selection
                    row.classList.add('selected');
                    selectedArchive = archive;
                    loadBtn.disabled = false;
                    deleteBtn.disabled = false;
                };
            });
        }
        catch (error) {
            console.error('Failed to fetch archives:', error);
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 16px;">Failed to load archives</td></tr>';
        }
    }
    // Initial load of archives
    refreshArchives();
}
