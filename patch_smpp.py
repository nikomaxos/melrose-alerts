with open('smppClient.js', 'r') as f:
    code = f.read()

# Add lastError initialization
code = code.replace("this.connected = false;", "this.connected = false;\n    this.lastError = null;")

# Capture bind error
code = code.replace("const err = new Error(`Failed to bind. Status: ${pdu.command_status}`);", 
                    "const err = new Error(`Failed to bind. Status: ${pdu.command_status}`);\n            this.lastError = err.message;")

# Capture session error
code = code.replace("console.error('SMPP Session error:', error.message);", 
                    "console.error('SMPP Session error:', error.message);\n        this.lastError = error.message;")

# Clear error on successful connect
code = code.replace("this.connected = true;\n            resolve();",
                    "this.connected = true;\n            this.lastError = null;\n            resolve();")

# Write changes
with open('smppClient.js', 'w') as f:
    f.write(code)
