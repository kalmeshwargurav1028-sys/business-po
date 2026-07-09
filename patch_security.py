import sys

with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

# Replace secret key and add session configs
old_config = "app.secret_key = 'business_dashboard_secret'\napp.config['UPLOAD_FOLDER']"
new_config = """import secrets
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER']"""

if old_config in content:
    content = content.replace(old_config, new_config)
else:
    print("Could not find old config")

# Add @app.after_request
security_headers = """
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
    return response

# Error handlers
"""
if "@app.after_request" not in content:
    # insert before error handlers or route definition. Let's find @app.route('/')
    if "@app.route('/')" in content:
        content = content.replace("@app.route('/')", security_headers + "@app.route('/')")

with open('business_dashboard/app.py', 'w') as f:
    f.write(content)
print("Patched security configs")
