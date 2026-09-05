with open('haproxy.cfg', 'r') as f:
    config = f.read()

config += """
backend melrose_alerts_http
        mode http
        server melrose 10.10.10.110:80

backend melrose_alerts_https
        mode tcp
        server melrose 10.10.10.110:443
"""

with open('haproxy.cfg.new', 'w') as f:
    f.write(config)
