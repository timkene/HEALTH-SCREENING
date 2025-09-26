#!/usr/bin/env python3
"""
Medical Report Portal - Production Version
Deploy-ready version with environment variables
"""

from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
import pandas as pd
import os
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta
import logging

app = Flask(__name__, static_folder='static')

# Configuration from environment variables
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
REPORTS_FOLDER = os.environ.get('REPORTS_FOLDER', 'reports')
CUSTOMER_DATA_FILE = os.environ.get('CUSTOMER_DATA_FILE', 'customers.csv')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Set session timeout
app.permanent_session_lifetime = timedelta(minutes=30)

class CustomerDatabase:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.customers = self.load_customers()
    
    def load_customers(self):
        """Load customer data from CSV"""
        try:
            if not os.path.exists(self.csv_file):
                logger.error(f"Customer data file not found: {self.csv_file}")
                return {}
                
            df = pd.read_csv(self.csv_file)
            customers = {}
            for _, row in df.iterrows():
                customers[str(row['ID'])] = {
                    'name': str(row['Name']).strip(),
                    'email': str(row['Email']).strip().lower(),
                    'phone': str(row['Phone']).strip(),
                    'report_file': str(row.get('ReportFileName', f"{row['ID']}.pdf")).strip()
                }
            logger.info(f"Loaded {len(customers)} customers from {self.csv_file}")
            return customers
        except Exception as e:
            logger.error(f"Error loading customer data: {e}")
            return {}
    
    def verify_customer(self, customer_id, email, phone):
        """Verify customer credentials with case-insensitive matching"""
        customer_id = str(customer_id).strip()
        email = email.strip().lower()
        phone = str(phone).strip()
        
        # Normalize phone number - remove leading 0 if present
        if phone.startswith('0'):
            phone_normalized = phone[1:]
        else:
            phone_normalized = phone
        
        if customer_id in self.customers:
            customer = self.customers[customer_id]
            customer_phone = customer['phone']
            
            # Normalize stored phone number too
            if customer_phone.startswith('0'):
                customer_phone_normalized = customer_phone[1:]
            else:
                customer_phone_normalized = customer_phone
            
            # Case-insensitive email matching and flexible phone matching
            if (customer['email'] == email and 
                (customer_phone == phone or customer_phone_normalized == phone_normalized)):
                return customer
        return None
    
    def get_customer_by_id(self, customer_id):
        """Get customer data by ID"""
        return self.customers.get(str(customer_id))

# Initialize database
db = CustomerDatabase(CUSTOMER_DATA_FILE)

