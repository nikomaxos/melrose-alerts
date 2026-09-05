with open('index.js', 'r') as f:
    code = f.read()

# Update fetch headers
old_fetch = """        'Authorization': `Bearer ${config.melrose.api_key}`,
        'Accept': 'application/json'"""
new_fetch = """        'Authorization': `Bearer ${config.melrose.api_key}`,
        'x-api-key': config.melrose.api_key,
        'Accept': 'application/json'"""
code = code.replace(old_fetch, new_fetch)

# Update checkAndAlert
old_check = """  const deliveryRate = stats.delivery_rate;
  const pendingMessages = stats.pending_messages || 0;"""
new_check = """  // Try to find delivery_rate and pending_messages in common JSON structures
  let deliveryRate = stats.delivery_rate ?? stats.deliveryRate ?? (stats.data && stats.data.delivery_rate);
  let pendingMessages = stats.pending_messages ?? stats.pendingMessages ?? (stats.data && stats.data.pending_messages) ?? 0;
  
  if (deliveryRate === undefined && stats.delivered && stats.total) {
      deliveryRate = (stats.delivered / stats.total) * 100;
  }
"""
code = code.replace(old_check, new_check)

with open('index.js', 'w') as f:
    f.write(code)
