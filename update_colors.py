import re

files = [
    'business_dashboard/templates/view_po.html',
    'business_dashboard/templates/view_invoice.html',
    'business_dashboard/templates/create_po.html',
    'business_dashboard/templates/create_invoice.html'
]

# Replacement for the header text
header_html_old = """<div class="company-name">INDUS INTERNATIONAL SCHOOL</div>
                    <div class="company-subtitle">Eagle Robot Lab</div>
                    <p class="company-address">Billapura, Cross, Sarjapura - Attibele Rd, Sarjapura, Bengaluru, Karnataka 562125</p>
                    <p class="company-phone">Phone: +91 80-2289-5900, +91 80-2289-5990</p>"""

header_html_old_create = """<div class="company-name">INDUS INTERNATIONAL SCHOOL</div>
                    <div class="company-subtitle">Eagle Robot Lab</div>
                    <p class="company-address">Billapura, Cross, Sarjapura - Attibele Rd, Sarjapura, Bengaluru, Karnataka 562125</p>
                    <p class="company-phone">Phone: +91 80-2289-5900, +91 80-2289-5990</p>"""
                    
# Wait, let's just use regex or simple replace for the blocks.
for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Replace colors
    # Black borders and backgrounds
    content = content.replace('#1a1a1a', '#1e40af') 
    
    # Grey backgrounds -> Light blue backgrounds
    content = content.replace('#f3f4f6', '#eff6ff')
    
    # Replace the hardcoded company text with Jinja variables
    content = content.replace('<div class="company-name">INDUS INTERNATIONAL SCHOOL</div>', '<div class="company-name">{{ global_settings.business_name if global_settings else "BUSINESS PO" }}</div>')
    content = content.replace('<div class="company-subtitle">Eagle Robot Lab</div>', '')
    content = content.replace('<p class="company-address">Billapura, Cross, Sarjapura - Attibele Rd, Sarjapura, Bengaluru, Karnataka 562125</p>', '<p class="company-address">{{ global_settings.address if global_settings else "Company Address" }}</p>')
    content = content.replace('<p class="company-phone">Phone: +91 80-2289-5900, +91 80-2289-5990</p>', '<p class="company-phone">{{ global_settings.phone if global_settings else "Phone Number" }}</p>')
    
    with open(filepath, 'w') as f:
        f.write(content)

print("Updated colors and headers.")