# Security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def log_access(action, customer_id=None, ip_address=None, success=True, details=""):
    """Log access attempts for security monitoring"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip = ip_address or request.remote_addr
    status = "SUCCESS" if success else "FAILED"
    
    log_entry = f"{timestamp} - {status} - {action} - Customer: {customer_id or 'N/A'} - IP: {ip} - {details}"
    
    # Log to console (for cloud platforms)
    logger.info(log_entry)

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Customer verification page"""
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        
        # Log verification attempt
        log_access("VERIFICATION_ATTEMPT", customer_id, success=False, 
                  details=f"Email: {email}, Phone: {phone}")
        
        # Verify customer
        customer = db.verify_customer(customer_id, email, phone)
        
        if customer:
            # Store verified customer in session
            session.permanent = True
            session['verified'] = True
            session['customer_id'] = customer_id
            session['customer_name'] = customer['name']
            session['login_time'] = datetime.now().isoformat()
            
            # Log successful verification
            log_access("VERIFICATION_SUCCESS", customer_id, success=True)
            
            flash('Verification successful! Welcome to your secure portal.', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Log failed verification
            log_access("VERIFICATION_FAILED", customer_id, success=False, 
                      details="Invalid credentials")
            flash('Invalid credentials. Please check your ID, email, and phone number.', 'error')
    
    return render_template('verify.html')

@app.route('/dashboard')
def dashboard():
    """Customer dashboard - view report details"""
    if not session.get('verified'):
        log_access("DASHBOARD_ACCESS_DENIED", success=False, details="Not verified")
        flash('Please verify your identity first.', 'warning')
        return redirect(url_for('verify'))
    
    customer_id = session.get('customer_id')
    customer_name = session.get('customer_name')
    
    # Check if report file exists
    customer = db.get_customer_by_id(customer_id)
    if not customer:
        log_access("DASHBOARD_ERROR", customer_id, success=False, details="Customer not found")
        flash('Customer data not found.', 'error')
        return redirect(url_for('verify'))
    
    report_file = customer['report_file']
    report_path = os.path.join(REPORTS_FOLDER, report_file)
    report_exists = os.path.exists(report_path)
    
    # Log dashboard access
    log_access("DASHBOARD_ACCESS", customer_id, success=True)
    
    return render_template('dashboard.html', 
                         customer_name=customer_name,
                         customer_id=customer_id,
                         report_exists=report_exists,
                         report_file=report_file)

@app.route('/download_report')
def download_report():
    """Download customer's medical report"""
    if not session.get('verified'):
        log_access("DOWNLOAD_DENIED", success=False, details="Not verified")
        flash('Please verify your identity first.', 'warning')
        return redirect(url_for('verify'))
    
    customer_id = session.get('customer_id')
    customer = db.get_customer_by_id(customer_id)
    
    if not customer:
        log_access("DOWNLOAD_ERROR", customer_id, success=False, details="Customer not found")
        flash('Customer data not found.', 'error')
        return redirect(url_for('dashboard'))
    
    report_file = customer['report_file']
    report_path = os.path.join(REPORTS_FOLDER, report_file)
    
    if not os.path.exists(report_path):
        log_access("DOWNLOAD_ERROR", customer_id, success=False, details="Report file not found")
        flash('Report file not found. Please contact support.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Log successful download
        log_access("REPORT_DOWNLOAD", customer_id, success=True, details=f"File: {report_file}")
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"Health_Report_{customer_id}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error downloading report for customer {customer_id}: {e}")
        log_access("DOWNLOAD_ERROR", customer_id, success=False, details=f"Error: {str(e)}")
        flash('Error downloading report. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/view_report')
def view_report():
    """View report in browser (inline)"""
    if not session.get('verified'):
        log_access("VIEW_DENIED", success=False, details="Not verified")
        flash('Please verify your identity first.', 'warning')
        return redirect(url_for('verify'))
    
    customer_id = session.get('customer_id')
    customer = db.get_customer_by_id(customer_id)
    
    if not customer:
        log_access("VIEW_ERROR", customer_id, success=False, details="Customer not found")
        flash('Customer data not found.', 'error')
        return redirect(url_for('dashboard'))
    
    report_file = customer['report_file']
    report_path = os.path.join(REPORTS_FOLDER, report_file)
    
    if not os.path.exists(report_path):
        log_access("VIEW_ERROR", customer_id, success=False, details="Report file not found")
        flash('Report file not found. Please contact support.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Log successful view
        log_access("REPORT_VIEW", customer_id, success=True, details=f"File: {report_file}")
        
        return send_file(
            report_path,
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error viewing report for customer {customer_id}: {e}")
        log_access("VIEW_ERROR", customer_id, success=False, details=f"Error: {str(e)}")
        flash('Error viewing report. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout and clear session"""
    customer_id = session.get('customer_id')
    log_access("LOGOUT", customer_id, success=True)
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/stats')
def admin_stats():
    """Admin statistics page (basic security)"""
    # Simple password protection for admin
    admin_password = request.args.get('password')
    if admin_password != ADMIN_PASSWORD:
        return "Unauthorized", 401
    
    try:
        # Basic stats
        stats = {
            'total_customers': len(db.customers),
            'reports_folder': REPORTS_FOLDER,
            'customer_file': CUSTOMER_DATA_FILE,
            'reports_count': len([f for f in os.listdir(REPORTS_FOLDER) if f.endswith('.pdf')]) if os.path.exists(REPORTS_FOLDER) else 0
        }
        
        return f"""
        <h2>Portal Statistics</h2>
        <p>Total Customers: {stats['total_customers']}</p>
        <p>Reports Folder: {stats['reports_folder']}</p>
        <p>Customer File: {stats['customer_file']}</p>
        <p>PDF Reports Available: {stats['reports_count']}</p>
        <h3>System Status: ✅ Online</h3>
        """
    except Exception as e:
        return f"Error reading stats: {str(e)}"

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_message="Internal server error"), 500

if __name__ == '__main__':
    # Check if customer data file exists
    if not os.path.exists(CUSTOMER_DATA_FILE):
        print(f"⚠️  Warning: {CUSTOMER_DATA_FILE} not found.")
        print("Please ensure the customer data file is uploaded to the server.")
    
    # Check if reports folder has files
    if os.path.exists(REPORTS_FOLDER):
        report_files = [f for f in os.listdir(REPORTS_FOLDER) if f.endswith('.pdf')]
        print(f"📁 Found {len(report_files)} PDF reports in {REPORTS_FOLDER}")
        if len(report_files) == 0:
            print("⚠️  No PDF reports found. Please upload reports to the server.")
    else:
        print(f"📁 Creating reports folder: {REPORTS_FOLDER}")
        os.makedirs(REPORTS_FOLDER, exist_ok=True)
    
    print("\n🏥 Medical Report Portal Starting...")
    print("=" * 50)
    print(f"Portal URL: http://localhost:{os.environ.get('PORT', 5001)}")
    print(f"Admin Stats: http://localhost:{os.environ.get('PORT', 5001)}/admin/stats?password={ADMIN_PASSWORD}")
    print("=" * 50)
    
    # Run the application
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
