import re

with open('business_dashboard/templates/dashboard.html', 'r') as f:
    content = f.read()

# Replace inventory value
content = re.sub(
    r'<div class="stat-value">₹{{ "%\.2f"\|format\(inventory_value\|float\) }}</div>',
    '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}<div class="stat-value">₹{{ "%.2f"|format(inventory_value|float) }}</div>{% else %}<div class="stat-value">***</div>{% endif %}',
    content
)

# Replace total PO value
content = re.sub(
    r'Total PO Value: ₹{{ "%\.2f"\|format\(total_po_value\|float\) }}',
    '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}Total PO Value: ₹{{ "%.2f"|format(total_po_value|float) }}{% else %}Total PO Value: ***{% endif %}',
    content
)

with open('business_dashboard/templates/dashboard.html', 'w') as f:
    f.write(content)
