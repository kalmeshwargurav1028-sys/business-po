with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

# Add activity_collection
content = content.replace("settings_collection = db['settings']", "settings_collection = db['settings']\nactivity_collection = db['activity_logs']")

# Add log_activity function after send_otp_email
log_activity_fn = """
def log_activity(action, details=""):
    if not session.get('user_id'): return
    activity_collection.insert_one({
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name', 'Unknown'),
        'user_email': session.get('user_email', 'Unknown'),
        'role': session.get('user_role', 'Employee'),
        'action': action,
        'details': details,
        'timestamp': datetime.datetime.now()
    })
"""
content = content.replace("def send_otp_email(to_email, otp_code):", log_activity_fn + "\ndef send_otp_email(to_email, otp_code):")

# Update default permissions in login
content = content.replace("'inventory': False, 'transport': False, 'delete_data': False", "'inventory': False, 'transport': False, 'delete_data': False, 'view_financials': False")

# Update default permissions in register
content = content.replace("'inventory': False, 'transport': False, 'delete_data': False}", "'inventory': False, 'transport': False, 'delete_data': False, 'view_financials': False}")

# Update update_permissions route
content = content.replace("'delete_data': request.form.get('delete_data') == 'on'", "'delete_data': request.form.get('delete_data') == 'on',\n        'view_financials': request.form.get('view_financials') == 'on'")

with open('business_dashboard/app.py', 'w') as f:
    f.write(content)
