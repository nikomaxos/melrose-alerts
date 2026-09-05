import re

with open('index.js', 'r') as f:
    code = f.read()

# Replace the test-alert endpoint body
new_endpoint = """
app.post('/api/test-alert', async (req, res) => {
    try {
        const { destination } = req.body;
        if (!destination) {
            return res.status(400).json({ error: "Destination number is required" });
        }
        
        console.log(`Manual test alert requested for ${destination}`);
        
        // 1. Make the real API call
        let stats = {};
        if (config.melrose && config.melrose.api_url) {
            try {
                const response = await fetch(config.melrose.api_url, {
                    headers: {
                        'Authorization': `Bearer ${config.melrose.api_key}`,
                        'x-api-key': config.melrose.api_key,
                        'Accept': 'application/json'
                    }
                });
                if (response.ok) {
                    stats = await response.json();
                } else {
                    stats = { _error: `API returned ${response.status}` };
                }
            } catch (apiErr) {
                stats = { _error: `API fetch failed: ${apiErr.message}` };
            }
        } else {
            stats = { _error: "Melrose API URL not configured" };
        }

        // 2. Parse stats
        let deliveryRate = stats.delivery_rate ?? stats.deliveryRate ?? (stats.data && stats.data.delivery_rate);
        let pendingMessages = stats.pending_messages ?? stats.pendingMessages ?? (stats.data && stats.data.pending_messages);
        
        if (deliveryRate === undefined && stats.delivered && stats.total) {
            deliveryRate = ((stats.delivered / stats.total) * 100).toFixed(1);
        }

        const drText = deliveryRate !== undefined ? deliveryRate + '%' : 'N/A';
        const pendText = pendingMessages !== undefined ? pendingMessages : 'N/A';
        
        const testReason = `Test Alert from Web UI`;
        const smsBody = `URGENT (Melrose): Test Alert. Current Stats -> Delivery Rate: ${drText}, Pending: ${pendText}`;
        
        // 3. Send SMS
        await smppClient.sendSMS(destination, smsBody);
        
        // 4. Log to history
        logAlertHistory(destination, testReason, stats);
        
        res.json({ success: true, message: "Test alert sent successfully with real stats" });
    } catch (e) {
        console.error("Test alert failed:", e);
        res.status(500).json({ error: e.message || "Failed to send test alert" });
    }
});
"""

# Replace existing test-alert
pattern = re.compile(r"app\.post\('/api/test-alert', async \(req, res\) => \{.*?\n\}\);\n", re.DOTALL)
code = pattern.sub(new_endpoint, code)

with open('index.js', 'w') as f:
    f.write(code)
