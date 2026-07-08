with open('business_dashboard/templates/users.html', 'r') as f:
    content = f.read()

replacement = """
                        {% if session.get('user_id') != u._id %}
                        <div style="display: flex; gap: 8px;">
                            <form action="{{ url_for('update_role', user_id=u._id) }}" method="POST" style="display: flex; gap: 8px;">
                                <select name="role" class="form-control" style="width: 120px; padding: 4px 8px;">
                                    <option value="Employee" {% if u.get('role', 'Employee') == 'Employee' %}selected{% endif %}>Employee</option>
                                    <option value="Admin" {% if u.get('role', 'Employee') == 'Admin' %}selected{% endif %}>Admin</option>
                                </select>
                                <button type="submit" class="btn btn-primary" style="padding: 4px 12px; font-size: 0.8rem;">Role</button>
                            </form>
                            {% if u.get('role', 'Employee') == 'Employee' %}
                            <button type="button" class="btn" style="padding: 4px 12px; font-size: 0.8rem; background: white; border: 1px solid #cbd5e1; cursor: pointer;" onclick='openPermModal("{{ u._id }}", "{{ u.name }}", {{ u.get("permissions", {}) | tojson }})'>Permissions</button>
                            {% endif %}
                        </div>
                        {% else %}
"""

content = content.replace("""
                        {% if session.get('user_id') != u._id %}
                        <form action="{{ url_for('update_role', user_id=u._id) }}" method="POST" style="display: flex; gap: 8px;">
                            <select name="role" class="form-control" style="width: 120px; padding: 4px 8px;">
                                <option value="Employee" {% if u.get('role', 'Employee') == 'Employee' %}selected{% endif %}>Employee</option>
                                <option value="Admin" {% if u.get('role', 'Employee') == 'Admin' %}selected{% endif %}>Admin</option>
                            </select>
                            <button type="submit" class="btn btn-primary" style="padding: 4px 12px; font-size: 0.8rem;">Update</button>
                        </form>
                        {% else %}
""", replacement)

modal = """
<!-- Permissions Modal -->
<div id="permModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
    <div style="background: white; width: 400px; margin: 100px auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h3 style="margin: 0;">Permissions: <span id="permUserName"></span></h3>
            <button onclick="document.getElementById('permModal').style.display='none'" style="background: none; border: none; cursor: pointer; font-size: 1.2rem;">&times;</button>
        </div>
        <form id="permForm" method="POST">
            <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem;">
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" name="dashboard" id="perm_dashboard"> View Dashboard
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" name="create_po" id="perm_create_po"> Create Purchase Orders
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" name="view_pos" id="perm_view_pos"> View Historical POs & Status
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" name="create_invoice" id="perm_create_invoice"> Create Invoices
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" name="inventory" id="perm_inventory"> Manage Inventory
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="checkbox" name="transport" id="perm_transport"> Manage Transport
                </label>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; width: 100%;">
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; color: #ef4444; font-weight: 600;">
                    <input type="checkbox" name="delete_data" id="perm_delete_data"> Allow Deleting Data (DANGER)
                </label>
            </div>
            <div style="text-align: right;">
                <button type="button" onclick="document.getElementById('permModal').style.display='none'" style="padding: 0.5rem 1rem; border: 1px solid #cbd5e1; background: white; border-radius: 4px; cursor: pointer; margin-right: 0.5rem;">Cancel</button>
                <button type="submit" class="btn btn-primary" style="padding: 0.5rem 1rem;">Save Permissions</button>
            </div>
        </form>
    </div>
</div>

<script>
function openPermModal(userId, userName, permissions) {
    document.getElementById('permUserName').innerText = userName;
    document.getElementById('permForm').action = '/update-permissions/' + userId;
    
    // Reset checkboxes
    document.getElementById('perm_dashboard').checked = permissions.dashboard || false;
    document.getElementById('perm_create_po').checked = permissions.create_po || false;
    document.getElementById('perm_view_pos').checked = permissions.view_pos || false;
    document.getElementById('perm_create_invoice').checked = permissions.create_invoice || false;
    document.getElementById('perm_inventory').checked = permissions.inventory || false;
    document.getElementById('perm_transport').checked = permissions.transport || false;
    document.getElementById('perm_delete_data').checked = permissions.delete_data || false;
    
    document.getElementById('permModal').style.display = 'block';
}
</script>
{% endblock %}
"""

content = content.replace("{% endblock %}", modal)

with open('business_dashboard/templates/users.html', 'w') as f:
    f.write(content)
