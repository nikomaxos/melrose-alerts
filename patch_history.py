with open('public/history.html', 'r') as f:
    html = f.read()

# Add styles for expandable row and pre formatted json
styles = """
        .stats-badge { background: #e9ecef; color: #495057; padding: 3px 6px; border-radius: 4px; font-size: 0.85em; font-family: monospace; }
        .stats-btn { background: #e9ecef; color: #495057; border: 1px solid #ccc; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.85em; font-family: inherit; }
        .stats-btn:hover { background: #dee2e6; }
        .expanded-row { display: none; background-color: #fafafa; }
        .expanded-row td { padding: 15px; border-bottom: 2px solid #ddd; }
        .json-pre { margin: 0; background: #272822; color: #f8f8f2; padding: 15px; border-radius: 6px; font-family: monospace; overflow-x: auto; font-size: 13px; }
"""
html = html.replace(".stats-badge { background: #e9ecef; color: #495057; padding: 3px 6px; border-radius: 4px; font-size: 0.85em; font-family: monospace; }", styles)

# Add toggle script
toggle_script = """
    function toggleRow(id) {
        const row = document.getElementById(id);
        if (row.style.display === 'table-row') {
            row.style.display = 'none';
        } else {
            row.style.display = 'table-row';
        }
    }

    async function loadHistory() {
"""
html = html.replace("async function loadHistory() {", toggle_script)


# Replace the javascript row generation
old_row = """                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="white-space: nowrap;">${formatDate(alert.timestamp)}</td>
                    <td><strong>${alert.destination_number}</strong></td>
                    <td style="color: #dc3545;">${alert.reason}</td>
                    <td><span class="stats-badge" title="${statsStr}">${alert.stats ? 'Hover to view' : 'N/A'}</span></td>
                `;
                tbody.appendChild(tr);"""

new_row = """                const rowId = 'details_' + Math.random().toString(36).substring(7);
                const hasStats = !!alert.stats;
                const formattedJson = hasStats ? JSON.stringify(alert.stats, null, 2).replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="white-space: nowrap;">${formatDate(alert.timestamp)}</td>
                    <td><strong>${alert.destination_number}</strong></td>
                    <td style="color: #dc3545;">${alert.reason}</td>
                    <td>
                        ${hasStats ? `<button class="stats-btn" onclick="toggleRow('${rowId}')">👁️ View Data</button>` : '<span class="stats-badge">N/A</span>'}
                    </td>
                `;
                tbody.appendChild(tr);
                
                if (hasStats) {
                    const trExpanded = document.createElement('tr');
                    trExpanded.id = rowId;
                    trExpanded.className = 'expanded-row';
                    trExpanded.innerHTML = `
                        <td colspan="4">
                            <strong>Raw API Response:</strong>
                            <pre class="json-pre">${formattedJson}</pre>
                        </td>
                    `;
                    tbody.appendChild(trExpanded);
                }"""

html = html.replace(old_row, new_row)

with open('public/history.html', 'w') as f:
    f.write(html)
