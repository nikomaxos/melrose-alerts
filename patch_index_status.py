with open('index.js', 'r') as f:
    code = f.read()

status_endpoint = """
app.get('/api/status', (req, res) => {
  res.json({
    smpp_connected: smppClient.connected,
    smpp_last_error: smppClient.lastError || null
  });
});
"""

code = code.replace("app.get('/api/config'", status_endpoint + "\napp.get('/api/config'")

with open('index.js', 'w') as f:
    f.write(code)
