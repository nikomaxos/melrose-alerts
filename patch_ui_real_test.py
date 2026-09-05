import re

with open('public/index.html', 'r') as f:
    html = f.read()

# Add the test button HTML inside the profile card
old_dest_html = """<label>Destination Number (e.g. 3069...)</label>
                    <input type="text" id="dest_${index}" value="${p.destination_number || ''}" required>
                </div>"""

new_dest_html = """<label>Destination Number (e.g. 3069...)</label>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="dest_${index}" value="${p.destination_number || ''}" required style="flex: 1;">
                        <button type="button" class="btn btn-secondary" onclick="testAlert(document.getElementById('dest_${index}').value)">🔔 Test</button>
                    </div>
                </div>"""

html = html.replace(old_dest_html, new_dest_html)

with open('public/index.html', 'w') as f:
    f.write(html)
