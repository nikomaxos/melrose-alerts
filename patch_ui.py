import re

with open('public/index.html', 'r') as f:
    html = f.read()

melrose_section = """
        <!-- MELROSE API SETTINGS -->
        <div class="card">
            <h3>Melrose SSG API Settings</h3>
            <div class="form-row">
                <div class="form-group" style="flex: 2">
                    <label>API URL</label>
                    <input type="text" id="melrose_url" placeholder="http://ip:port/v1/stats" required>
                </div>
                <div class="form-group">
                    <label>API Key (optional)</label>
                    <input type="password" id="melrose_key">
                </div>
                <div class="form-group">
                    <label>Polling Interval (Secs)</label>
                    <input type="number" id="melrose_interval" value="5" required>
                </div>
            </div>
        </div>
"""

# Insert the new section before the SMPP settings
html = html.replace('<!-- SMPP GLOBAL SETTINGS -->', melrose_section + '\n        <!-- SMPP GLOBAL SETTINGS -->')

# Update Javascript loadConfig()
js_load = """
            // Melrose
            if (globalConfig.melrose) {
                document.getElementById('melrose_url').value = globalConfig.melrose.api_url || '';
                document.getElementById('melrose_key').value = globalConfig.melrose.api_key || '';
                document.getElementById('melrose_interval').value = globalConfig.melrose.polling_interval_seconds || 5;
            }

            // SMPP
"""
html = html.replace('// SMPP', js_load)

# Update Javascript save
js_save = """
        // Gather Melrose
        if (!globalConfig.melrose) globalConfig.melrose = {};
        globalConfig.melrose.api_url = document.getElementById('melrose_url').value;
        globalConfig.melrose.api_key = document.getElementById('melrose_key').value;
        globalConfig.melrose.polling_interval_seconds = parseInt(document.getElementById('melrose_interval').value);

        // Gather SMPP
"""
html = html.replace('// Gather SMPP', js_save)

with open('public/index.html', 'w') as f:
    f.write(html)
