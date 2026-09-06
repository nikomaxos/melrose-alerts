const fs = require('fs');
const YAML = require('yaml');
const express = require('express');
const SmppClient = require('./smppClient');
const webpush = require('web-push');

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

let config = YAML.parse(fs.readFileSync('./config.yaml', 'utf8'));
let smppClient = new SmppClient(config.smpp);

// State tracking per profile destination number
// lastAlertTime[dest] = Date.now()
// pendingExceededSince[dest] = Date.now()
let state = {
  lastAlertTime: {},
  pendingExceededSince: {}
};

// UI Server setup
const app = express();
app.use(express.json());
app.use(express.static('public'));


app.get('/api/status', (req, res) => {
  res.json({
    smpp_connected: smppClient.connected,
    smpp_last_error: smppClient.lastError || null
  });
});


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

app.get('/api/config', (req, res) => {
  res.json(config);
});




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
        }
        
        res.status(200).send("ok");
    } catch (e) {
        console.error("Webhook processing error:", e);
        res.status(500).send("error");
    }
});



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
        
        // 3. Send SMS and Push based on config
        const p = config.profiles.find(x => x.destination_number === destination) || {};
        if (p.enable_sms !== false) {
            await smppClient.sendSMS(destination, smsBody);
        }
        if (p.enable_push !== false) {
            await sendWebPush(destination, smsBody);
        }
        
        // 4. Log to history
        logAlertHistory(destination, testReason, stats);
        
        res.json({ success: true, message: "Test alert sent successfully with real stats" });
    } catch (e) {
        console.error("Test alert failed:", e);
        res.status(500).json({ error: e.message || "Failed to send test alert" });
    }
});

app.post('/api/config', (req, res) => {
  try {
    const newConfig = req.body;
    
    const smppChanged = JSON.stringify(config.smpp) !== JSON.stringify(newConfig.smpp);

    // Merge updates
    config.smpp = newConfig.smpp;
    config.profiles = newConfig.profiles || [];
    if (newConfig.melrose) {
        config.melrose = newConfig.melrose;
    }

    // Save to file
    fs.writeFileSync('./config.yaml', YAML.stringify(config), 'utf8');
    console.log('Configuration updated successfully via UI');

    // Reconnect SMPP if global settings changed
    if (smppChanged) {
      console.log('SMPP settings changed, reconnecting...');
      smppClient.config = config.smpp;
      smppClient.connect().catch(e => console.error('Reconnect failed:', e.message));
    }

    res.json({ success: true, config });
  } catch (err) {
    console.error('Failed to update config:', err);
    res.status(500).json({ error: 'Failed to update config' });
  }
});

async function fetchMelroseStats() {
  try {
    const response = await fetch(config.melrose.api_url, {
      headers: {
        'Authorization': `Bearer ${config.melrose.api_key}`,
        'x-api-key': config.melrose.api_key,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Error fetching data from API:', error.message);
    return null;
  }
}

async function sendAlert(profile, reason, stats) {
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
}

async function checkAndAlert(stats) {
  // Try to find delivery_rate and pending_messages in common JSON structures
  let deliveryRate = stats.delivery_rate ?? stats.deliveryRate ?? (stats.data && stats.data.delivery_rate);
  let pendingMessages = stats.pending_messages ?? stats.pendingMessages ?? (stats.data && stats.data.pending_messages) ?? 0;
  
  if (deliveryRate === undefined && stats.delivered && stats.total) {
      deliveryRate = (stats.delivered / stats.total) * 100;
  }


  console.log(`Stats - Delivery Rate: ${deliveryRate}%, Pending: ${pendingMessages}`);

  for (const profile of config.profiles) {
    const dest = profile.destination_number;
    if (!dest) continue;

    // Condition 1: Delivery Rate
    if (deliveryRate !== undefined && deliveryRate < profile.delivery_rate_threshold_percent) {
      await sendAlert(profile, `Delivery rate dropped to ${deliveryRate}%`, stats);
    }

    // Condition 2: Pending Messages
    const pendingThreshold = profile.pending_messages_threshold;
    if (pendingMessages > pendingThreshold) {
      if (!state.pendingExceededSince[dest]) {
        state.pendingExceededSince[dest] = Date.now();
      }
      
      const exceededDurationSecs = (Date.now() - state.pendingExceededSince[dest]) / 1000;
      if (exceededDurationSecs >= profile.pending_messages_duration_seconds) {
        await sendAlert(profile, `Pending messages (${pendingMessages}) exceeded threshold for > ${profile.pending_messages_duration_seconds}s`, stats);
      }
    } else {
      // Reset if it drops below threshold
      state.pendingExceededSince[dest] = null;
    }
  }
}

async function startPoller() {
  console.log('Starting Melrose Alerting Service poller...');
  try {
    await smppClient.connect();
  } catch (error) {
    console.error('Failed to connect to SMPP provider at startup:', error.message);
  }

  const intervalMs = config.melrose.polling_interval_seconds * 1000;
  setInterval(async () => {
    const stats = await fetchMelroseStats();
    if (stats) await checkAndAlert(stats);
  }, intervalMs);
}

// Start HTTP server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`UI Server listening on http://localhost:${PORT}`);
});

startPoller();
