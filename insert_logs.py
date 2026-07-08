import re

with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

# Login log
content = content.replace("session['user_permissions'] = user_data.get('permissions', {})", "session['user_permissions'] = user_data.get('permissions', {})\n            log_activity('Logged In', 'User authenticated successfully')")

# Create PO log
content = content.replace("flash('Purchase Order Created Successfully!', 'success')", "log_activity('Created PO', f'Created Purchase Order {po_number}')\n        flash('Purchase Order Created Successfully!', 'success')")

# Delete PO log
content = content.replace("flash('Purchase Order deleted successfully.', 'success')", "log_activity('Deleted PO', f'Deleted Purchase Order ID {po_id}')\n    flash('Purchase Order deleted successfully.', 'success')")

# Create Invoice log
content = content.replace("flash('Invoice generated successfully!', 'success')", "log_activity('Created Invoice', f'Generated invoice for {request.form.get(\"customer_name\")}')\n        flash('Invoice generated successfully!', 'success')")

# Add Inventory log
content = content.replace("flash('Item added to inventory successfully!', 'success')", "log_activity('Added Inventory', f'Added item {name} (SKU: {sku})')\n    flash('Item added to inventory successfully!', 'success')")

# Delete Inventory log
content = content.replace("flash('Item deleted successfully.', 'success')", "log_activity('Deleted Inventory', f'Deleted inventory item ID {item_id}')\n    flash('Item deleted successfully.', 'success')")

with open('business_dashboard/app.py', 'w') as f:
    f.write(content)
