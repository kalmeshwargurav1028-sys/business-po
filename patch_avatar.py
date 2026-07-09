import sys
with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

# Remove session['user_photo_base64'] = photo_base64
content = content.replace("session['user_photo_base64'] = photo_base64", "session['has_custom_avatar'] = True")

# In verify_otp, add session['has_custom_avatar']
login_session_code = """
            session['user_email'] = user['email']
            session['user_role'] = user.get('role', 'Employee')
"""
new_login_session_code = """
            session['user_email'] = user['email']
            session['user_role'] = user.get('role', 'Employee')
            if user.get('photo_base64') or user.get('photo'):
                session['has_custom_avatar'] = True
"""
content = content.replace(login_session_code, new_login_session_code)

# Add the avatar route at the end of the file
avatar_route = """

@app.route('/api/user-avatar/<user_id>')
def user_avatar(user_id):
    from bson.objectid import ObjectId
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if user and user.get('photo_base64'):
            # photo_base64 is like data:image/jpeg;base64,/9j/4AAQSkZJRg...
            # We can just redirect to it or return it as a direct response
            # Actually, returning a data URI directly in an img src is usually done in the HTML
            # But since we want to serve it, we can parse it and return bytes.
            import base64
            data_uri = user['photo_base64']
            header, encoded = data_uri.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
            image_data = base64.b64decode(encoded)
            from flask import Response
            return Response(image_data, mimetype=mime_type)
    except:
        pass
    return "", 404
"""
content += avatar_route

with open('business_dashboard/app.py', 'w') as f:
    f.write(content)
print("Patched app.py")
