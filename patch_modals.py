import re

modal_html = """<!-- PREVIEW MODAL -->
<div id="previewModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 9999; overflow-y: auto; padding: 2rem; box-sizing: border-box; backdrop-filter: blur(4px);">
    <div style="max-width: 850px; margin: 0 auto; position: relative; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);">
        
        <!-- Modal Controls (Not printed) -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;" class="no-print">
            <h3 style="margin: 0; color: #1a1a1a; font-size: 1.5rem;">Document Preview</h3>
            <div style="display: flex; gap: 1rem;">
                <button type="button" class="btn btn-primary" style="padding: 0.5rem 1.5rem; font-size: 1rem; border-radius: 6px; cursor: pointer; background-color: #2563eb; color: white; border: none;" onclick="window.print()"><i class="fas fa-print" style="margin-right: 0.5rem;"></i>Print PDF</button>
                <button type="button" onclick="closePreviewModal()" style="background: #f1f5f9; border: none; font-size: 1.5rem; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; color: #1e293b; display: flex; align-items: center; justify-content: center;">&times;</button>
            </div>
        </div>
        
        <!-- PRINT AREA STYLES -->
        <style>
            .print-area {
                font-family: Arial, sans-serif;
                color: #1a1a1a;
            }
            .header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
            .header-left { display: flex; flex-direction: column; gap: 4px; }
            .company-name { font-size: 1.5rem; font-weight: bold; margin: 0 0 10px 0; text-transform: uppercase; }
            .company-subtitle { font-size: 1rem; color: #4b5563; margin-bottom: 10px; }
            .company-address, .company-phone { font-size: 0.85rem; color: #6b7280; margin: 0; max-width: 300px; line-height: 1.4; }
            .header-right { text-align: right; display: flex; flex-direction: column; gap: 6px; }
            .doc-title { font-size: 1.8rem; font-weight: bold; text-transform: uppercase; margin: 0 0 10px 0; letter-spacing: 1px; color: #374151; }
            .meta-text { font-size: 0.95rem; color: #1f2937; font-weight: 500; }
            .divider { border-top: 2px solid #1a1a1a; margin: 20px 0 30px 0; }
            .vendor-section-title { font-size: 1rem; font-weight: bold; margin: 0 0 10px 0; text-transform: uppercase; }
            .vendor-box { background-color: #f3f4f6; border-left: 4px solid #1a1a1a; padding: 15px 20px; margin-bottom: 30px; }
            .vendor-name { font-weight: bold; font-size: 1rem; margin: 0 0 5px 0; text-transform: uppercase; }
            .vendor-address { font-size: 0.9rem; color: #4b5563; margin: 0; }
            .order-details-title { font-size: 1.1rem; font-weight: bold; margin: 0 0 10px 0; }
            .preview-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
            .preview-table th { background-color: #1a1a1a !important; color: white !important; font-size: 0.85rem; text-align: left; padding: 8px; font-weight: bold; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .preview-table td { padding: 8px; font-size: 0.85rem; border-bottom: 1px solid #e5e7eb; }
            .totals-container { display: flex; justify-content: flex-end; margin-bottom: 30px; }
            .totals-box { width: 300px; }
            .totals-row { display: flex; justify-content: space-between; padding: 6px 10px; font-size: 0.9rem; background-color: #f3f4f6 !important; margin-bottom: 2px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .totals-row.final { font-weight: bold; }
            .amount-words-box { background-color: #f3f4f6 !important; border-left: 4px solid #1a1a1a; padding: 10px 15px; font-size: 0.9rem; margin-bottom: 40px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .terms-section { margin-bottom: 40px; }
            .terms-title { font-weight: bold; font-size: 1rem; margin: 0 0 10px 0; }
            .terms-list { list-style: none; padding: 0; margin: 0; font-size: 0.85rem; color: #4b5563; line-height: 1.6; }
            .signature-section { display: flex; justify-content: flex-end; margin-top: 60px; }
            .signature-box { text-align: right; width: 300px; }
            .signature-line { border-top: 1px solid #1a1a1a; margin-bottom: 10px; }
            .signature-name { font-weight: bold; font-size: 1rem; margin: 0 0 5px 0; }
            @media print {
                body * { visibility: hidden; }
                #previewModal { position: absolute; left: 0; top: 0; padding: 0; background: white; }
                #previewModal * { visibility: visible; }
                .no-print { display: none !important; }
            }
        </style>

        <div class="print-area">
            <!-- HEADER -->
            <div class="header-top">
                <div class="header-left">
                    <div class="company-name">INDUS INTERNATIONAL SCHOOL</div>
                    <div class="company-subtitle">Eagle Robot Lab</div>
                    <p class="company-address">Billapura, Cross, Sarjapura - Attibele Rd, Sarjapura, Bengaluru, Karnataka 562125</p>
                    <p class="company-phone">Phone: +91 80-2289-5900, +91 80-2289-5990</p>
                </div>
                <div class="header-right">
                    <h1 class="doc-title" id="pv-doc-title">PURCHASE ORDER</h1>
                    <div class="meta-text">Date: <span id="pv-date"></span></div>
                    <div class="meta-text"><span id="pv-num-label">PO #:</span> <span id="pv-doc-num"></span></div>
                </div>
            </div>
            
            <div class="divider"></div>
            
            <!-- VENDOR -->
            <h3 class="vendor-section-title">VENDOR</h3>
            <div class="vendor-box">
                <h4 class="vendor-name" id="pv-vendor">Vendor Name</h4>
                <p class="vendor-address" id="pv-vendor-address">Vendor Address</p>
            </div>
            
            <!-- ORDER DETAILS -->
            <h3 class="order-details-title">Order Details</h3>
            <table class="preview-table">
                <thead>
                    <tr>
                        <th style="width: 5%;">S.No</th>
                        <th style="width: 25%;">Item Name</th>
                        <th style="width: 35%;">Description</th>
                        <th style="width: 5%; text-align: center;">Qty</th>
                        <th style="width: 10%; text-align: right;">Unit Price</th>
                        <th style="width: 10%; text-align: right;">Shipping</th>
                        <th style="width: 10%; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody id="pv-table-body">
                    <!-- Populated by JS -->
                </tbody>
            </table>
            
            <!-- TOTALS -->
            <div class="totals-container">
                <div class="totals-box">
                    <div class="totals-row">
                        <span>Subtotal:</span>
                        <span id="pv-subtotal"></span>
                    </div>
                    <div class="totals-row">
                        <span>Shipping:</span>
                        <span id="pv-shipping"></span>
                    </div>
                    <div class="totals-row">
                        <span>Tax:</span>
                        <span id="pv-tax"></span>
                    </div>
                    <div class="totals-row final">
                        <span>TOTAL:</span>
                        <span id="pv-grand-total"></span>
                    </div>
                </div>
            </div>
            
            <div class="amount-words-box">
                <strong>Amount In Words:</strong> <span id="pv-words">Amount will appear here</span>
            </div>
            
            <div class="terms-section">
                <h4 class="terms-title">Terms and Conditions</h4>
                <ul class="terms-list">
                    <li>1) Payment Terms: <span id="pv-terms"></span></li>
                    <li>2) Notes: <span id="pv-notes"></span></li>
                </ul>
            </div>
            
            <div class="signature-section">
                <div class="signature-box">
                    <div class="signature-line"></div>
                    <h4 class="signature-name">Mr. Sumit H</h4>
                </div>
            </div>
        </div>
    </div>
</div>
"""

