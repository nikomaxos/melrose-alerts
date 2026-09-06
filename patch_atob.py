import re

with open('public/index.html', 'r') as f:
    html = f.read()

# Trim the string before padding
old_base64 = """    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);"""
        
new_base64 = """    function urlBase64ToUint8Array(base64String) {
        base64String = (base64String || '').trim();
        const padding = '='.repeat((4 - base64String.length % 4) % 4);"""

html = html.replace(old_base64, new_base64)

with open('public/index.html', 'w') as f:
    f.write(html)
