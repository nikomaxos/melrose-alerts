const fs = require('fs');
const YAML = require('yaml');
const express = require('express');
const SmppClient = require('./smppClient');

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

app.post('/api/config', (req, res) => {
  try {
    const newConfig = req.body;
    
    const smppChanged = JSON.stringify(config.smpp) !== JSON.stringify(newConfig.smpp);

    // Merge updates
    config.smpp = newConfig.smpp;
    config.profiles = newConfig.profiles || [];

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
