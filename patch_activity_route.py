import sys
with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

import re

old_activity_route = """@app.route('/activity')
@admin_required
def activity():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    logs = list(activity_collection.find().sort('timestamp', -1).limit(200))
    return render_template('activity.html', logs=logs)"""

new_activity_route = """@app.route('/activity')
@admin_required
def activity():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    user_filter = request.args.get('user_filter', '').strip()
    date_filter = request.args.get('date_filter', '').strip()
    action_type = request.args.get('action_type', '').strip()
    search = request.args.get('search', '').strip()
    
    query = {}
    
    if user_filter:
        query['user_name'] = {'$regex': user_filter, '$options': 'i'}
        
    if action_type:
        query['action'] = {'$regex': action_type, '$options': 'i'}
        
    if search:
        query['$or'] = [
            {'action': {'$regex': search, '$options': 'i'}},
            {'details': {'$regex': search, '$options': 'i'}},
            {'device': {'$regex': search, '$options': 'i'}}
        ]
        
    # Optional: implement date filter logic here if needed for exact dates
    
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    
    total_logs = activity_collection.count_documents(query)
    import math
    total_pages = math.ceil(total_logs / per_page) if total_logs > 0 else 1
    
    logs = list(activity_collection.find(query).sort('timestamp', -1).skip(skip).limit(per_page))
    
    return render_template('activity.html', 
                           logs=logs, 
                           page=page, 
                           total_pages=total_pages,
                           user_filter=user_filter,
                           date_filter=date_filter,
                           action_type=action_type,
                           search=search)"""

if old_activity_route in content:
    content = content.replace(old_activity_route, new_activity_route)
    with open('business_dashboard/app.py', 'w') as f:
        f.write(content)
    print("Patched activity route")
else:
    print("Could not find old_activity_route")
