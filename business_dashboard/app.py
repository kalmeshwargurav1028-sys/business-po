from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime
import random
import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from functools import wraps

def admin_required(f):
    # Decorator to enforce admin role
    # Trigger final Vercel deployment
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_portal'))
        if session.get('user_role') != 'Admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                fallback = 'admin_portal' if session.get('login_type') == 'admin' else 'login'
                return redirect(url_for(fallback))
            if session.get('user_role') == 'Admin':
                return f(*args, **kwargs)
            
            user_perms = session.get('user_permissions', {})
            if not user_perms.get(permission_name):
                flash('Access denied. You do not have permission to view this feature.', 'error')
                if request.endpoint == 'dashboard':
                    return redirect(url_for('login'))
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_activity(action, details=""):
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
    })

import threading

def send_otp_email_async(to_email, otp_code):
    # Using the Office 365 credentials provided
    sender_email = "agent4@indusschool.com"
    sender_password = "Agent@2026"
        
    try:
        msg = MIMEText(f"Your login OTP is: {otp_code}")
        msg['Subject'] = 'Your Login OTP - Business Portal'
        msg['From'] = sender_email
        msg['To'] = to_email
        
        # Office 365 uses STARTTLS on port 587
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.ehlo()
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_otp_email(to_email, otp_code):
    # Vercel is a serverless environment which freezes the execution context
    # once the HTTP response is returned. Background threads will be paused,
    # causing emails to fail. We must send the email synchronously.
    send_otp_email_async(to_email, otp_code)
    return True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
import secrets
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads/profiles')
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except OSError:
    pass # Vercel has a read-only filesystem, ignore the error

import certifi

# Connect to MongoDB
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
db = client['business_dashboard_db']
users_collection = db['users']
vendors_collection = db['vendors']
po_collection = db['purchase_orders']
invoices_collection = db['invoices']
inventory_collection = db['inventory']
transport_collection = db['transport']
settings_collection = db['settings']
activity_collection = db['activity_logs']
tasks_collection = db['tasks']

@app.context_processor
def inject_settings():
    try:
        settings = settings_collection.find_one({'type': 'global'})
    except Exception:
        settings = None
        return dict(global_settings={'business_name': "Business Dashboard", 'email': '', 'phone': '', 'address': '', 'tax_id': '', 'mode': 'business'})
        
    if not settings:
        settings = {
            'type': 'global',
            'business_name': 'Your Business Name',
            'email': '',
            'phone': '',
            'address': '',
            'tax_id': '',
            'mode': 'business'
        }
        settings_collection.insert_one(settings)
    return dict(global_settings=settings)

def process_login_request(template_name, expected_login_type):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        login_type = request.form.get('login_type', expected_login_type)
        
        # Brute Force Protection Check
        fifteen_mins_ago = datetime.datetime.now() - datetime.timedelta(minutes=15)
        failed_attempts = activity_collection.count_documents({
            'action': 'Login Failed',
            'user_email': email,
            'timestamp': {'$gte': fifteen_mins_ago}
        })
        
        if failed_attempts >= 5:
            flash('Too many failed login attempts. Please try again after 15 minutes.', 'error')
            return render_template(template_name)
        
        try:
            user = users_collection.find_one({'email': email})
        except Exception as e:
            flash(f"Database Error: {str(e)}", 'error')
            return redirect(request.url)
        
        if user and check_password_hash(user['password'], password):
            user_role = user.get('role', 'Employee')
            
            # Enforce strict portal separation
            if login_type == 'admin' and user_role != 'Admin':
                flash('Access denied. Please use the Employee Portal.', 'error')
                return redirect(url_for('login'))
                
            if login_type == 'employee' and user_role == 'Admin':
                flash('Access denied. Administrators must log in through the Admin Portal.', 'error')
                return redirect(url_for('admin_portal'))
                
            otp = str(random.randint(100000, 999999))
            
            session['temp_user'] = {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user.get('email', ''),
                'role': user.get('role', 'Employee'),
                'phone': user.get('phone', ''),
                'permissions': user.get('permissions', {
                    'dashboard': True, 'create_po': False, 'view_pos': False,
                    'create_invoice': False, 'inventory': False, 'transport': False, 'delete_data': False, 'view_financials': False
                })
            }
            session['login_type'] = login_type
            session['otp'] = otp
            session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()
            
            send_otp_email(email, otp)
            return redirect(url_for('verify_otp'))
        else:
            # Log failure to activity_collection
            device_info = "Unknown"
            try:
                if request.user_agent:
                    browser = request.user_agent.browser.capitalize() if request.user_agent.browser else "Unknown Browser"
                    platform = request.user_agent.platform.capitalize() if request.user_agent.platform else "Unknown OS"
                    device_info = f"{browser} ({platform})"
            except:
                pass
                
            activity_collection.insert_one({
                'user_id': None,
                'user_name': 'Unknown',
                'user_email': email,
                'role': 'Unknown',
                'action': 'Login Failed',
                'details': f'Invalid password (attempt {failed_attempts + 1})',
                'device': device_info,
                'timestamp': datetime.datetime.now()
            })
            flash('Invalid email or password', 'error')
            
    return render_template(template_name)


