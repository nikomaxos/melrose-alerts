const fs = require('fs');
const YAML = require('yaml');
const SmppClient = require('./smppClient');

// Read config
const file = fs.readFileSync('./config.yaml', 'utf8');
const config = YAML.parse(file);

const smppClient = new SmppClient(config.smpp);

let lastAlertTime = 0;

async function fetchMelroseStats() {
  try {
    const response = await fetch(config.melrose.api_url, {
      headers: {
        'Authorization': `Bearer ${config.melrose.api_key}`,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      console.error(`API returned status ${response.status}`);
      return null;
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data from Melrose API:', error.message);
    return null;
  }
}

async function checkAndAlert(stats) {
  // Assuming the API returns a JSON object like { delivery_rate: 80.5 }
  // You might need to adjust this based on the actual API response structure
  const deliveryRate = stats.delivery_rate;

  if (deliveryRate === undefined) {
    console.warn('delivery_rate not found in API response');
    return;
  }

  console.log(`Current Delivery Rate: ${deliveryRate}%`);

  const threshold = config.alerting.delivery_rate_threshold_percent;
  if (deliveryRate < threshold) {
    const now = Date.now();
    const cooldownMs = config.alerting.alert_cooldown_minutes * 60 * 1000;

    if (now - lastAlertTime > cooldownMs) {
      console.log(`Delivery rate (${deliveryRate}%) is below threshold (${threshold}%). Sending alert...`);
      
      const message = `URGENT: Melrose Delivery Rate dropped to ${deliveryRate}%. Threshold is ${threshold}%.`;
      try {
        await smppClient.sendSMS(message);
        lastAlertTime = now;
        console.log('Alert sent successfully.');
      } catch (error) {
        console.error('Failed to send SMS alert:', error);
      }
    } else {
      console.log(`Delivery rate is low, but alert is in cooldown mode. (${Math.round((cooldownMs - (now - lastAlertTime)) / 1000 / 60)} minutes left)`);
    }
  } else {
    // If rate recovers, we could optionally reset the cooldown, but usually it's fine as is.
    console.log(`Delivery rate is healthy (>= ${threshold}%).`);
  }
}

async function start() {
  console.log('Starting Melrose Alerting Service...');
  
  try {
    await smppClient.connect();
  } catch (error) {
    console.error('Failed to connect to SMPP provider at startup:', error);
    // Continue anyway, as SMPP might come back online, or implement retry logic in client
  }

  const intervalMs = config.melrose.polling_interval_seconds * 1000;
  
  setInterval(async () => {
    const stats = await fetchMelroseStats();
    if (stats) {
      await checkAndAlert(stats);
    }
  }, intervalMs);

  // Run the first check immediately
  const stats = await fetchMelroseStats();
  if (stats) {
    await checkAndAlert(stats);
  }
}

start();
