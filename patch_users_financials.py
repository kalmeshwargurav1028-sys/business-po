with open('business_dashboard/templates/users.html', 'r') as f:
    content = f.read()

content = content.replace(
    '<hr style="border: 0; border-top: 1px solid #e2e8f0; width: 100%;">',
    '<hr style="border: 0; border-top: 1px solid #e2e8f0; width: 100%;">\n                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">\n                    <input type="checkbox" name="view_financials" id="perm_view_financials"> <strong>View Financial Amounts</strong>\n                </label>'
)

content = content.replace(
    "document.getElementById('perm_delete_data').checked = permissions.delete_data || false;",
    "document.getElementById('perm_delete_data').checked = permissions.delete_data || false;\n    document.getElementById('perm_view_financials').checked = permissions.view_financials || false;"
)

with open('business_dashboard/templates/users.html', 'w') as f:
    f.write(content)
