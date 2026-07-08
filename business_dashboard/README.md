![Indus International School Logo](static/images/logo.png)

# Business PO Dashboard

A comprehensive, open-source dashboard designed to help small and medium businesses streamline their operations. Manage Purchase Orders, Invoices, Inventory, and Transport logistics seamlessly in one beautifully designed, user-friendly interface.

## 🚀 Features

- **📊 Centralized Dashboard**: Get a bird's-eye view of your business health with our Data Health Snapshot, tracking inventory levels, vendor counts, and financial totals.
- **📄 Purchase Order System**: Create professional, printable Purchase Orders. Track them from submission to completion.
- **🧾 Invoice Generation**: A sleek live-preview invoice generator that automatically calculates subtotals, taxes, and grand totals. Print directly to PDF.
- **📦 Inventory Management**: Track your stock levels, SKUs, and categories. Includes low-stock and out-of-stock indicators.
- **🚚 Transport & Courier Tracking**: Monitor your shipments in real-time. Update statuses from "Preparing" to "In Transit" to "Delivered".
- **⚙️ Dynamic Configuration**: Easily switch between "Personal" and "Business" modes, and configure your global business profile right from the Settings page.

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask framework
- **Database**: MongoDB (PyMongo)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (No heavy frameworks required)
- **Styling**: Custom modern CSS (Flexbox/Grid), FontAwesome Icons

## ⚙️ Installation & Setup

Follow these steps to get the project running on your local machine:

### 1. Prerequisites
Ensure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/)
- [MongoDB](https://www.mongodb.com/try/download/community) (Running locally on default port `27017`)

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/business-po-dashboard.git
cd business-po-dashboard
```

### 3. Install Dependencies
It's recommended to use a virtual environment.
```bash
pip install -r requirements.txt
```

### 4. Start the Application
Run the Flask server:
```bash
python3 app.py
```
You should see output indicating the server is running on `http://127.0.0.1:4000`.

### 5. Access the Dashboard
Open your web browser and navigate to:
[http://127.0.0.1:4000](http://127.0.0.1:4000)

*Note: You will be prompted to register an admin account on your first visit.*

## 💡 How to Use (For Beginners)

1. **First Steps**: Go to **Utility > Settings** to configure your Business Name and details. This ensures your Invoices and POs have your branding.
2. **Vendors**: Before creating a PO, add a vendor under **Accounts > Add Vendor**.
3. **Inventory**: Keep track of your products under the **Inventory** tab to automatically pull prices into your invoices.
4. **Need Help?**: Hover over the icons in the sidebar for descriptive tooltips, or check the helper text under complex form fields!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
