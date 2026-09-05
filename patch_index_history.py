import json

with open('index.js', 'r') as f:
    code = f.read()

history_code = """
const HISTORY_FILE = './alerts_history.json';
if (!fs.existsSync(HISTORY_FILE)) {
    fs.writeFileSync(HISTORY_FILE, JSON.stringify([]));
}

function logAlertHistory(dest, reason, stats) {
    try {
        const history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
        history.unshift({
            timestamp: new Date().toISOString(),
            destination_number: dest,
            reason: reason,
            stats: stats
        });
        
        // Keep only last 1000 alerts
        if (history.length > 1000) {
            history.length = 1000;
        }
        
        fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
    } catch (e) {
        console.error("Failed to write to alert history:", e);
    }
}

app.get('/api/history', (req, res) => {
    try {
        if (!fs.existsSync(HISTORY_FILE)) {
            return res.json([]);
        }
        const history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
        res.json(history);
    } catch (e) {
        res.status(500).json({ error: "Failed to read history" });
    }
});
"""

# Insert history code before app.get('/api/config')
code = code.replace("app.get('/api/config', (req, res) => {", history_code + "\napp.get('/api/config', (req, res) => {")

# Modify sendAlert function signature and logic to accept 'stats' and log it
old_sendAlert = "async function sendAlert(profile, reason) {"
new_sendAlert = "async function sendAlert(profile, reason, stats) {"
code = code.replace(old_sendAlert, new_sendAlert)

old_alert_success = "state.lastAlertTime[dest] = now;\n      console.log(`[${dest}] Alert sent successfully.`);"
new_alert_success = "state.lastAlertTime[dest] = now;\n      console.log(`[${dest}] Alert sent successfully.`);\n      logAlertHistory(dest, reason, stats);"
code = code.replace(old_alert_success, new_alert_success)

# Modify checkAndAlert to pass 'stats'
old_check_delivery = "await sendAlert(profile, `Delivery rate dropped to ${deliveryRate}%`);"
new_check_delivery = "await sendAlert(profile, `Delivery rate dropped to ${deliveryRate}%`, stats);"
code = code.replace(old_check_delivery, new_check_delivery)

old_check_pending = "await sendAlert(profile, `Pending messages (${pendingMessages}) exceeded threshold for > ${profile.pending_messages_duration_seconds}s`);"
new_check_pending = "await sendAlert(profile, `Pending messages (${pendingMessages}) exceeded threshold for > ${profile.pending_messages_duration_seconds}s`, stats);"
code = code.replace(old_check_pending, new_check_pending)

with open('index.js', 'w') as f:
    f.write(code)
