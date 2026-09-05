import re

with open('haproxy.cfg', 'r') as f:
    config = f.read()

# Add to http_front
if 'acl is_melrose_alerts' not in config:
    config = config.replace('use_backend staging_http if is_staging', 
                            'acl is_melrose_alerts hdr_end(host) -i melrose-alerts.globalnetservices.net\n        use_backend melrose_alerts_http if is_melrose_alerts\n        use_backend staging_http if is_staging')

# Add to https_front
if 'use_backend melrose_alerts_https' not in config:
    config = config.replace('use_backend staging_https if is_staging',
                            'acl is_melrose_alerts req_ssl_sni -i melrose-alerts.globalnetservices.net\n        use_backend melrose_alerts_https if is_melrose_alerts\n        use_backend staging_https if is_staging')

# Add backends at the end
if 'backend melrose_alerts_http' not in config:
    config += """\nbackend melrose_alerts_http
        mode http
        server melrose 10.10.10.110:80

backend melrose_alerts_https
        mode tcp
        server melrose 10.10.10.110:443\n"""

with open('haproxy.cfg.new', 'w') as f:
    f.write(config)
