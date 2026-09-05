import yaml

with open('docker-compose.yml', 'r') as f:
    config = yaml.safe_load(f)

# Add volume for history
volumes = config['services']['melrose-alerts'].get('volumes', [])
if './alerts_history.json:/usr/src/app/alerts_history.json' not in volumes:
    volumes.append('./alerts_history.json:/usr/src/app/alerts_history.json')
config['services']['melrose-alerts']['volumes'] = volumes

with open('docker-compose.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
