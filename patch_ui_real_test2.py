with open('public/index.html', 'r') as f:
    html = f.read()

old_dest = """                    <input type="text" id="dest_${index}" value="${p.destination_number || ''}" required placeholder="3069...">"""
new_dest = """                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="dest_${index}" value="${p.destination_number || ''}" required placeholder="3069..." style="flex: 1;">
                        <button type="button" class="btn btn-secondary" onclick="testAlert(document.getElementById('dest_${index}').value)">🔔 Test Alert</button>
                    </div>"""

html = html.replace(old_dest, new_dest)

with open('public/index.html', 'w') as f:
    f.write(html)
