import sys
with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

import re

old_log_func = """def log_activity(action, details=""):
    if not session.get('user_id'): return
    activity_collection.insert_one({
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name', 'Unknown'),
        'user_email': session.get('user_email', 'Unknown'),
        'role': session.get('user_role', 'Employee'),
        'action': action,
        'details': details,
        'timestamp': datetime.datetime.now()
    })"""

new_log_func = """def log_activity(action, details=""):
    if not session.get('user_id'): return
    
    device_info = "Unknown"
    try:
        if request.user_agent:
            browser = request.user_agent.browser.capitalize() if request.user_agent.browser else "Unknown Browser"
            platform = request.user_agent.platform.capitalize() if request.user_agent.platform else "Unknown OS"
            device_info = f"{browser} ({platform})"
    except:
        pass

    activity_collection.insert_one({
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name', 'Unknown'),
        'user_email': session.get('user_email', 'Unknown'),
        'role': session.get('user_role', 'Employee'),
        'action': action,
        'details': details,
        'device': device_info,
        'timestamp': datetime.datetime.now()
    })"""

if old_log_func in content:
    content = content.replace(old_log_func, new_log_func)
    with open('business_dashboard/app.py', 'w') as f:
        f.write(content)
    print("Patched log_activity")
else:
    print("Could not find old_log_func")