js_update_function = """function numberToWords(n) {
        if (n === 0) return "Zero Rupees";
        const ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"];
        const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
        const teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
        function convert(num) {
            if (num < 10) return ones[num];
            if (num < 20) return teens[num - 10];
            if (num < 100) return tens[Math.floor(num / 10)] + (num % 10 !== 0 ? " " + ones[num % 10] : "");
            if (num < 1000) return ones[Math.floor(num / 100)] + " Hundred" + (num % 100 !== 0 ? " and " + convert(num % 100) : "");
            if (num < 100000) return convert(Math.floor(num / 1000)) + " Thousand" + (num % 1000 !== 0 ? " " + convert(num % 1000) : "");
            if (num < 10000000) return convert(Math.floor(num / 100000)) + " Lakh" + (num % 100000 !== 0 ? " " + convert(num % 100000) : "");
            return convert(Math.floor(num / 10000000)) + " Crore" + (num % 10000000 !== 0 ? " " + convert(num % 10000000) : "");
        }
        return convert(Math.floor(n)).trim() + " Rupees";
    }

    function updatePreview() {
        const isInvoice = document.getElementById('pv-doc-title').textContent === 'INVOICE';
        
        // Date & Terms
        const dateInput = document.querySelector('input[name="po_date"]') || document.querySelector('input[name="invoice_date"]');
        document.getElementById('pv-date').textContent = dateInput.value || '---';
        const termsInput = document.querySelector('select[name="payment_terms"]');
        document.getElementById('pv-terms').textContent = termsInput ? termsInput.value : '---';
        
        // Vendor Info
        const vendorSelect = document.getElementById('vendor-select');
        document.getElementById('pv-vendor').textContent = vendorSelect.options[vendorSelect.selectedIndex].text !== '-- Select Vendor --' ? vendorSelect.options[vendorSelect.selectedIndex].text : 'Vendor Name';
        const vendorAddress = document.getElementById('vendor_address');
        document.getElementById('pv-vendor-address').textContent = vendorAddress ? vendorAddress.value : '';
        
        // Notes
        const notesInput = document.getElementById('notes');
        document.getElementById('pv-notes').textContent = notesInput ? notesInput.value : 'None';
        
        // Table Items
        const tbody = document.getElementById('pv-table-body');
        tbody.innerHTML = '';
        
        const rows = document.querySelectorAll('.po-row, .invoice-row');
        let counter = 1;
        rows.forEach(row => {
            const name = row.querySelector('input[name="item_name[]"]').value;
            const desc = row.querySelector('input[name="description[]"]');
            const qty = row.querySelector('input[name="qty[]"]').value;
            const price = parseFloat(row.querySelector('input[name="unit_price[]"]').value || 0).toFixed(2);
            const shipping = parseFloat(row.querySelector('input[name="item_shipping[]"]')?.value || 0).toFixed(2);
            const rowTotal = row.querySelector('.row-total-text').textContent;
            
            if (name) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${counter++}</td>
                    <td>${name}</td>
                    <td>${desc ? desc.value : ''}</td>
                    <td style="text-align: center;">${qty}</td>
                    <td style="text-align: right;">₹${price}</td>
                    <td style="text-align: right;">₹${shipping}</td>
                    <td style="text-align: right; font-weight: bold;">₹${rowTotal}</td>
                `;
                tbody.appendChild(tr);
            }
        });
        
        // Totals
        document.getElementById('pv-subtotal').textContent = '₹' + document.getElementById('subtotal').value;
        const shippingTotal = document.getElementById('total_shipping');
        document.getElementById('pv-shipping').textContent = '₹' + (shippingTotal ? shippingTotal.value : '0.00');
        const taxTotal = document.getElementById('total_tax');
        document.getElementById('pv-tax').textContent = '₹' + (taxTotal ? taxTotal.value : '0.00');
        
        const grandTotalStr = document.getElementById('grand_total').value;
        document.getElementById('pv-grand-total').textContent = '₹' + grandTotalStr;
        
        // Words
        document.getElementById('pv-words').textContent = numberToWords(parseFloat(grandTotalStr || 0));
    }
"""

