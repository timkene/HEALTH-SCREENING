#!/usr/bin/env python3
"""
Medical Report Portal - Secure access to individual health reports
Integrates with the health screening system
"""

from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session, Response
import pandas as pd
import os
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta
import logging
import json
from database_config import get_db, close_db
from pdf_storage import get_pdf_storage

app = Flask(__name__, static_folder='static')
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REPORTS_FOLDER = 'reports'  # Folder containing PDF reports
CUSTOMER_DATA_FILE = 'customers.csv'  # CSV with customer data
UPLOAD_FOLDER = 'uploads'
LOG_FILE = 'portal_access.log'

# Ensure folders exist
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set session timeout to 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)

class CustomerDatabase:
    def __init__(self):
        self.db = get_db()
        self.pdf_storage = get_pdf_storage()
    
    def verify_customer(self, customer_id, email, phone):
        """Verify customer credentials with case-insensitive matching"""
        try:
            customer = self.db.verify_customer(customer_id, email, phone)
            if customer:
                # Convert to expected format
                return {
                    'name': customer['name'],
                    'email': customer['email'],
                    'phone': customer['phone'],
                    'report_file': customer['report_file_name']
                }
            return None
        except Exception as e:
            logger.error(f"Error verifying customer: {e}")
            return None
    
    def get_customer_by_id(self, customer_id):
        """Get customer data by ID"""
        try:
            customer = self.db.get_customer(customer_id)
            if customer:
                return {
                    'name': customer['name'],
                    'email': customer['email'],
                    'phone': customer['phone'],
                    'report_file': customer['report_file_name']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting customer: {e}")
            return None

# Initialize database
db = CustomerDatabase()

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
    
    # Log to file
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + "\n")
    
    # Log to console
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
    
    # Check if report exists in MotherDuck
    customer = db.get_customer_by_id(customer_id)
    if not customer:
        log_access("DASHBOARD_ERROR", customer_id, success=False, details="Customer not found")
        flash('Customer data not found.', 'error')
        return redirect(url_for('verify'))
    
    # Check if PDF exists in MotherDuck
    pdf_metadata = db.pdf_storage.get_pdf_metadata(customer_id)
    report_exists = pdf_metadata is not None
    report_file = customer['report_file']
    
    # Log dashboard access
    log_access("DASHBOARD_ACCESS", customer_id, success=True)
    
    return render_template('dashboard.html', 
                         customer_name=customer_name,
                         customer_id=customer_id,
                         report_exists=report_exists,
                         report_file=report_file)

@app.route('/download_report')
def download_report():
    """Download customer's medical report from MotherDuck"""
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
    
    try:
        # Get PDF from MotherDuck
        pdf_data = db.pdf_storage.get_pdf(customer_id)
        
        if not pdf_data:
            log_access("DOWNLOAD_ERROR", customer_id, success=False, details="Report not found in database")
            flash('Report not found. Please contact support.', 'error')
            return redirect(url_for('dashboard'))
        
        # Log successful download
        log_access("REPORT_DOWNLOAD", customer_id, success=True, details="Downloaded from MotherDuck")
        
        # Return PDF as download
        return Response(
            pdf_data,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=Health_Report_{customer_id}.pdf'
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading report for customer {customer_id}: {e}")
        log_access("DOWNLOAD_ERROR", customer_id, success=False, details=f"Error: {str(e)}")
        flash('Error downloading report. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/view_report')
def view_report():
    """View report in browser (inline) from MotherDuck"""
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
    
    try:
        # Get PDF from MotherDuck
        pdf_data = db.pdf_storage.get_pdf(customer_id)
        
        if not pdf_data:
            log_access("VIEW_ERROR", customer_id, success=False, details="Report not found in database")
            flash('Report not found. Please contact support.', 'error')
            return redirect(url_for('dashboard'))
        
        # Log successful view
        log_access("REPORT_VIEW", customer_id, success=True, details="Viewed from MotherDuck")
        
        # Return PDF for inline viewing
        return Response(
            pdf_data,
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
    if admin_password != 'admin123':  # Change this password!
        return "Unauthorized", 401
    
    try:
        # Read log file and show basic stats
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
            
            total_attempts = len(lines)
            successful_logins = len([l for l in lines if 'VERIFICATION_SUCCESS' in l])
            downloads = len([l for l in lines if 'REPORT_DOWNLOAD' in l])
            views = len([l for l in lines if 'REPORT_VIEW' in l])
            
            stats = {
                'total_attempts': total_attempts,
                'successful_logins': successful_logins,
                'downloads': downloads,
                'views': views,
                'recent_activity': lines[-10:] if lines else []
            }
            
            return f"""
            <h2>Portal Statistics</h2>
            <p>Total Access Attempts: {stats['total_attempts']}</p>
            <p>Successful Logins: {stats['successful_logins']}</p>
            <p>Report Downloads: {stats['downloads']}</p>
            <p>Report Views: {stats['views']}</p>
            <h3>Recent Activity:</h3>
            <pre>{chr(10).join(stats['recent_activity'])}</pre>
            """
        else:
            return "No log file found."
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
        print("Please run 'python generate_customer_csv.py' first to create the customer data file.")
        print("Expected columns: ID, Name, Email, Phone, ReportFileName")
    
    # Check if reports folder has files
    if os.path.exists(REPORTS_FOLDER):
        report_files = [f for f in os.listdir(REPORTS_FOLDER) if f.endswith('.pdf')]
        print(f"📁 Found {len(report_files)} PDF reports in {REPORTS_FOLDER}")
        if len(report_files) == 0:
            print("⚠️  No PDF reports found. Please generate reports using the Streamlit app first.")
    else:
        print(f"📁 Creating reports folder: {REPORTS_FOLDER}")
        os.makedirs(REPORTS_FOLDER, exist_ok=True)
    
    print("\n🏥 Medical Report Portal Starting...")
    print("=" * 50)
    print("Portal URL: http://localhost:5001")
    print("Admin Stats: http://localhost:5001/admin/stats?password=admin123")
    print("=" * 50)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)