def number_to_words(n):
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    
    def convert(n):
        if n == 0: return ""
        elif n < 10: return ones[n]
        elif n < 20: return teens[n - 10]
        elif n < 100: return tens[n // 10] + (" " + ones[n % 10] if (n % 10) != 0 else "")
        elif n < 1000: return ones[n // 100] + " Hundred" + ((" and " + convert(n % 100)) if (n % 100) != 0 else "")
        elif n < 100000: return convert(n // 1000) + " Thousand" + ((" " + convert(n % 1000)) if (n % 1000) != 0 else "")
        elif n < 10000000: return convert(n // 100000) + " Lakh" + ((" " + convert(n % 100000)) if (n % 100000) != 0 else "")
        else: return convert(n // 10000000) + " Crore" + ((" " + convert(n % 10000000)) if (n % 10000000) != 0 else "")

    if n == 0: return "Zero Rupees"
    try:
        val = int(float(n))
        return convert(val).strip() + " Rupees"
    except:
        return "Unknown"

app.jinja_env.filters['num_words'] = number_to_words

@app.route('/view-invoice/<inv_id>')
def view_invoice(inv_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    from bson.objectid import ObjectId
    inv = invoices_collection.find_one({'_id': ObjectId(inv_id)})
    if not inv:
        flash('Invoice not found.', 'error')
        return redirect(url_for('invoices'))
    vendor = vendors_collection.find_one({'_id': ObjectId(inv.get('vendor_id'))})
    return render_template('view_invoice.html', inv=inv, vendor=vendor)

@app.route('/', methods=['GET', 'POST'])
def login():
    return process_login_request('login.html', 'employee')

@app.route('/admin-portal', methods=['GET', 'POST'])
def admin_portal():
    return process_login_request('admin_login.html', 'admin')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    login_type = session.get('login_type', 'employee')
    fallback_route = 'admin_portal' if login_type == 'admin' else 'login'

    if 'temp_user' not in session or 'otp' not in session:
        return redirect(url_for(fallback_route))
        
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        expiry = session.get('otp_expiry', 0)
        
        if datetime.datetime.now().timestamp() > expiry:
            flash('OTP has expired. Please login again.', 'error')
            session.pop('temp_user', None)
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('login_type', None)
            return redirect(url_for(fallback_route))
            
        if entered_otp == session.get('otp'):
            user_data = session.pop('temp_user')
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('login_type', None)
            
            # Fetch full user from DB to get photo (avoiding large session cookie)
            from bson.objectid import ObjectId
            db_user = users_collection.find_one({'_id': ObjectId(user_data['id'])})
            
            session['logged_in'] = True
            session['user_id'] = user_data['id']
            session['user_name'] = user_data['name']
            session['user_email'] = user_data['email']
            session['user_role'] = user_data['role']
            session['user_phone'] = user_data['phone']
            if db_user:
                session['user_photo'] = db_user.get('photo', '')
                if db_user.get('photo_base64'):
                    session['has_custom_avatar'] = True
            session['user_permissions'] = user_data.get('permissions', {})
            log_activity('Logged In', 'User authenticated successfully')
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP code. Please try again.', 'error')
            
    return render_template('verify_otp.html')

@app.route('/dashboard')
@permission_required('dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    # Calculate stats
    inventory_items = list(inventory_collection.find())
    total_inventory = len(inventory_items)
    inventory_value = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in inventory_items)
    low_stock = sum(1 for item in inventory_items if 0 < item.get('quantity', 0) <= item.get('reorder_level', 0))
    out_of_stock = sum(1 for item in inventory_items if item.get('quantity', 0) == 0)
    
    total_vendors = vendors_collection.count_documents({})
    
    pos = list(po_collection.find().sort('date_created', -1))
    total_pos = len(pos)
    total_po_value = sum(po.get('total', 0) for po in pos)
    
    recent_pos = pos[:5]
    total_transport = transport_collection.count_documents({})
    
    template_name = 'admin_dashboard.html' if session.get('user_role') == 'Admin' else 'employee_dashboard.html'
    
    recent_employee_logs = []
    total_logs = 0
    page = request.args.get('page', 1, type=int)
    emp_search = request.args.get('emp_search', '')
    action_filter = request.args.get('action_filter', '')
    per_page = 15
    total_pages = 1
    
    if template_name == 'admin_dashboard.html':
        query = {'role': 'Employee'}
        if emp_search:
            query['user_name'] = {'$regex': emp_search, '$options': 'i'}
        if action_filter:
            query['action'] = action_filter
            
        total_logs = activity_collection.count_documents(query)
        total_pages = max(1, (total_logs + per_page - 1) // per_page)
        page = min(page, total_pages)
        
        recent_employee_logs = list(activity_collection.find(query)
                                    .sort('timestamp', -1)
                                    .skip((page - 1) * per_page)
                                    .limit(per_page))
    
    return render_template(template_name, 
                           page=page,
                           total_pages=total_pages,
                           emp_search=emp_search,
                           action_filter=action_filter,
                           total_inventory=total_inventory, 
                           inventory_value=inventory_value,
                           low_stock=low_stock,
                           out_of_stock=out_of_stock,
                           total_vendors=total_vendors,
                           total_pos=total_pos,
                           total_po_value=total_po_value,
                           recent_pos=recent_pos,
                           total_transport=total_transport,
                           recent_employee_logs=recent_employee_logs)

@app.route('/create-po', methods=['GET', 'POST'])
@permission_required('create_po')
def create_po():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        po_number = request.form.get('po_number')
        po_date = request.form.get('po_date')
        expected_delivery = request.form.get('expected_delivery')
        payment_terms = request.form.get('payment_terms')
        
        vendor_id = request.form.get('vendor')
        ship_to = request.form.get('ship_to')
        notes = request.form.get('notes')
        
        # Items arrays
        item_names = request.form.getlist('item_name[]')
        descriptions = request.form.getlist('description[]')
        qtys = request.form.getlist('qty[]')
        unit_prices = request.form.getlist('unit_price[]')
        shippings = request.form.getlist('item_shipping[]')
        taxes = request.form.getlist('tax[]')
        discounts = request.form.getlist('discount[]')
        
        items = []
        for i in range(len(item_names)):
            if item_names[i].strip():
                items.append({
                    'name': item_names[i],
                    'description': descriptions[i] if i < len(descriptions) else '',
                    'qty': float(qtys[i]) if i < len(qtys) and qtys[i] else 0,
                    'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                    'shipping': float(shippings[i]) if i < len(shippings) and shippings[i] else 0,
                    'tax': float(taxes[i]) if i < len(taxes) and taxes[i] else 0,
                    'discount': float(discounts[i]) if i < len(discounts) and discounts[i] else 0
                })
        
        subtotal = request.form.get('subtotal', 0)
        total_shipping = request.form.get('total_shipping', 0)
        total_tax = request.form.get('total_tax', 0)
        total_discount = request.form.get('total_discount', 0)
        total = float(request.form.get('total', 0))
        action = request.form.get('action', 'generated')
        
        status = 'draft' if action == 'draft' else 'generated'
        
        # Enforce Spending Limits for Employees
        if session.get('user_role') != 'Admin' and action != 'draft':
            spending_limit = session.get('user_permissions', {}).get('spending_limit')
            if spending_limit is not None and total > spending_limit:
                status = 'pending_approval'
        
        po_collection.insert_one({
            'po_number': po_number,
            'po_date': po_date,
            'expected_delivery': expected_delivery,
            'payment_terms': payment_terms,
            'vendor_id': vendor_id,
            'ship_to': ship_to,
            'notes': notes,
            'items': items,
            'subtotal': float(subtotal),
            'total_shipping': float(total_shipping),
            'total_tax': float(total_tax),
            'total_discount': float(total_discount),
            'total': total,
            'status': status,
            'created_by': session.get('user_id'),
            'date_created': datetime.datetime.now()
        })
        
        if action == 'draft':
            flash('Purchase Order saved as draft successfully!', 'success')
        elif status == 'pending_approval':
            flash(f'Purchase Order submitted and is Pending Approval (Exceeds limit of ${spending_limit:,.2f})', 'warning')
        else:
            flash('Purchase Order generated successfully!', 'success')
            
        return redirect(url_for('create_po'))
        
    vendors = list(vendors_collection.find())
    for v in vendors:
        v['_id'] = str(v['_id'])
        
    total_pos = po_collection.count_documents({})
    pipeline = [{"$group": {"_id": None, "total_amount": {"$sum": "$total"}}}]
    result = list(po_collection.aggregate(pipeline))
    total_amount = result[0]['total_amount'] if result else 0
    
    recent_pos = list(po_collection.find().sort("date_created", -1).limit(10))
    for po in recent_pos:
        po['_id'] = str(po['_id'])
        
    po_number = f"PO-{datetime.datetime.now().year}-{total_pos}"
    return render_template('create_po.html', vendors=vendors, po_number=po_number, total_pos=total_pos, total_amount=total_amount, recent_pos=recent_pos)

@app.route('/delete-po/<po_id>', methods=['POST'])
@permission_required('delete_data')
def delete_po(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    po_collection.delete_one({'_id': ObjectId(po_id)})
    flash('Purchase order deleted successfully!', 'success')
    return redirect(url_for('create_po'))

@app.route('/approve-po/<po_id>', methods=['POST'])
def approve_po(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Check if admin or has approve_pos permission
    if session.get('user_role') != 'Admin' and not session.get('user_permissions', {}).get('approve_pos'):
        flash('You do not have permission to approve Purchase Orders.', 'error')
        return redirect(url_for('submitted_pos'))
        
    from bson.objectid import ObjectId
    po_collection.update_one({'_id': ObjectId(po_id)}, {'$set': {'status': 'generated'}})
    log_activity('Approved PO', f'Approved Purchase Order ID {po_id}')
    flash('Purchase order approved successfully!', 'success')
    return redirect(url_for('submitted_pos'))

@app.route('/view-po/<po_id>')
@permission_required('view_pos')
def view_po(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    po = po_collection.find_one({'_id': ObjectId(po_id)})
    
    if not po:
        flash('Purchase order not found.', 'error')
        return redirect(url_for('create_po'))
        
    # Get vendor details
    vendor = vendors_collection.find_one({'_id': ObjectId(po.get('vendor_id'))})
    
    return render_template('view_po.html', po=po, vendor=vendor)

@app.route('/delete-po-dashboard/<po_id>')
@permission_required('delete_data')
def delete_po_dashboard(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    try:
        po_collection.delete_one({'_id': ObjectId(po_id)})
        log_activity('Deleted PO', f'Deleted Purchase Order ID {po_id}')
        flash('Purchase Order deleted successfully.', 'success')
    except Exception as e:
        flash('Failed to delete Purchase Order.', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/add-vendor', methods=['GET', 'POST'])
@permission_required('create_po')
def add_vendor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('vendor_name')
        email = request.form.get('vendor_email')
        phone = request.form.get('vendor_phone')
        address = request.form.get('vendor_address')
        
        vendors_collection.insert_one({
            'name': name,
            'email': email,
            'phone': phone,
            'address': address
        })
        flash('Vendor added successfully!', 'success')
        return redirect(url_for('create_po'))
        
    return render_template('add_vendor.html')

@app.route('/api/vendor/<vendor_id>')
def get_vendor(vendor_id):
    from bson.objectid import ObjectId
    from bson.errors import InvalidId
    from flask import jsonify
    try:
        vendor = vendors_collection.find_one({'_id': ObjectId(vendor_id)})
        if vendor:
            return jsonify({'success': True, 'phone': vendor.get('phone', ''), 'address': vendor.get('address', ''), 'email': vendor.get('email', '')})
    except InvalidId:
        # Fallback if ID is a custom string
        vendor = vendors_collection.find_one({'_id': vendor_id})
        if vendor:
            return jsonify({'success': True, 'phone': vendor.get('phone', ''), 'address': vendor.get('address', ''), 'email': vendor.get('email', '')})
    return jsonify({'success': False})

@app.route('/submitted-pos')
@permission_required('view_pos')
def submitted_pos():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    all_pos = list(po_collection.find().sort("date_created", -1))
    
    # Map vendor IDs to names
    vendors = {str(v['_id']): v['name'] for v in vendors_collection.find()}
    
    total_pos = len(all_pos)
    approved_count = 0
    
    for po in all_pos:
        po['_id'] = str(po['_id'])
        po['vendor_name'] = vendors.get(po.get('vendor_id'), 'Unknown Vendor')
        po['items_count'] = sum(1 for item in po.get('items', []) if isinstance(item, dict))
        
        internal_status = po.get('status', 'generated')
        if internal_status == 'draft':
            po['display_status'] = 'Draft'
        elif internal_status == 'pending_approval':
            po['display_status'] = 'Pending Approval'
        else:
            po['display_status'] = 'Approved'
            approved_count += 1
            
    return render_template('submitted_pos.html', pos=all_pos, total_pos=total_pos, approved_count=approved_count)

@app.route('/invoices')
@permission_required('create_invoice')
def invoices():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    all_invoices = list(invoices_collection.find().sort("date_created", -1))
    vendors = {str(v['_id']): v['name'] for v in vendors_collection.find()}
    
    total_invoices = len(all_invoices)
    finalized_count = 0
    
    for inv in all_invoices:
        inv['_id'] = str(inv['_id'])
        inv['vendor_name'] = vendors.get(inv.get('vendor_id'), 'Unknown Customer')
        if inv.get('doc_status') == 'generated':
            finalized_count += 1
            
    return render_template('invoices.html', invoices=all_invoices, total=total_invoices, finalized=finalized_count)

@app.route('/finalize-invoice/<inv_id>', methods=['POST'])
def finalize_invoice(inv_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if session.get('user_role') != 'Admin' and not session.get('user_permissions', {}).get('finalize_invoices'):
        flash('You do not have permission to finalize invoices.', 'error')
        return redirect(url_for('invoices'))
        
    from bson.objectid import ObjectId
    invoices_collection.update_one({'_id': ObjectId(inv_id)}, {'$set': {'doc_status': 'generated'}})
    log_activity('Finalized Invoice', f'Finalized Invoice ID {inv_id}')
    flash('Invoice finalized successfully!', 'success')
    return redirect(url_for('invoices'))

@app.route('/create-invoice', methods=['GET', 'POST'])
@permission_required('create_invoice')
def create_invoice():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        invoice_number = request.form.get('invoice_number')
        invoice_date = request.form.get('invoice_date')
        due_date = request.form.get('due_date')
        status = request.form.get('status')
        linked_po = request.form.get('linked_po')
        payment_terms = request.form.get('payment_terms')
        
        vendor_id = request.form.get('vendor')
        billing_address = request.form.get('billing_address')
        contact_info = request.form.get('contact_info')
        notes = request.form.get('notes')
        
        # Items arrays
        item_names = request.form.getlist('item_name[]')
        descriptions = request.form.getlist('description[]')
        qtys = request.form.getlist('qty[]')
        unit_prices = request.form.getlist('unit_price[]')
        taxes = request.form.getlist('tax[]')
        discounts = request.form.getlist('discount[]')
        
        items = []
        for i in range(len(item_names)):
            if item_names[i].strip():
                items.append({
                    'name': item_names[i],
                    'description': descriptions[i] if i < len(descriptions) else '',
                    'qty': float(qtys[i]) if i < len(qtys) and qtys[i] else 0,
                    'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                    'tax': float(taxes[i]) if i < len(taxes) and taxes[i] else 0,
                    'discount': float(discounts[i]) if i < len(discounts) and discounts[i] else 0
                })
        
        subtotal = request.form.get('subtotal', 0)
        total_tax = request.form.get('total_tax', 0)
        total_discount = request.form.get('total_discount', 0)
        total = request.form.get('total', 0)
        action = request.form.get('action', 'generated')
        
        invoices_collection.insert_one({
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'status': status,
            'linked_po': linked_po,
            'payment_terms': payment_terms,
            'vendor_id': vendor_id,
            'billing_address': billing_address,
            'contact_info': contact_info,
            'notes': notes,
            'items': items,
            'subtotal': float(subtotal),
            'total_tax': float(total_tax),
            'total_discount': float(total_discount),
            'total': float(total),
            'doc_status': 'draft' if action == 'draft' else 'generated',
            'created_by': session.get('user_id'),
            'date_created': datetime.datetime.now()
        })
        
        if action == 'draft':
            flash('Invoice saved as draft successfully!', 'success')
        else:
            log_activity('Created Invoice', f'Generated invoice for {request.form.get("customer_name")}')
        flash('Invoice generated successfully!', 'success')
            
        return redirect(url_for('create_invoice'))
        
    vendors = list(vendors_collection.find())
    for v in vendors:
        v['_id'] = str(v['_id'])
        
    pos = list(po_collection.find().sort("date_created", -1))
    for po in pos:
        po['_id'] = str(po['_id'])
        
    total_invoices = invoices_collection.count_documents({})
    invoice_number = f"INV-{datetime.datetime.now().year}-{total_invoices}"
    return render_template('create_invoice.html', vendors=vendors, invoice_number=invoice_number, pos=pos)

@app.route('/po-status')
@permission_required('view_pos')
def po_status():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    search_query = request.args.get('q', '').strip()
    
    # Map vendor IDs to names
    vendors = {str(v['_id']): v['name'] for v in vendors_collection.find()}
    
    all_pos = list(po_collection.find().sort("date_created", -1))
    for po in all_pos:
        po['_id'] = str(po['_id'])
        po['vendor_name'] = vendors.get(po.get('vendor_id'), 'Unknown Vendor')
        po['tracking_step'] = po.get('tracking_step', 1)
        
        # Determine Display Status based on tracking step
        if po['tracking_step'] <= 2:
            po['display_status'] = 'Pending'
        elif po['tracking_step'] == 3:
            po['display_status'] = 'Approved'
        elif po['tracking_step'] == 4:
            po['display_status'] = 'Shipped'
        else:
            po['display_status'] = 'Delivered'
            
    # Find active PO
    active_po = None
    if search_query:
        active_po = next((po for po in all_pos if po.get('po_number') == search_query), None)
    
    # Default to first PO if no search or not found
    if not active_po and all_pos:
        active_po = all_pos[0]
        
    recent_pos = all_pos[:5] # Top 5 recent for bottom list
    
    return render_template('po_status.html', active_po=active_po, recent_pos=recent_pos, search_query=search_query)

@app.route('/update-po-status/<po_id>', methods=['POST'])
def update_po_status(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    po = po_collection.find_one({'_id': ObjectId(po_id)})
    if po:
        current_step = po.get('tracking_step', 1)
        if current_step < 5:
            po_collection.update_one({'_id': ObjectId(po_id)}, {'$set': {'tracking_step': current_step + 1}})
            flash('PO tracking status updated successfully!', 'success')
            
    # Redirect back to the tracking page for this PO
    return redirect(url_for('po_status', q=po.get('po_number') if po else ''))



@app.route('/transport')
@permission_required('transport')
def transport():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    shipments = list(transport_collection.find().sort('date_added', -1))
    
    # Calculate stats
    total_shipments = len(shipments)
    in_transit = sum(1 for s in shipments if s.get('status') == 'In Transit')
    delivered = sum(1 for s in shipments if s.get('status') == 'Delivered')
    preparing = sum(1 for s in shipments if s.get('status') == 'Preparing')
    
    return render_template('transport.html', shipments=shipments, total=total_shipments, in_transit=in_transit, delivered=delivered, preparing=preparing)

@app.route('/add-transport', methods=['POST'])
@permission_required('transport')
def add_transport():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    tracking_number = request.form.get('tracking_number')
    courier = request.form.get('courier')
    destination = request.form.get('destination')
    status = request.form.get('status', 'Preparing')
    notes = request.form.get('notes', '')
    
    transport_collection.insert_one({
        'tracking_number': tracking_number,
        'courier': courier,
        'destination': destination,
        'status': status,
        'notes': notes,
        'date_added': datetime.datetime.now()
    })
    flash('Shipment tracked successfully!', 'success')
    return redirect(url_for('transport'))

@app.route('/update-transport-status/<shipment_id>', methods=['POST'])
def update_transport_status(shipment_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    status = request.form.get('status')
    from bson.objectid import ObjectId
    transport_collection.update_one({'_id': ObjectId(shipment_id)}, {'$set': {'status': status}})
    flash('Shipment status updated!', 'success')
    return redirect(url_for('transport'))


@app.route('/inventory')
@permission_required('inventory')
def inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    items = list(inventory_collection.find())
    
    total_items = len(items)
    in_stock = 0
    low_stock = 0
    out_of_stock = 0
    
    for item in items:
        qty = item.get('quantity', 0)
        reorder = item.get('reorder_level', 0)
        item['stock_value'] = qty * item.get('unit_price', 0)
        
        if qty == 0:
            out_of_stock += 1
            item['status'] = 'Out of Stock'
        elif qty <= reorder:
            low_stock += 1
            item['status'] = 'Low Stock'
        else:
            in_stock += 1
            item['status'] = 'In Stock'
            
    return render_template('inventory.html', items=items, total=total_items, in_stock=in_stock, low_stock=low_stock, out_stock=out_of_stock)

@app.route('/delete-inventory/<item_id>', methods=['POST'])
@permission_required('delete_data')
def delete_inventory(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    inventory_collection.delete_one({'_id': ObjectId(item_id)})
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('inventory'))

@app.route('/add-inventory', methods=['POST'])
@permission_required('inventory')
def add_inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    name = request.form.get('name')
    sku = request.form.get('sku')
    category = request.form.get('category')
    quantity = int(request.form.get('quantity', 0))
    reorder_level = int(request.form.get('reorder_level', 0))
    unit_price = float(request.form.get('unit_price', 0))
    
    inventory_collection.insert_one({
        'name': name,
        'sku': sku,
        'category': category,
        'quantity': quantity,
        'reorder_level': reorder_level,
        'unit_price': unit_price
    })
    log_activity('Added Inventory', f'Added item {name} (SKU: {sku})')
    flash('Item added to inventory successfully!', 'success')
    return redirect(url_for('inventory'))

@app.route('/users')
@admin_required
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    all_users = list(users_collection.find())
    for u in all_users:
        u['_id'] = str(u['_id'])
        
    return render_template('users.html', users=all_users)

@app.route('/update-role/<user_id>', methods=['POST'])
@admin_required
def update_role(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    new_role = request.form.get('role')
    
    # Don't allow an admin to change their own role to Employee to prevent lockouts
    if user_id == session.get('user_id') and new_role != 'Admin':
        flash('You cannot demote yourself.', 'error')
        return redirect(url_for('users'))
        
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'role': new_role}})
    flash('User role updated successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/delete-user/<user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    try:
        if str(session.get('user_id')) == str(user_id):
            flash('You cannot delete your own account.', 'error')
            return redirect(url_for('users'))
            
        users_collection.delete_one({'_id': ObjectId(user_id)})
        flash('User deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete user: {str(e)}', 'error')
    return redirect(url_for('users'))

@app.route('/update-permissions/<user_id>', methods=['POST'])
@admin_required
def update_permissions(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    
    spending_limit_val = request.form.get('spending_limit')
    try:
        spending_limit = float(spending_limit_val) if spending_limit_val else None
    except ValueError:
        spending_limit = None

    new_perms = {
        'dashboard': request.form.get('dashboard') == 'on',
        'create_po': request.form.get('create_po') == 'on',
        'view_pos': request.form.get('view_pos') == 'on',
        'create_invoice': request.form.get('create_invoice') == 'on',
        'inventory': request.form.get('inventory') == 'on',
        'transport': request.form.get('transport') == 'on',
        'delete_data': request.form.get('delete_data') == 'on',
        'view_financials': request.form.get('view_financials') == 'on',
        'approve_pos': request.form.get('approve_pos') == 'on',
        'finalize_invoices': request.form.get('finalize_invoices') == 'on',
        'spending_limit': spending_limit
    }
    
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'permissions': new_perms}})
    flash('User permissions updated successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/activity')
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
                           search=search)

@app.route('/utility')
@admin_required
def utility():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    settings = settings_collection.find_one({'type': 'global'})
    return render_template('settings.html', settings=settings)

@app.route('/update-settings', methods=['POST'])
@admin_required
def update_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    business_name = request.form.get('business_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    tax_id = request.form.get('tax_id')
    mode = request.form.get('mode')
    
    settings_collection.update_one(
        {'type': 'global'},
        {'$set': {
            'business_name': business_name,
            'email': email,
            'phone': phone,
            'address': address,
            'tax_id': tax_id,
            'mode': mode
        }},
        upsert=True
    )
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('utility'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if users_collection.find_one({'email': email}):
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        role = request.form.get('role', 'Admin')
        default_perms = {'dashboard': False, 'create_po': False, 'view_pos': False, 'create_invoice': False, 'inventory': False, 'transport': False, 'delete_data': False, 'view_financials': False}
        
        users_collection.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role,
            'permissions': {} if role == 'Admin' else default_perms
        })
        
        flash(f'{role} account created successfully!', 'success')
        
        if session.get('logged_in') and session.get('user_role') == 'Admin':
            return redirect(url_for('users'))
        return redirect(url_for('admin_portal'))
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Mock forgot password
        fallback = 'admin_portal' if session.get('login_type') == 'admin' else 'login'
        return redirect(url_for(fallback))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    log_activity('Logged Out', 'User logged out')
    login_type = session.get('login_type', 'employee')
    session.clear()
    if login_type == 'admin':
        return redirect(url_for('admin_portal'))
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        fallback = 'admin_portal' if session.get('login_type') == 'admin' else 'login'
        return redirect(url_for(fallback))
        
    from bson.objectid import ObjectId
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('profile.html', user=user)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if not session.get('logged_in'):
        fallback = 'admin_portal' if session.get('login_type') == 'admin' else 'login'
        return redirect(url_for(fallback))
        
    from bson.objectid import ObjectId
    user_id = session['user_id']
    name = request.form.get('name')
    phone = request.form.get('phone')
    
    update_data = {
        'name': name,
        'phone': phone
    }
    
    # Handle Photo Upload (Base64 from Cropper to bypass Vercel read-only FS)
    photo_base64 = request.form.get('photo_base64')
    if photo_base64:
        update_data['photo_base64'] = photo_base64
        session['has_custom_avatar'] = True

    # Update database
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
    
    # Update Session
    session['user_name'] = name
    session['user_phone'] = phone
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if not session.get('logged_in'):
        fallback = 'admin_portal' if session.get('login_type') == 'admin' else 'login'
        return redirect(url_for(fallback))
        
    if request.method == 'POST':
        # Only admins can create tasks
        if session.get('user_role') != 'Admin':
            flash('Only admins can assign tasks.', 'error')
            return redirect(url_for('tasks'))
            
        title = request.form.get('title')
        description = request.form.get('description')
        assignee_id = request.form.get('assignee_id')
        due_date = request.form.get('due_date')
        
        assignee = users_collection.find_one({'_id': ObjectId(assignee_id)})
        assignee_name = assignee['name'] if assignee else 'Unknown'
        
        tasks_collection.insert_one({
            'title': title,
            'description': description,
            'assignee_id': assignee_id,
            'assignee_name': assignee_name,
            'due_date': due_date,
            'status': 'Pending',
            'created_by': session.get('user_id'),
            'created_by_name': session.get('user_name'),
            'date_created': datetime.datetime.now()
        })
        log_activity('Assigned Task', f'Assigned task "{title}" to {assignee_name}')
        flash('Task assigned successfully!', 'success')
        return redirect(url_for('tasks'))
        
    # Get all users for the assignment dropdown
    all_users = list(users_collection.find({'role': 'Employee'}))
    for u in all_users:
        u['_id'] = str(u['_id'])
        
    # Fetch tasks depending on role
    if session.get('user_role') == 'Admin':
        all_tasks = list(tasks_collection.find().sort('date_created', -1))
    else:
        all_tasks = list(tasks_collection.find({'assignee_id': str(session.get('user_id'))}).sort('date_created', -1))
        
    for t in all_tasks:
        t['_id'] = str(t['_id'])
        
    return render_template('tasks.html', tasks=all_tasks, employees=all_users)

@app.route('/update-task/<task_id>', methods=['POST'])
def update_task(task_id):
    if not session.get('logged_in'):
        fallback = 'admin_portal' if session.get('login_type') == 'admin' else 'login'
        return redirect(url_for(fallback))
        
    from bson.objectid import ObjectId
    status = request.form.get('status')
    
    task = tasks_collection.find_one({'_id': ObjectId(task_id)})
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks'))
        
    # Only assignee or admin can update status
    if session.get('user_role') != 'Admin' and task.get('assignee_id') != str(session.get('user_id')):
        flash('You can only update your own tasks.', 'error')
        return redirect(url_for('tasks'))
        
    tasks_collection.update_one({'_id': ObjectId(task_id)}, {'$set': {'status': status}})
    if status == 'Completed':
        log_activity('Completed Task', f'Completed task "{task.get("title")}"')
        
    flash('Task status updated!', 'success')
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    print("Local server URL: http://127.0.0.1:4000")
    app.run(debug=True, port=4000)


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
