with open('business_dashboard/templates/base.html', 'r') as f:
    content = f.read()

def wrap(content, html_pattern, perm):
    # This will wrap the specific li tag
    # Be careful not to replace too much
    import re
    # we need to find the specific <li> block for Dashboard, etc.
    return content

# Let's just do it manually with simple replaces
replacements = [
    (
        '<li><a href="{{ url_for(\'dashboard\') }}"',
        '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("dashboard") %}\n                <li><a href="{{ url_for(\'dashboard\') }}"'
    ),
    (
        '<li><a href="{{ url_for(\'create_po\') }}"',
        '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("create_po") %}\n                        <li><a href="{{ url_for(\'create_po\') }}"'
    ),
    (
        '<li><a href="{{ url_for(\'submitted_pos\') }}"',
        '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_pos") %}\n                        <li><a href="{{ url_for(\'submitted_pos\') }}"'
    ),
    (
        '<li><a href="{{ url_for(\'create_invoice\') }}"',
        '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("create_invoice") %}\n                        <li><a href="{{ url_for(\'create_invoice\') }}"'
    ),
    (
        '<li><a href="{{ url_for(\'po_status\') }}"',
        '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_pos") %}\n                        <li><a href="{{ url_for(\'po_status\') }}"'
    )
]

for old, new in replacements:
    content = content.replace(old, new)

# Close the ifs
content = content.replace(' Dashboard</a></li>', ' Dashboard</a></li>\n                {% endif %}')
content = content.replace(' Create PO</a></li>', ' Create PO</a></li>\n                        {% endif %}')
content = content.replace(' Submitted PO</a></li>', ' Submitted PO</a></li>\n                        {% endif %}')
content = content.replace(' Create Invoice</a></li>', ' Create Invoice</a></li>\n                        {% endif %}')
content = content.replace(' PO Status</a></li>', ' PO Status</a></li>\n                        {% endif %}')

# For whole sections (Transport, Inventory)
content = content.replace(
    '                    <a href="#" style="justify-content: space-between;">\n                        <span><i class="fas fa-truck" style="width: 20px;"></i> Transport</span>',
    '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("transport") %}\n                    <a href="#" style="justify-content: space-between;">\n                        <span><i class="fas fa-truck" style="width: 20px;"></i> Transport</span>'
)
content = content.replace(' Overview</a></li>\n                    </ul>\n                </li>\n                \n                <li>\n                    <a href="#" style="justify-content: space-between;">\n                        <span><i class="fas fa-boxes"', ' Overview</a></li>\n                    </ul>\n                </li>\n                {% endif %}\n                \n                <li>\n                    <a href="#" style="justify-content: space-between;">\n                        <span><i class="fas fa-boxes"')

content = content.replace(
    '                <li>\n                    <a href="#" style="justify-content: space-between;">\n                        <span><i class="fas fa-boxes" style="width: 20px;"></i> Inventory</span>',
    '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("inventory") %}\n                <li>\n                    <a href="#" style="justify-content: space-between;">\n                        <span><i class="fas fa-boxes" style="width: 20px;"></i> Inventory</span>'
)
content = content.replace(' Stock</a></li>\n                    </ul>\n                </li>\n                \n                {% if', ' Stock</a></li>\n                    </ul>\n                </li>\n                {% endif %}\n                \n                {% if')

with open('business_dashboard/templates/base.html', 'w') as f:
    f.write(content)
