with open('public/index.html', 'r') as f:
    html = f.read()

link_html = """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="margin: 0;">Melrose Alerts Setup</h2>
        <a href="/history.html" class="btn btn-secondary" style="background-color: #6c757d; text-decoration: none;">📋 View Alerts History</a>
    </div>
"""

html = html.replace("<h2>Melrose Alerts Setup</h2>", link_html)

with open('public/index.html', 'w') as f:
    f.write(html)
