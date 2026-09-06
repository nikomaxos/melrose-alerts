with open('index.js', 'r') as f:
    code = f.read()

webhook_code = """
// ----------------------------------------------------
// SLACK WEBHOOK RECEIVER FOR MELROSE TRAFFIC ALARMS
// ----------------------------------------------------
app.post('/webhook/melrose', async (req, res) => {
    try {
        console.log("Received Webhook from Melrose:", JSON.stringify(req.body));
        
        let alertText = "Traffic Alarm from Melrose";
        
        // Slack webhook payload usually has a "text" field
        if (req.body && req.body.text) {
            alertText = req.body.text;
        } else if (req.body && req.body.attachments && req.body.attachments.length > 0) {
            alertText = req.body.attachments[0].text || req.body.attachments[0].fallback || JSON.stringify(req.body.attachments);
        } else {
            // Fallback: just dump the payload if format is unknown
            alertText = JSON.stringify(req.body).substring(0, 140);
        }

        // Keep SMS within typical length (160 chars) or allow multipart depending on SMPP
        const smsBody = `MELROSE ALARM: ${alertText}`.substring(0, 160);

        if (!config.profiles || config.profiles.length === 0) {
            console.warn("Webhook received but no destination profiles are configured!");
            return res.status(200).send("ok");
        }

        // Send to all configured destinations
        for (const p of config.profiles) {
            if (!p.destination_number) continue;
            
            try {
                await smppClient.sendSMS(p.destination_number, smsBody);
                logAlertHistory(p.destination_number, "Melrose External Webhook", req.body);
                console.log(`Sent webhook alert SMS to ${p.destination_number}`);
            } catch (err) {
                console.error(`Failed to send webhook alert to ${p.destination_number}:`, err);
            }
        }
        
        res.status(200).send("ok");
    } catch (e) {
        console.error("Webhook processing error:", e);
        res.status(500).send("error");
    }
});
"""

if "/webhook/melrose" not in code:
    code = code.replace("app.post('/api/test-alert'", webhook_code + "\n\napp.post('/api/test-alert'")
    with open('index.js', 'w') as f:
        f.write(code)
    print("Webhook injected.")
else:
    print("Webhook already exists.")
