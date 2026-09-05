const fs = require('fs');
const YAML = require('yaml');
const express = require('express');
const SmppClient = require('./smppClient');

let config = YAML.parse(fs.readFileSync('./config.yaml', 'utf8'));
let smppClient = new SmppClient(config.smpp);

// State tracking
let lastAlertTime = 0;
let pendingExceededSince = null;

// UI Server setup
const app = express();
app.use(express.json());
app.use(express.static('public'));

app.get('/api/config', (req, res) => {
  res.json(config);
});

app.post('/api/config', (req, res) => {
  try {
    const newConfig = req.body;
    
    // Merge updates
    config.smpp.destination_number = newConfig.destination_number;
    config.alerting.delivery_rate_threshold_percent = Number(newConfig.delivery_rate_threshold_percent);
    config.alerting.pending_messages_threshold = Number(newConfig.pending_messages_threshold);
    config.alerting.pending_messages_duration_seconds = Number(newConfig.pending_messages_duration_seconds);

    // Save to file
    fs.writeFileSync('./config.yaml', YAML.stringify(config), 'utf8');

    // Update SMPP client if needed (though it might require reconnect for changes to host/port, we just update the destination here which is used dynamically per SMS)
    smppClient.config = config.smpp;

    console.log('Configuration updated successfully via UI');
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

async function sendAlert(reason) {
  const now = Date.now();
  const cooldownMs = config.alerting.alert_cooldown_minutes * 60 * 1000;

  if (now - lastAlertTime > cooldownMs) {
    console.log(`Sending alert: ${reason}`);
    try {
      await smppClient.sendSMS(`URGENT (Melrose): ${reason}`);
      lastAlertTime = now;
      console.log('Alert sent successfully.');
    } catch (error) {
      console.error('Failed to send SMS alert:', error);
    }
  } else {
    console.log(`Alert condition met (${reason}), but in cooldown mode.`);
  }
}

async function checkAndAlert(stats) {
  const deliveryRate = stats.delivery_rate;
  const pendingMessages = stats.pending_messages || 0;

  console.log(`Stats - Delivery Rate: ${deliveryRate}%, Pending: ${pendingMessages}`);

  // Condition 1: Delivery Rate
  if (deliveryRate !== undefined && deliveryRate < config.alerting.delivery_rate_threshold_percent) {
    await sendAlert(`Delivery rate dropped to ${deliveryRate}%`);
  }

  // Condition 2: Pending Messages
  const pendingThreshold = config.alerting.pending_messages_threshold;
  if (pendingMessages > pendingThreshold) {
    if (!pendingExceededSince) {
      pendingExceededSince = Date.now();
    }
    
    const exceededDurationSecs = (Date.now() - pendingExceededSince) / 1000;
    if (exceededDurationSecs >= config.alerting.pending_messages_duration_seconds) {
      await sendAlert(`Pending messages (${pendingMessages}) exceeded threshold for > ${config.alerting.pending_messages_duration_seconds}s`);
    }
  } else {
    // Reset if it drops below threshold
    pendingExceededSince = null;
  }
}

async function startPoller() {
  console.log('Starting Melrose Alerting Service poller...');
  try {
    await smppClient.connect();
  } catch (error) {
    console.error('Failed to connect to SMPP provider at startup:', error);
  }

  const intervalMs = config.melrose.polling_interval_seconds * 1000;
  setInterval(async () => {
    const stats = await fetchMelroseStats();
    if (stats) await checkAndAlert(stats);
  }, intervalMs);
}

// Start HTTP server
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`UI Server listening on http://localhost:${PORT}`);
});

startPoller();
