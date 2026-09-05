with open('public/index.html', 'r') as f:
    html = f.read()

# Add badge HTML
header_replacement = """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0;">Global SMPP Connection Settings</h3>
                <span id="smpp_badge" style="padding: 5px 10px; border-radius: 4px; font-size: 0.85em; font-weight: bold; background: #6c757d; color: white;">Checking Status...</span>
            </div>
            <div id="smpp_error_box" style="display: none; background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 0.9em; border: 1px solid #f5c6cb;"></div>
"""

html = html.replace("<h3>Global SMPP Connection Settings</h3>", header_replacement)

# Add javascript polling
js_poll = """
    async function pollStatus() {
        try {
            const res = await fetch('/api/status');
            const status = await res.json();
            
            const badge = document.getElementById('smpp_badge');
            const errorBox = document.getElementById('smpp_error_box');
            
            if (status.smpp_connected) {
                badge.innerText = "● CONNECTED";
                badge.style.background = "#28a745";
                errorBox.style.display = "none";
            } else {
                badge.innerText = "● DISCONNECTED";
                badge.style.background = "#dc3545";
                if (status.smpp_last_error) {
                    errorBox.innerText = "Error: " + status.smpp_last_error;
                    errorBox.style.display = "block";
                } else {
                    errorBox.style.display = "none";
                }
            }
        } catch (e) {
            console.error("Status fetch failed");
        }
    }
    
    // Poll every 3 seconds
    setInterval(pollStatus, 3000);
    pollStatus();
"""

html = html.replace("loadConfig();\n</script>", "loadConfig();\n" + js_poll + "\n</script>")

with open('public/index.html', 'w') as f:
    f.write(html)
