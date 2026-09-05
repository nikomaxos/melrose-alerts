with open('public/index.html', 'r') as f:
    html = f.read()

# Add test alert javascript function
js_test = """
    async function testAlert(destination) {
        if (!confirm(`Are you sure you want to send a test alert to ${destination}?`)) return;
        
        try {
            const res = await fetch('/api/test-alert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ destination })
            });
            const data = await res.json();
            if (data.success) {
                alert("Test alert sent successfully! Check your phone and the History page.");
            } else {
                alert("Failed to send test alert: " + data.error);
            }
        } catch (e) {
            alert("Error triggering test alert.");
        }
    }
"""
html = html.replace("function removeProfile", js_test + "\n    function removeProfile")

# Add button to the profile HTML generator
old_profile_html = """<button type="button" class="btn btn-danger" onclick="removeProfile(${index})" style="margin-top: 15px;">Remove Profile</button>"""
new_profile_html = """
                <div style="display: flex; gap: 10px; margin-top: 15px;">
                    <button type="button" class="btn btn-secondary" onclick="testAlert(document.getElementById('dest_${index}').value)">🔔 Send Test Alert</button>
                    <button type="button" class="btn btn-danger" onclick="removeProfile(${index})">Remove Profile</button>
                </div>
"""
html = html.replace(old_profile_html, new_profile_html)

with open('public/index.html', 'w') as f:
    f.write(html)
