from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime
import random
import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText

def send_otp_email(to_email, otp_code):
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
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = 'business_dashboard_secret'
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

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = users_collection.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            otp = str(random.randint(100000, 999999))
            
            session['temp_user'] = {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user.get('email', ''),
                'role': user.get('role', 'Admin'),
                'phone': user.get('phone', ''),
                'photo': user.get('photo', '')
            }
            session['otp'] = otp
            session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()
            
            send_otp_email(email, otp)
            return redirect(url_for('verify_otp'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'temp_user' not in session or 'otp' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        expiry = session.get('otp_expiry', 0)
        
        if datetime.datetime.now().timestamp() > expiry:
            flash('OTP has expired. Please login again.', 'error')
            session.pop('temp_user', None)
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            return redirect(url_for('login'))
            
        if entered_otp == session.get('otp'):
            user_data = session.pop('temp_user')
            session.pop('otp', None)
            session.pop('otp_expiry', None)
            
            session['logged_in'] = True
            session['user_id'] = user_data['id']
            session['user_name'] = user_data['name']
            session['user_email'] = user_data['email']
            session['user_role'] = user_data['role']
            session['user_phone'] = user_data['phone']
            session['user_photo'] = user_data['photo']
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP code. Please try again.', 'error')
            
    return render_template('verify_otp.html')

@app.route('/dashboard')
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
    
    return render_template('dashboard.html', 
                           total_inventory=total_inventory, 
                           inventory_value=inventory_value,
                           low_stock=low_stock,
                           out_of_stock=out_of_stock,
                           total_vendors=total_vendors,
                           total_pos=total_pos,
                           total_po_value=total_po_value,
                           recent_pos=recent_pos,
                           total_transport=total_transport)

@app.route('/create-po', methods=['GET', 'POST'])
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
        total = request.form.get('total', 0)
        action = request.form.get('action', 'generated')
        
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
            'total': float(total),
            'status': 'draft' if action == 'draft' else 'generated',
            'created_by': session.get('user_id'),
            'date_created': datetime.datetime.now()
        })
        
        if action == 'draft':
            flash('Purchase Order saved as draft successfully!', 'success')
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
def delete_po(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    po_collection.delete_one({'_id': ObjectId(po_id)})
    flash('Purchase order deleted successfully!', 'success')
    return redirect(url_for('create_po'))

@app.route('/view-po/<po_id>')
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
def delete_po_dashboard(po_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    try:
        po_collection.delete_one({'_id': ObjectId(po_id)})
        flash('Purchase Order deleted successfully.', 'success')
    except Exception as e:
        flash('Failed to delete Purchase Order.', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/add-vendor', methods=['GET', 'POST'])
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
        
        # Map our internal status to display status
        internal_status = po.get('status', 'generated')
        if internal_status == 'draft':
            po['display_status'] = 'Pending'
        else:
            po['display_status'] = 'Approved'
            approved_count += 1
            
    return render_template('submitted_pos.html', pos=all_pos, total_pos=total_pos, approved_count=approved_count)

@app.route('/create-invoice', methods=['GET', 'POST'])
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
def delete_inventory(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    inventory_collection.delete_one({'_id': ObjectId(item_id)})
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('inventory'))

@app.route('/add-inventory', methods=['POST'])
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
    flash('Item added to inventory successfully!', 'success')
    return redirect(url_for('inventory'))

@app.route('/utility')
def utility():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    settings = settings_collection.find_one({'type': 'global'})
    return render_template('settings.html', settings=settings)

@app.route('/update-settings', methods=['POST'])
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
        users_collection.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password
        })
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Mock forgot password
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('profile.html', user=user)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    from bson.objectid import ObjectId
    user_id = session['user_id']
    name = request.form.get('name')
    phone = request.form.get('phone')
    role = request.form.get('role')
    
    update_data = {
        'name': name,
        'phone': phone,
        'role': role
    }
    
    # Handle Photo Upload
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '':
            filename = secure_filename(f"{user_id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            update_data['photo'] = filename
            session['user_photo'] = filename

    # Update database
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
    
    # Update Session
    session['user_name'] = name
    session['user_phone'] = phone
    session['user_role'] = role
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    print("Local server URL: http://127.0.0.1:4000")
    app.run(debug=True, port=4000)
