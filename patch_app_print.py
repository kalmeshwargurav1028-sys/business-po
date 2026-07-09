import sys

with open('business_dashboard/app.py', 'r') as f:
    content = f.read()

# Add number_to_words filter
words_filter = """
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
"""

if "def number_to_words(n):" not in content:
    # insert it before @app.route('/')
    content = content.replace("@app.route('/', methods=['GET', 'POST'])", words_filter + "\n@app.route('/', methods=['GET', 'POST'])")

with open('business_dashboard/app.py', 'w') as f:
    f.write(content)
print("Added filter and view_invoice route")
