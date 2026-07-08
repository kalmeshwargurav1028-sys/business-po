import re

with open('business_dashboard/templates/create_po.html', 'r') as f:
    c = f.read()

# I will wrap the financial columns in the table with Jinja ifs
c = re.sub(r'(<th.*?UNIT PRICE.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<th.*?SHIPPING.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<th.*?TAX.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<th.*?DISCOUNT.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<th.*?SUBTOTAL.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)

# And the td inputs
c = re.sub(r'(<td><input type="number" name="unit_price\[\]".*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% else %}<input type="hidden" name="unit_price[]" value="0">{% endif %}', c)
c = re.sub(r'(<td><input type="number" name="item_shipping\[\]".*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% else %}<input type="hidden" name="item_shipping[]" value="0">{% endif %}', c)
c = re.sub(r'(<td><input type="number" name="tax\[\]".*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% else %}<input type="hidden" name="tax[]" value="0">{% endif %}', c)
c = re.sub(r'(<td><input type="number" name="discount\[\]".*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% else %}<input type="hidden" name="discount[]" value="0">{% endif %}', c)
c = re.sub(r'(<td class="row-subtotal".*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)

# And the totals section at the bottom
c = c.replace('<div class="totals-section">', '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\n            <div class="totals-section">')
c = c.replace('<!-- End Totals Section -->', '<!-- End Totals Section -->\n            {% endif %}')

with open('business_dashboard/templates/create_po.html', 'w') as f:
    f.write(c)

with open('business_dashboard/templates/view_po.html', 'r') as f:
    c = f.read()

c = re.sub(r'(<th.*?UNIT PRICE.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<th.*?TOTAL.*?</th>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<td.*?₹\{\{ "%\.2f"\|format\(item\.get\(\'unit_price\'\, 0\)\|float\) \}\}.*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)
c = re.sub(r'(<td.*?₹\{\{ "%\.2f"\|format\(item\.get\(\'qty\'\, 0\)\|float \* item\.get\(\'unit_price\'\, 0\)\|float\) \}\}.*?</td>)', r'{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\1{% endif %}', c)

c = c.replace('<div style="width: 300px;">', '{% if session.get("user_role") == "Admin" or session.get("user_permissions", {}).get("view_financials") %}\n            <div style="width: 300px;">')
c = c.replace('<!-- Payment Terms -->', '{% endif %}\n            <!-- Payment Terms -->')

with open('business_dashboard/templates/view_po.html', 'w') as f:
    f.write(c)
