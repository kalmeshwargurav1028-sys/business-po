with open('business_dashboard/templates/view_po.html', 'r') as f:
    c = f.read()

c = c.replace(
    '<div class="totals">',
    '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\n        <div class="totals">'
)

c = c.replace(
    '        <div class="notes">',
    '        {% endif %}\n        <div class="notes">'
)

with open('business_dashboard/templates/view_po.html', 'w') as f:
    f.write(c)
