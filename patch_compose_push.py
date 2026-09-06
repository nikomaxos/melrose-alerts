import yaml

with open('docker-compose.yml', 'r') as f:
    config = yaml.safe_load(f)

volumes = config['services']['melrose-alerts'].get('volumes', [])
if './vapid_keys.json:/usr/src/app/vapid_keys.json' not in volumes:
    volumes.append('./vapid_keys.json:/usr/src/app/vapid_keys.json')
if './subscriptions.json:/usr/src/app/subscriptions.json' not in volumes:
    volumes.append('./subscriptions.json:/usr/src/app/subscriptions.json')

config['services']['melrose-alerts']['volumes'] = volumes

with open('docker-compose.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
