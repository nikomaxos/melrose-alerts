with open('index.js', 'r') as f:
    code = f.read()

test_alert_endpoint = """
app.post('/api/test-alert', async (req, res) => {
    try {
        const { destination } = req.body;
        if (!destination) {
            return res.status(400).json({ error: "Destination number is required" });
        }
        
        console.log(`Manual test alert requested for ${destination}`);
        const testReason = "Test Alert from Web UI";
        const dummyStats = { delivery_rate: 100, pending_messages: 0, _note: "This is a test alert" };
        
        await smppClient.sendSMS(destination, `URGENT (Melrose): ${testReason}`);
        logAlertHistory(destination, testReason, dummyStats);
        
        res.json({ success: true, message: "Test alert sent successfully" });
    } catch (e) {
        console.error("Test alert failed:", e);
        res.status(500).json({ error: e.message || "Failed to send test alert" });
    }
});
"""

code = code.replace("app.post('/api/config'", test_alert_endpoint + "\napp.post('/api/config'")

with open('index.js', 'w') as f:
    f.write(code)
