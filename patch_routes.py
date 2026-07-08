import re

with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

def replace_route(content, route, decorator, replace_admin=False):
    pattern = r"(@app\.route\('"+route+r"'.*\n)(?:@admin_required\n)?" if replace_admin else r"(@app\.route\('"+route+r"'.*\n)"
    replacement = r"\1" + decorator + "\n"
    return re.sub(pattern, replacement, content)

# Dashboard
content = replace_route(content, '/dashboard', "@permission_required('dashboard')")

# POs
content = replace_route(content, '/create-po', "@permission_required('create_po')")
content = replace_route(content, '/add-vendor', "@permission_required('create_po')")
content = replace_route(content, '/submitted-pos', "@permission_required('view_pos')")
content = replace_route(content, '/po-status', "@permission_required('view_pos')")
content = replace_route(content, '/view-po/<po_id>', "@permission_required('view_pos')")

# Invoice
content = replace_route(content, '/create-invoice', "@permission_required('create_invoice')")

# Transport
content = replace_route(content, '/transport', "@permission_required('transport')")
content = replace_route(content, '/add-transport', "@permission_required('transport')")

# Inventory
content = replace_route(content, '/inventory', "@permission_required('inventory')")
content = replace_route(content, '/add-inventory', "@permission_required('inventory')")

# Deletes (replace admin_required)
content = replace_route(content, '/delete-po/<po_id>', "@permission_required('delete_data')", True)
content = replace_route(content, '/delete-po-dashboard/<po_id>', "@permission_required('delete_data')", True)
content = replace_route(content, '/delete-inventory/<item_id>', "@permission_required('delete_data')", True)

with open('business_dashboard/app.py', 'w') as f:
    f.write(content)
