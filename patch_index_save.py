with open('index.js', 'r') as f:
    code = f.read()

old_save = """    // Merge updates
    config.smpp = newConfig.smpp;
    config.profiles = newConfig.profiles || [];"""

new_save = """    // Merge updates
    config.smpp = newConfig.smpp;
    config.profiles = newConfig.profiles || [];
    if (newConfig.melrose) {
        config.melrose = newConfig.melrose;
    }"""

code = code.replace(old_save, new_save)

with open('index.js', 'w') as f:
    f.write(code)
