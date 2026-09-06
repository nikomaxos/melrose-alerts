import re

with open('index.js', 'r') as f:
    code = f.read()

top_imports = """
const express = require('express');
const fs = require('fs');
const YAML = require('yaml');
const SMPPClient = require('./smppClient');
const webpush = require('web-push'); // NEW

// VAPID keys setup
const VAPID_KEYS_FILE = './vapid_keys.json';
let vapidKeys = {};
if (fs.existsSync(VAPID_KEYS_FILE)) {
    vapidKeys = JSON.parse(fs.readFileSync(VAPID_KEYS_FILE, 'utf8'));
} else {
    vapidKeys = webpush.generateVAPIDKeys();
    fs.writeFileSync(VAPID_KEYS_FILE, JSON.stringify(vapidKeys));
}
webpush.setVapidDetails('mailto:support@globalnetservices.net', vapidKeys.publicKey, vapidKeys.privateKey);

// Subscriptions storage
const SUBS_FILE = './subscriptions.json';
let subscriptions = {};
if (fs.existsSync(SUBS_FILE)) {
    try {
        subscriptions = JSON.parse(fs.readFileSync(SUBS_FILE, 'utf8'));
    } catch (e) {
        subscriptions = {};
    }
}
function saveSubscriptions() {
    fs.writeFileSync(SUBS_FILE, JSON.stringify(subscriptions, null, 2));
}

"""
code = re.sub(r"const express = require\('express'\);\nconst fs = require\('fs'\);\nconst YAML = require\('yaml'\);\nconst SMPPClient = require\('\./smppClient'\);", top_imports, code)


push_endpoints = """
// Push endpoints
app.get('/api/push/vapidPublicKey', (req, res) => {
    res.send(vapidKeys.publicKey);
});

app.post('/api/push/subscribe', (req, res) => {
    const { destination, subscription } = req.body;
    if (!destination || !subscription) return res.status(400).send("Bad request");
    
    if (!subscriptions[destination]) subscriptions[destination] = [];
    
    // Check if already exists
    const exists = subscriptions[destination].find(s => s.endpoint === subscription.endpoint);
    if (!exists) {
        subscriptions[destination].push(subscription);
        saveSubscriptions();
    }
    res.status(201).json({});
});

app.post('/api/push/unsubscribe', (req, res) => {
    const { destination, endpoint } = req.body;
    if (subscriptions[destination]) {
        subscriptions[destination] = subscriptions[destination].filter(s => s.endpoint !== endpoint);
        saveSubscriptions();
    }
    res.status(200).json({});
});

async function sendWebPush(dest, text) {
    if (!subscriptions[dest] || subscriptions[dest].length === 0) return;
    
    const payload = JSON.stringify({ title: 'Melrose Alert', body: text });
    for (let i = subscriptions[dest].length - 1; i >= 0; i--) {
        const sub = subscriptions[dest][i];
        try {
            await webpush.sendNotification(sub, payload);
        } catch (err) {
            if (err.statusCode === 404 || err.statusCode === 410) {
                // Subscription has expired or is no longer valid
                subscriptions[dest].splice(i, 1);
                saveSubscriptions();
            } else {
                console.error('Push error:', err);
            }
        }
    }
}
"""

code = code.replace("app.post('/api/test-alert'", push_endpoints + "\napp.post('/api/test-alert'")


send_alert_old = """async function sendAlert(profile, reason, stats) {
  const dest = profile.destination_number;
  const now = Date.now();
  const lastAlert = state.lastAlertTime[dest] || 0;
  const cooldownMs = profile.alert_cooldown_minutes * 60 * 1000;

  if (now - lastAlert > cooldownMs) {
    console.log(`[${dest}] Sending alert: ${reason}`);
    try {
      await smppClient.sendSMS(dest, `URGENT (Melrose): ${reason}`);
      state.lastAlertTime[dest] = now;
      console.log(`[${dest}] Alert sent successfully.`);
      logAlertHistory(dest, reason, stats);
    } catch (error) {
      console.error(`[${dest}] Failed to send SMS alert:`, error.message);
    }
  } else {
    console.log(`[${dest}] Alert condition met (${reason}), but in cooldown mode.`);
  }
}"""

send_alert_new = """async function sendAlert(profile, reason, stats) {
  const dest = profile.destination_number;
  const now = Date.now();
  const lastAlert = state.lastAlertTime[dest] || 0;
  const cooldownMs = (profile.alert_cooldown_minutes || 15) * 60 * 1000;

  const enableSms = profile.enable_sms !== false; // Default true
  const enablePush = profile.enable_push !== false; // Default true

  if (now - lastAlert > cooldownMs) {
    console.log(`[${dest}] Sending alert: ${reason}`);
    const alertText = `URGENT (Melrose): ${reason}`;
    
    let sent = false;

    if (enableSms) {
        try {
            await smppClient.sendSMS(dest, alertText);
            console.log(`[${dest}] SMS alert sent successfully.`);
            sent = true;
        } catch (error) {
            console.error(`[${dest}] Failed to send SMS alert:`, error.message);
        }
    }

    if (enablePush) {
        try {
            await sendWebPush(dest, alertText);
            console.log(`[${dest}] Web Push alert sent successfully.`);
            sent = true;
        } catch (error) {
            console.error(`[${dest}] Failed to send Web Push alert:`, error.message);
        }
    }

    if (sent) {
        state.lastAlertTime[dest] = now;
        logAlertHistory(dest, reason, stats);
    }
  } else {
    console.log(`[${dest}] Alert condition met (${reason}), but in cooldown mode.`);
  }
}"""

code = code.replace(send_alert_old, send_alert_new)

# Also update the webhook and test endpoints to respect channels
webhook_old = """        // Send to all configured destinations
        for (const p of config.profiles) {
            if (!p.destination_number) continue;
            
            try {
                await smppClient.sendSMS(p.destination_number, smsBody);
                logAlertHistory(p.destination_number, "Melrose External Webhook", req.body);
                console.log(`Sent webhook alert SMS to ${p.destination_number}`);
            } catch (err) {
                console.error(`Failed to send webhook alert to ${p.destination_number}:`, err);
            }
        }"""
webhook_new = """        // Send to all configured destinations
        for (const p of config.profiles) {
            if (!p.destination_number) continue;
            
            const enableSms = p.enable_sms !== false;
            const enablePush = p.enable_push !== false;

            if (enableSms) {
                try {
                    await smppClient.sendSMS(p.destination_number, smsBody);
                    console.log(`Sent webhook SMS to ${p.destination_number}`);
                } catch (err) {
                    console.error(`Failed to send webhook SMS to ${p.destination_number}:`, err);
                }
            }
            if (enablePush) {
                try {
                    await sendWebPush(p.destination_number, smsBody);
                    console.log(`Sent webhook Push to ${p.destination_number}`);
                } catch (err) {
                    console.error(`Failed to send webhook Push to ${p.destination_number}:`, err);
                }
            }
            logAlertHistory(p.destination_number, "Melrose External Webhook", req.body);
        }"""
code = code.replace(webhook_old, webhook_new)

test_alert_old = """        // 3. Send SMS
        await smppClient.sendSMS(destination, smsBody);"""
test_alert_new = """        // 3. Send SMS and Push based on config
        const p = config.profiles.find(x => x.destination_number === destination) || {};
        if (p.enable_sms !== false) {
            await smppClient.sendSMS(destination, smsBody);
        }
        if (p.enable_push !== false) {
            await sendWebPush(destination, smsBody);
        }"""
code = code.replace(test_alert_old, test_alert_new)


with open('index.js', 'w') as f:
    f.write(code)