def patch_file(filepath, is_invoice=False):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace HTML
    start_idx = content.find("<!-- PREVIEW MODAL -->")
    # find the end of the script tag or body
    end_idx = content.find("<script>", start_idx)
    if end_idx == -1: end_idx = len(content)

    new_html = modal_html
    if is_invoice:
        new_html = new_html.replace('PURCHASE ORDER', 'INVOICE')
        new_html = new_html.replace('PO #:', 'INVOICE #:')
        new_html = new_html.replace('pv-doc-num"></span>', 'pv-doc-num">{{ invoice_number }}</span>')
    else:
        new_html = new_html.replace('pv-doc-num"></span>', 'pv-doc-num">{{ po_number }}</span>')

    content = content[:start_idx] + new_html + "\n" + content[end_idx:]

    # Replace updatePreview function
    start_func = content.find("function updatePreview()")
    if start_func != -1:
        # find the matching closing brace for the function... hacky but let's just regex replace everything up to the next function or script end
        end_func = content.find("</script>", start_func)
        content = content[:start_func] + js_update_function + "\n    " + content[end_func:]
        
    with open(filepath, 'w') as f:
        f.write(content)

patch_file('business_dashboard/templates/create_po.html', is_invoice=False)
patch_file('business_dashboard/templates/create_invoice.html', is_invoice=True)
print("Modals Patched")
