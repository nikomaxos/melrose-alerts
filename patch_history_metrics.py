import re

with open('public/history.html', 'r') as f:
    html = f.read()

# Add Key Metrics column to the table header
html = html.replace('<th>Trigger Reason</th>\n                    <th>Raw Stats</th>', '<th>Trigger Reason</th>\n                    <th>Key Metrics</th>\n                    <th>Raw Stats</th>')
html = html.replace('<td colspan="4" class="empty-msg">', '<td colspan="5" class="empty-msg">')


# Replace the javascript row generation
old_row = """                const rowId = 'details_' + Math.random().toString(36).substring(7);
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

new_row = """                const rowId = 'details_' + Math.random().toString(36).substring(7);
                const hasStats = !!alert.stats;
                const formattedJson = hasStats ? JSON.stringify(alert.stats, null, 2).replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';
                
                // Parse key metrics from stats
                let metricsHtml = '<span style="color: #999;">N/A</span>';
                if (hasStats) {
                    const s = alert.stats;
                    if (s._error) {
                        metricsHtml = `<span style="color: #dc3545; font-weight: 500;">Error: ${s._error}</span>`;
                    } else {
                        let dr = s.delivery_rate ?? s.deliveryRate ?? (s.data && s.data.delivery_rate);
                        if (dr === undefined && s.delivered && s.total) dr = ((s.delivered / s.total) * 100).toFixed(1);
                        let pend = s.pending_messages ?? s.pendingMessages ?? (s.data && s.data.pending_messages);
                        let parts = [];
                        if (dr !== undefined) parts.push(`<strong>DLR:</strong> ${dr}%`);
                        if (pend !== undefined) parts.push(`<strong>Pending:</strong> ${pend}`);
                        if (parts.length > 0) {
                            metricsHtml = parts.join(' | ');
                        } else {
                            metricsHtml = '<span style="color: #666; font-size: 0.9em;">(No metric fields found)</span>';
                        }
                    }
                }
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="white-space: nowrap;">${formatDate(alert.timestamp)}</td>
                    <td><strong>${alert.destination_number}</strong></td>
                    <td style="color: #dc3545;">${alert.reason}</td>
                    <td>${metricsHtml}</td>
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
                        <td colspan="5">
                            <strong>Raw API Response:</strong>
                            <pre class="json-pre">${formattedJson}</pre>
                        </td>
                    `;
                    tbody.appendChild(trExpanded);
                }"""

html = html.replace(old_row, new_row)

with open('public/history.html', 'w') as f:
    f.write(html)
