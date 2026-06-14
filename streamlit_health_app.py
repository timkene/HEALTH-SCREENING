import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime
from report_generator import generate_report
from individual_report_generator import generate_individual_report
import tempfile
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from database_config import get_db, close_db
from pdf_storage import get_pdf_storage
from backblaze_native_config import backblaze_native_manager, test_backblaze_native_setup
from dotenv import load_dotenv

# Zoho Mail Configuration
CLIENT_ID = "1000.N7OTEZEMAV4AS2X2FEC0P7P2PYJIZC"
CLIENT_SECRET = "39b86ec1a58c47c68ec3b5f3f044f2df7142bb1e2f"
REFRESH_TOKEN = "1000.0fafe8457278c99308fdd487c9c46709.c74a0b6a3f87cee8109e00eb37b48d43"
ACCOUNT_ID = '8896202000000008002'

# SMTP Configuration (Zoho Mail SMTP)
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587
SMTP_USERNAME = "hello@clearlinehmo.com"
SMTP_PASSWORD = "your_app_password_here"  # You'll need to set this

# MotherDuck Configuration
MOTHERDUCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Imxlb2Nhc2V5MEBnbWFpbC5jb20iLCJzZXNzaW9uIjoibGVvY2FzZXkwLmdtYWlsLmNvbSIsInBhdCI6IndUUEFydnRna19INlVTbDFGamlyVGFoa3ZoVUtrX2pOZ05XcmtNd0VTQXciLCJ1c2VySWQiOiJmNDAzMTg5ZS05ODIxLTQ2NzktYjRmZS0wZWMyMjY0NDQyZjgiLCJpc3MiOiJtZF9wYXQiLCJyZWFkT25seSI6ZmFsc2UsInRva2VuVHlwZSI6InJlYWRfd3JpdGUiLCJpYXQiOjE3NTIyMjMzODJ9.BjvBqQ8dpgYkbW98IpxE8QTwGJbWexsctB4qNxaxGpo"

# Load environment variables for Backblaze B2
load_dotenv('backblaze_credentials.env')

def initialize_motherduck():
    """Initialize MotherDuck database connection"""
    try:
        # Set environment variable for MotherDuck token
        os.environ['MOTHERDUCK_TOKEN'] = MOTHERDUCK_TOKEN
        
        # Initialize database
        db = get_db()
        pdf_storage = get_pdf_storage()
        
        return db, pdf_storage
    except Exception as e:
        st.error(f"Failed to initialize MotherDuck: {e}")
        return None, None

def initialize_backblaze():
    """Initialize Backblaze B2 connection"""
    try:
        # Test Backblaze connection
        success, message = backblaze_native_manager.config.test_connection()
        if not success:
            st.error(f"Backblaze B2 connection failed: {message}")
            return False
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize Backblaze B2: {e}")
        return False

def test_backblaze_connection():
    """Test Backblaze B2 connection and display results"""
    try:
        with st.spinner("Testing Backblaze B2 connection..."):
            # Test connection directly to get detailed error message
            success, message = backblaze_native_manager.config.test_connection()
            if success:
                st.success(f"✅ {message}")
                return True
            else:
                st.error(f"❌ {message}")
                # Show additional help if initialization failed
                if backblaze_native_manager.config.init_error:
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        **Common issues:**
                        - Invalid Application Key ID or Application Key
                        - Bucket name doesn't exist or is incorrect
                        - Network connectivity issues
                        - Missing `b2sdk` package (install with: `pip install b2sdk`)
                        
                        **Check your credentials in:**
                        - Environment variables: `BACKBLAZE_ACCESS_KEY_ID`, `BACKBLAZE_SECRET_ACCESS_KEY`, `BACKBLAZE_BUCKET_NAME`
                        - Or in `backblaze_credentials.env` file
                        """)
                return False
    except Exception as e:
        st.error(f"❌ Backblaze B2 test error: {str(e)}")
        return False

def upload_pdf_to_backblaze(file_path, customer_id, company_name="Unknown"):
    """Upload PDF to Backblaze B2 and return download URL"""
    try:
        # Upload PDF and get download URL
        success, message, file_key, download_url = backblaze_native_manager.upload_and_get_url(
            file_path=file_path,
            customer_id=customer_id,
            company_name=company_name,
            expiry_hours=168  # URLs expire in 7 days (168 hours)
        )
        
        if success:
            return True, message, download_url
        else:
            return False, message, None
            
    except Exception as e:
        return False, f"Upload error: {str(e)}", None

_ZOHO_TOKEN_CACHE = {"access_token": None, "expires_at": 0.0}

def get_access_token(force_refresh: bool = False):
    """Get a Zoho access token, cached in-process.

    Zoho's /oauth/v2/token endpoint is rate-limited (~15-20 requests / 10 min per
    refresh token). Access tokens are valid for ~1 hour, so we cache and reuse
    them across the whole bulk-email run instead of requesting a new one per
    email (which was causing 'too many requests continuously' errors).
    """
    now = time.time()
    cached = _ZOHO_TOKEN_CACHE.get("access_token")
    if (not force_refresh) and cached and now < _ZOHO_TOKEN_CACHE.get("expires_at", 0):
        return cached

    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=data)
    resp_json = response.json()

    if "access_token" in resp_json:
        expires_in = int(resp_json.get("expires_in", 3600))
        _ZOHO_TOKEN_CACHE["access_token"] = resp_json["access_token"]
        _ZOHO_TOKEN_CACHE["expires_at"] = now + max(60, expires_in - 300)
        return resp_json["access_token"]
    else:
        raise Exception(f"Failed to get access token: {resp_json}")

def test_zoho_connection():
    """Test Zoho Mail API connection"""
    try:
        access_token = get_access_token()
        url = f"https://mail.zoho.com/api/accounts/{ACCOUNT_ID}"
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return True, "Zoho API connection successful"
        else:
            return False, f"Zoho API connection failed. Status: {response.status_code}, Response: {response.text}"
    except Exception as e:
        return False, f"Zoho API connection error: {str(e)}"

def test_email_with_attachment():
    """Test sending email with PDF attachment using base64 encoding"""
    try:
        # Create a simple test PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        test_pdf_path = "test_health_report.pdf"
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "Test Health Screening Report")
        c.drawString(100, 700, "This is a test PDF attachment.")
        c.drawString(100, 650, "Generated by Clearline HMO Health Screening System")
        c.drawString(100, 600, "If you can see this PDF, the attachment system is working!")
        c.save()
        
        # Test email
        test_email = "leocasey0@gmail.com"  # Use your test email
        subject = "Test Email with PDF Attachment - Clearline HMO"
        content = """<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Dear <strong>Test User</strong>,</p>
            
            <p>This is a test email to verify that our PDF attachment system is working correctly.</p>
            
            <p>Please find your test health screening report attached as a PDF file.</p>
            
            <p>If you have any questions, please contact our medical team:</p>
            <p>📱 <strong>WhatsApp Telemedicine:</strong> 08076490056 (Chat with a medical doctor)<br/>
            📧 <strong>Email:</strong> hello@clearlinehmo.com</p>
            
            <div style="margin-top: 40px;">
                <p>Best regards,</p>
                <p style="margin-top: 20px; font-weight: bold; color: #2c5aa0;">Clearline HMO Medical Team</p>
            </div>
        </div>"""
        
        success, message = send_email_via_zoho(test_email, subject, content, test_pdf_path)
        
        # Clean up test file
        try:
            os.remove(test_pdf_path)
        except:
            pass
        
        return success, message
        
    except Exception as e:
        return False, f"Test email error: {str(e)}"

def send_email_via_zoho(to_email, subject, content, download_url=None):
    """Send email via Zoho Mail API with Backblaze download link"""
    try:
        access_token = get_access_token()
        url = f"https://mail.zoho.com/api/accounts/{ACCOUNT_ID}/messages"

        def _build_headers(tok):
            return {
                "Authorization": f"Zoho-oauthtoken {tok}",
                "Content-Type": "application/json"
            }

        headers = _build_headers(access_token)

        # Prepare email data - only use supported fields
        data = {
            "fromAddress": "hello@clearlinehmo.com",
            "toAddress": to_email,
            "subject": subject,
            "content": content,
            "mailFormat": "html"
        }
        
        # Add download link if provided
        if download_url:
            data['content'] += f"\n\n📎 <strong>Your personalized health screening report is ready for download!</strong><br/><br/>"
            data['content'] += f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;'>"
            data['content'] += f"<h3 style='color: #2c5aa0; margin-top: 0;'>📄 Download Your Health Report</h3>"
            data['content'] += f"<p>Click the button below to download your personalized health screening report:</p>"
            data['content'] += f"<a href='{download_url}' style='display: inline-block; background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;'>📥 Download Report</a>"
            data['content'] += f"<p style='font-size: 12px; color: #666; margin-top: 10px;'>This link will expire in 7 days for security reasons.</p>"
            data['content'] += f"</div>"
        
        # Send the email
        print(f"Debug: Sending email to {to_email}")
        print(f"Debug: JSON data keys: {list(data.keys())}")

        response = requests.post(url, headers=headers, json=data)

        # If the cached token was rejected, refresh once and retry
        if response.status_code in (401, 403):
            try:
                access_token = get_access_token(force_refresh=True)
                response = requests.post(url, headers=_build_headers(access_token), json=data)
            except Exception:
                pass

        if response.status_code == 200:
            if download_url:
                return True, "Email sent successfully with download link"
            else:
                return True, "Email sent successfully"
        else:
            return False, f"Failed to send email. Status: {response.status_code}, Response: {response.text}"

    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def send_email_via_smtp(to_email, subject, content, attachment_path=None, download_url=None, smtp_password=None):
    """Send email via SMTP with PDF attachment or Backblaze download link"""
    try:
        if not smtp_password:
            return False, "SMTP password not provided"
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add download link to content if provided
        if download_url:
            content += f"\n\n📎 <strong>Your personalized health screening report is ready for download!</strong><br/><br/>"
            content += f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;'>"
            content += f"<h3 style='color: #2c5aa0; margin-top: 0;'>📄 Download Your Health Report</h3>"
            content += f"<p>Click the button below to download your personalized health screening report:</p>"
            content += f"<a href='{download_url}' style='display: inline-block; background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;'>📥 Download Report</a>"
            content += f"<p style='font-size: 12px; color: #666; margin-top: 10px;'>This link will expire in 7 days for security reasons.</p>"
            content += f"</div>"
        
        # Add body to email
        msg.attach(MIMEText(content, 'html'))
        
        # Add attachment if provided (for backward compatibility)
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
                
            except Exception as e:
                return False, f"Error attaching file: {str(e)}"
        
        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable security
        server.login(SMTP_USERNAME, smtp_password)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        if download_url:
            return True, "Email sent successfully with download link"
        elif attachment_path and os.path.exists(attachment_path):
            return True, "Email sent successfully with PDF attachment"
        else:
            return True, "Email sent successfully"
            
    except Exception as e:
        return False, f"SMTP Error: {str(e)}"

def test_smtp_connection(smtp_password):
    """Test SMTP connection"""
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, smtp_password)
        server.quit()
        return True, "SMTP connection successful"
    except Exception as e:
        return False, f"SMTP connection failed: {str(e)}"

def test_smtp_email_with_attachment(smtp_password):
    """Test sending email with PDF attachment via SMTP"""
    try:
        # Create a test PDF
        test_pdf_path = "test_attachment.pdf"
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "Test PDF Attachment")
        c.drawString(100, 730, "This is a test PDF for SMTP email testing.")
        c.save()
        
        # Test email content
        test_content = """
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Test Email with PDF Attachment</h2>
            <p>This is a test email sent via SMTP with a PDF attachment.</p>
            <p>If you can see this email and the PDF attachment, the SMTP method is working correctly!</p>
            
            <p>For any questions, contact our medical team:</p>
            <p>📱 <strong>WhatsApp Telemedicine:</strong> 08076490056 (Chat with a medical doctor)<br/>
            📧 <strong>Email:</strong> hello@clearlinehmo.com</p>
            
            <div style="margin-top: 40px;">
                <p>Best regards,</p>
                <p style="margin-top: 20px; font-weight: bold; color: #2c5aa0;">Clearline HMO Medical Team</p>
            </div>
        </div>
        """
        
        success, message = send_email_via_smtp(
            to_email="leocasey0@gmail.com",
            subject="Test Email with PDF Attachment - SMTP Method",
            content=test_content,
            attachment_path=test_pdf_path,
            smtp_password=smtp_password
        )
        
        # Clean up test file
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            
        return success, message
        
    except Exception as e:
        return False, f"Test email error: {str(e)}"

def analyze_blood_pressure(data_df):
    """Analyzes blood pressure data and categorizes it into ranges"""
    def categorize_bp(row):
        systolic = row['SYSTOLIC']
        diastolic = row['DIASTOLIC']
        
        if systolic < 100 or diastolic < 60:
            return 'LOW'
        elif systolic > 160 or diastolic > 99:
            return 'HIGH'
        elif (141 <= systolic <= 160) or (91 <= diastolic <= 99):
            return 'MODERATE HIGH'
        else:
            return 'NORMAL'
    
    data_df['BP_CATEGORY'] = data_df.apply(categorize_bp, axis=1)
    bp_distribution = data_df['BP_CATEGORY'].value_counts()
    bp_distribution_pct = (bp_distribution / len(data_df) * 100).round(2)
    
    return {
        'distribution': bp_distribution.to_dict(),
        'distribution_pct': bp_distribution_pct.to_dict()
    }

def analyze_blood_sugar(data_df):
    """Analyzes blood sugar data and categorizes it into ranges"""
    def categorize_glucose(reading):
        if reading > 125:
            return 'DIABETIC'
        elif 100 <= reading <= 125:
            return 'PRE_DIABETIC'
        else:
            return 'NORMAL'
    
    data_df['GLUCOSE_CATEGORY'] = data_df['BLOOD GLUCOSE'].apply(categorize_glucose)
    glucose_distribution = data_df['GLUCOSE_CATEGORY'].value_counts()
    glucose_distribution_pct = (glucose_distribution / len(data_df) * 100).round(2)
    
    return {
        'distribution': glucose_distribution.to_dict(),
        'distribution_pct': glucose_distribution_pct.to_dict()
    }

def analyze_cholesterol(data_df):
    """Analyzes cholesterol data and categorizes it into ranges"""
    def categorize_cholesterol(reading):
        if reading > 240:
            return 'HIGH'
        elif 200 <= reading <= 239:
            return 'BORDERLINE HIGH'
        else:
            return 'NORMAL'
    
    data_df['CHOLESTEROL_CATEGORY'] = data_df['CHOLESTEROL'].apply(categorize_cholesterol)
    chol_distribution = data_df['CHOLESTEROL_CATEGORY'].value_counts()
    chol_distribution_pct = (chol_distribution / len(data_df) * 100).round(2)
    
    return {
        'distribution': chol_distribution.to_dict(),
        'distribution_pct': chol_distribution_pct.to_dict()
    }

def analyze_bmi(data_df):
    """Analyzes BMI data and categorizes it into ranges"""
    def categorize_bmi(bmi):
        if bmi > 30:
            return 'OBESITY'
        elif 25 <= bmi <= 30:
            return 'OVERWEIGHT'
        elif 18.5 <= bmi <= 25:
            return 'NORMAL'
        else:
            return 'BELOW NORMAL'
    
    data_df['BMI_CATEGORY'] = data_df['BMI'].apply(categorize_bmi)
    bmi_distribution = data_df['BMI_CATEGORY'].value_counts()
    bmi_distribution_pct = (bmi_distribution / len(data_df) * 100).round(2)
    
    return {
        'distribution': bmi_distribution.to_dict(),
        'distribution_pct': bmi_distribution_pct.to_dict()
    }

def analyze_urine(data_df):
    """Analyzes urine data for glucose and protein presence"""
    data_df['GLUCOSE'] = data_df['GLUCOSE'].str.upper()
    data_df['PROTEIN'] = data_df['PROTEIN'].str.upper()
    
    glucose_distribution = data_df['GLUCOSE'].value_counts()
    glucose_distribution_pct = (glucose_distribution / len(data_df) * 100).round(2)
    
    protein_distribution = data_df['PROTEIN'].value_counts()
    protein_distribution_pct = (protein_distribution / len(data_df) * 100).round(2)
    
    return {
        'glucose': {
            'distribution': glucose_distribution.to_dict(),
            'distribution_pct': glucose_distribution_pct.to_dict()
        },
        'protein': {
            'distribution': protein_distribution.to_dict(),
            'distribution_pct': protein_distribution_pct.to_dict()
        }
    }

def analyze_staff_data(data_df, company_name):
    """Analyzes staff data from DataFrame"""
    # Convert numeric columns to float, but keep all rows
    numeric_columns = ['AGE', 'SYSTOLIC', 'DIASTOLIC', 'BLOOD GLUCOSE', 'BMI']
    for col in numeric_columns:
        data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
    
    # Check if CHOLESTEROL column exists and has valid data
    has_cholesterol = False
    if 'CHOLESTEROL' in data_df.columns:
        data_df['CHOLESTEROL'] = pd.to_numeric(data_df['CHOLESTEROL'], errors='coerce')
        if not data_df['CHOLESTEROL'].isna().all():
            has_cholesterol = True
            numeric_columns.append('CHOLESTEROL')

    # Normalize urine test columns and determine availability
    has_urine = False
    if 'GLUCOSE' in data_df.columns and 'PROTEIN' in data_df.columns:
        def _clean_urine_value(val):
            if isinstance(val, str):
                stripped = val.strip()
                if stripped == "":
                    return pd.NA
                return stripped.upper()
            return val
        data_df['GLUCOSE'] = data_df['GLUCOSE'].apply(_clean_urine_value)
        data_df['PROTEIN'] = data_df['PROTEIN'].apply(_clean_urine_value)
        urine_non_empty = data_df.dropna(subset=['GLUCOSE', 'PROTEIN'])
        has_urine = len(urine_non_empty) > 0
    
    # Calculate total number of staff
    total_staff = len(data_df)
    
    # Calculate gender distribution
    gender_counts = data_df['GENDER'].value_counts()
    gender_distribution = pd.DataFrame({
        'GENDER': gender_counts.index,
        'NO OF STAFF': gender_counts.values,
        '%OF TOTAL': (gender_counts.values / total_staff * 100).round(2)
    })
    
    # Determine availability flags for all metrics
    has_bp = data_df[['SYSTOLIC', 'DIASTOLIC']].dropna(how='any').shape[0] > 0
    has_glucose = data_df['BLOOD GLUCOSE'].dropna().shape[0] > 0
    has_bmi = data_df['BMI'].dropna().shape[0] > 0

    # Blood Pressure Analysis
    bp_analysis = None
    if has_bp:
        bp_data = data_df.dropna(subset=['SYSTOLIC', 'DIASTOLIC'])
        bp_analysis = analyze_blood_pressure(bp_data)
    
    # Blood Sugar Analysis
    glucose_analysis = None
    if has_glucose:
        glucose_data = data_df.dropna(subset=['BLOOD GLUCOSE'])
        glucose_analysis = analyze_blood_sugar(glucose_data)
    
    # Cholesterol Analysis
    chol_analysis = None
    if has_cholesterol:
        chol_data = data_df.dropna(subset=['CHOLESTEROL'])
        chol_analysis = analyze_cholesterol(chol_data)
    
    # BMI Analysis
    bmi_analysis = None
    if has_bmi:
        bmi_data = data_df.dropna(subset=['BMI'])
        bmi_analysis = analyze_bmi(bmi_data)
    
    # Urine Analysis
    urine_analysis = None
    if has_urine:
        urine_data = data_df.dropna(subset=['GLUCOSE', 'PROTEIN'])
        urine_analysis = analyze_urine(urine_data)
    
    results = {
        'company_name': company_name,
        'total_staff': total_staff,
        'gender_distribution': gender_distribution.to_dict(),
        'blood_pressure': bp_analysis,
        'blood_sugar': glucose_analysis,
        'cholesterol': chol_analysis,
        'bmi': bmi_analysis,
        'urine': urine_analysis,
        'has_cholesterol': has_cholesterol,
        'has_urine': has_urine,
        'has_bp': has_bp,
        'has_glucose': has_glucose,
        'has_bmi': has_bmi
    }
    
    return results

def get_individual_data(data_df, enrollee_id):
    """Gets individual data from DataFrame based on enrollee ID"""
    individual_row = data_df[data_df['ENROLLEE ID'] == enrollee_id]
    
    if individual_row.empty:
        raise ValueError(f"No individual found with Enrollee ID: {enrollee_id}")
    
    individual_data = individual_row.iloc[0].to_dict()
    
    # Convert numeric columns
    numeric_columns = ['AGE', 'SYSTOLIC', 'DIASTOLIC', 'BLOOD GLUCOSE', 'BMI', 'CHOLESTEROL']
    for col in numeric_columns:
        if col in individual_data and pd.notna(individual_data[col]):
            individual_data[col] = pd.to_numeric(individual_data[col], errors='coerce')
    
    # Handle PSA separately
    if 'PSA' in individual_data and pd.notna(individual_data['PSA']):
        psa_value = individual_data['PSA']
        if isinstance(psa_value, str):
            individual_data['PSA'] = psa_value
        else:
            individual_data['PSA'] = pd.to_numeric(psa_value, errors='coerce')
    
    return individual_data

def analyze_individual_health(individual_data):
    """Analyzes individual health data and provides personalized insights"""
    analysis = {}
    
    # BMI Analysis
    if pd.notna(individual_data.get('BMI')):
        bmi = individual_data['BMI']
        if bmi < 18.5:
            bmi_category = 'UNDERWEIGHT'
        elif 18.5 <= bmi <= 24.9:
            bmi_category = 'NORMAL'
        elif 25 <= bmi <= 29.9:
            bmi_category = 'OVERWEIGHT'
        else:
            bmi_category = 'OBESE'
        
        analysis['bmi'] = {
            'value': bmi,
            'category': bmi_category,
            'systolic': individual_data.get('SYSTOLIC'),
            'diastolic': individual_data.get('DIASTOLIC'),
            'blood_glucose': individual_data.get('BLOOD GLUCOSE'),
            'cholesterol': individual_data.get('CHOLESTEROL')
        }
    
    # Blood Pressure Analysis
    if pd.notna(individual_data.get('SYSTOLIC')) and pd.notna(individual_data.get('DIASTOLIC')):
        systolic = individual_data['SYSTOLIC']
        diastolic = individual_data['DIASTOLIC']
        
        if systolic < 100 or diastolic < 60:
            bp_category = 'LOW'
        elif systolic > 160 or diastolic > 99:
            bp_category = 'HIGH'
        elif (141 <= systolic <= 160) or (91 <= diastolic <= 99):
            bp_category = 'MODERATE HIGH'
        else:
            bp_category = 'NORMAL'
        
        analysis['blood_pressure'] = {
            'systolic': systolic,
            'diastolic': diastolic,
            'category': bp_category,
            'bmi': individual_data.get('BMI'),
            'blood_glucose': individual_data.get('BLOOD GLUCOSE'),
            'cholesterol': individual_data.get('CHOLESTEROL')
        }
    
    # Blood Sugar Analysis
    if pd.notna(individual_data.get('BLOOD GLUCOSE')):
        glucose = individual_data['BLOOD GLUCOSE']
        if glucose > 125:
            glucose_category = 'DIABETIC'
        elif 100 <= glucose <= 125:
            glucose_category = 'PRE_DIABETIC'
        else:
            glucose_category = 'NORMAL'
        
        analysis['blood_sugar'] = {
            'value': glucose,
            'category': glucose_category,
            'bmi': individual_data.get('BMI'),
            'systolic': individual_data.get('SYSTOLIC'),
            'diastolic': individual_data.get('DIASTOLIC'),
            'cholesterol': individual_data.get('CHOLESTEROL')
        }
    
    # Cholesterol Analysis
    if pd.notna(individual_data.get('CHOLESTEROL')):
        cholesterol = individual_data['CHOLESTEROL']
        if cholesterol > 240:
            chol_category = 'HIGH'
        elif 200 <= cholesterol <= 239:
            chol_category = 'BORDERLINE HIGH'
        else:
            chol_category = 'NORMAL'
        
        analysis['cholesterol'] = {
            'value': cholesterol,
            'category': chol_category,
            'bmi': individual_data.get('BMI'),
            'systolic': individual_data.get('SYSTOLIC'),
            'diastolic': individual_data.get('DIASTOLIC'),
            'blood_glucose': individual_data.get('BLOOD GLUCOSE')
        }
    
    # Urine Analysis
    if pd.notna(individual_data.get('GLUCOSE')) and pd.notna(individual_data.get('PROTEIN')):
        analysis['urine'] = {
            'glucose': individual_data['GLUCOSE'].upper() if isinstance(individual_data['GLUCOSE'], str) else str(individual_data['GLUCOSE']).upper(),
            'protein': individual_data['PROTEIN'].upper() if isinstance(individual_data['PROTEIN'], str) else str(individual_data['PROTEIN']).upper()
        }
    
    # PSA Analysis
    if pd.notna(individual_data.get('PSA')):
        psa_value = individual_data['PSA']
        if isinstance(psa_value, str):
            psa_result = psa_value.upper()
        else:
            if psa_value > 4.0:
                psa_result = 'POSITIVE'
            else:
                psa_result = 'NEGATIVE'
        
        analysis['psa'] = {
            'value': psa_value,
            'result': psa_result,
            'age': individual_data.get('AGE'),
            'gender': individual_data.get('GENDER')
        }
    
    return analysis

def main():
    st.set_page_config(
        page_title="Clearline HMO Health Screening Report Generator",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 Clearline HMO Health Screening Report Generator")
    st.markdown("---")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Company Report", "Individual Reports", "Bulk Email Reports", "Backblaze B2 Setup"])
    
    if page == "Company Report":
        st.header("📊 Company Health Screening Report")
        
        # File upload
        uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                data_df = pd.read_excel(uploaded_file)
                st.success(f"✅ File loaded successfully! Found {len(data_df)} records.")
                
                # Company name input
                company_name = st.text_input("Enter Company Name", value="Your Company")
                
                if st.button("Generate Company Report", type="primary"):
                    with st.spinner("Analyzing data and generating report..."):
                        try:
                            # Analyze data (no MotherDuck, no Backblaze, no emails)
                            results = analyze_staff_data(data_df, company_name)
                            
                            # Ensure reports directory exists
                            os.makedirs("reports", exist_ok=True)
                            
                            # Generate report locally for direct download
                            output_path = f"reports/{company_name.replace(' ', '_')}_Health_Screening_Report.pdf"
                            report_path = generate_report(results, output_path)
                            
                            st.success("✅ Company report generated successfully!")
                            
                            # Display download button only
                            with open(report_path, "rb") as file:
                                st.download_button(
                                    label="📥 Download Company Report",
                                    data=file.read(),
                                    file_name=os.path.basename(output_path),
                                    mime="application/pdf"
                                )
                            
                            # Display summary
                            st.subheader("📈 Report Summary")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Total Staff", results['total_staff'])
                            
                            with col2:
                                if results.get('has_bp') and results.get('blood_pressure'):
                                    normal_bp = results['blood_pressure']['distribution_pct'].get('NORMAL', 0)
                                    st.metric("Normal BP %", f"{normal_bp}%")
                            
                            with col3:
                                if results.get('has_bmi') and results.get('bmi'):
                                    normal_bmi = results['bmi']['distribution_pct'].get('NORMAL', 0)
                                    st.metric("Normal BMI %", f"{normal_bmi}%")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating report: {str(e)}")
                            
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    elif page == "Individual Reports":
        st.header("👤 Individual Health Reports")
        
        # File upload
        uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'], key="individual")
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                data_df = pd.read_excel(uploaded_file)
                st.success(f"✅ File loaded successfully! Found {len(data_df)} records.")
                
                # Enrollee ID selection
                if 'ENROLLEE ID' in data_df.columns:
                    enrollee_ids = data_df['ENROLLEE ID'].tolist()
                    selected_id = st.selectbox("Select Enrollee ID", enrollee_ids)
                    
                    if st.button("Generate Individual Report", type="primary"):
                        with st.spinner("Generating individual report..."):
                            try:
                                # Initialize MotherDuck
                                db, pdf_storage = initialize_motherduck()
                                if not db:
                                    st.error("❌ Failed to connect to MotherDuck database")
                                    return
                                
                                # Get individual data
                                individual_data = get_individual_data(data_df, selected_id)
                                analysis = analyze_individual_health(individual_data)
                                
                                # Generate individual report using ENROLLEE ID as filename
                                enrollee_id = str(selected_id)
                                clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                                output_path = f"reports/{clean_enrollee_id}.pdf"
                                report_path = generate_individual_report(individual_data, analysis, output_path)
                                
                                # Store PDF in MotherDuck
                                st.info("💾 Storing report in MotherDuck...")
                                company_name = individual_data.get('COMPANY', 'Unknown Company')
                                success = pdf_storage.store_pdf(report_path, enrollee_id, company_name)
                                if success:
                                    st.success("✅ Individual report stored in MotherDuck database")
                                else:
                                    st.warning("⚠️ Report generated but failed to store in database")
                                
                                st.success("✅ Individual report generated successfully!")
                                
                                # Display download button
                                with open(report_path, "rb") as file:
                                    st.download_button(
                                        label="📥 Download Individual Report",
                                        data=file.read(),
                                        file_name=output_path,
                                        mime="application/pdf"
                                    )
                                
                                # Display individual summary
                                st.subheader("👤 Individual Health Summary")
                                name = individual_data.get('NAME', 'Unknown')
                                st.write(f"**Name:** {name}")
                                st.write(f"**Enrollee ID:** {selected_id}")
                                
                                # Show available tests
                                available_tests = []
                                if 'bmi' in analysis:
                                    available_tests.append("BMI")
                                if 'blood_pressure' in analysis:
                                    available_tests.append("Blood Pressure")
                                if 'blood_sugar' in analysis:
                                    available_tests.append("Blood Sugar")
                                if 'cholesterol' in analysis:
                                    available_tests.append("Cholesterol")
                                if 'urine' in analysis:
                                    available_tests.append("Urine Analysis")
                                if 'psa' in analysis:
                                    available_tests.append("PSA")
                                
                                st.write(f"**Tests Available:** {', '.join(available_tests)}")
                                
                            except Exception as e:
                                st.error(f"❌ Error generating individual report: {str(e)}")
                else:
                    st.error("❌ No 'ENROLLEE ID' column found in the file.")
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    elif page == "Bulk Email Reports":
        st.header("📧 Bulk Email Individual Reports")
        
        # File upload
        uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'], key="bulk")
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                data_df = pd.read_excel(uploaded_file)
                st.success(f"✅ File loaded successfully! Found {len(data_df)} records.")
                
                # Check for EMAIL column
                if 'EMAIL' not in data_df.columns:
                    st.error("❌ No 'EMAIL' column found in the file. Please add an EMAIL column with employee email addresses.")
                else:
                    # Email Method Selection
                    st.subheader("🔧 Email Method Configuration")
                    email_method = st.radio(
                        "Choose email method:",
                        ["Backblaze B2 + Zoho Mail API (Recommended)", "Backblaze B2 + SMTP", "Zoho Mail API (No PDF attachments)", "SMTP (With PDF attachments)"],
                        help="Backblaze B2 methods store PDFs in cloud and send download links. This eliminates file size limits and email delivery issues."
                    )
                    
                    # SMTP Configuration (only show if SMTP is selected)
                    if email_method in ["SMTP (With PDF attachments)", "Backblaze B2 + SMTP"]:
                        st.subheader("⚙️ SMTP Configuration")
                        
                        with st.expander("📖 How to set up SMTP (Click to expand)"):
                            st.markdown("""
                            **To use SMTP with PDF attachments, you need to set up an App Password:**
                            
                            1. **Log into your Zoho Mail account**
                            2. **Go to Settings** → **Security** → **App Passwords**
                            3. **Generate a new App Password** for this application
                            4. **Copy the generated password** (it will look like: `abcd efgh ijkl mnop`)
                            5. **Paste it below** (without spaces)
                            
                            **SMTP Settings:**
                            - Server: `smtp.zoho.com`
                            - Port: `587`
                            - Security: `TLS`
                            - Username: `hello@clearlinehmo.com`
                            - Password: `[Your App Password]`
                            
                            **Note:** Use the App Password, NOT your regular Zoho Mail password!
                            """)
                        
                        smtp_password = st.text_input(
                            "SMTP App Password", 
                            type="password",
                            help="Enter your Zoho Mail app password (not your regular password)"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔗 Test SMTP Connection"):
                                if smtp_password:
                                    success, message = test_smtp_connection(smtp_password)
                                    if success:
                                        st.success(f"✅ {message}")
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error("Please enter SMTP password first")
                        
                        with col2:
                            if st.button("📧 Test Email with Attachment"):
                                if smtp_password:
                                    with st.spinner("Sending test email..."):
                                        success, message = test_smtp_email_with_attachment(smtp_password)
                                        if success:
                                            st.success(f"✅ {message}")
                                        else:
                                            st.error(f"❌ {message}")
                                else:
                                    st.error("Please enter SMTP password first")
                    else:
                        # Zoho API Test
                        st.subheader("🔧 Zoho Mail API Test")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Test Zoho Mail Connection"):
                                with st.spinner("Testing connection..."):
                                    success, message = test_zoho_connection()
                                    if success:
                                        st.success(f"✅ {message}")
                                    else:
                                        st.error(f"❌ {message}")
                        
                        with col2:
                            if st.button("Test Email with Attachment"):
                                with st.spinner("Testing email with attachment..."):
                                    success, message = test_email_with_attachment()
                                    if success:
                                        st.success(f"✅ {message}")
                                    else:
                                        st.error(f"❌ {message}")
                    
                    # Filter rows with valid emails
                    valid_emails = data_df.dropna(subset=['EMAIL'])
                    valid_emails = valid_emails[valid_emails['EMAIL'].str.contains('@', na=False)]
                    
                    st.info(f"📧 Found {len(valid_emails)} records with valid email addresses.")
                    
                    if len(valid_emails) > 0:
                        # Preview
                        st.subheader("📋 Email Preview")
                        preview_data = valid_emails[['NAME', 'ENROLLEE ID', 'EMAIL']].head(10)
                        st.dataframe(preview_data)
                        
                        # Email sending options based on method
                        if email_method == "Zoho Mail API (No PDF attachments)":
                            st.warning("⚠️ **Zoho Mail API Limitation**: The Zoho Mail API does not support PDF attachments in the current implementation. Emails will be sent with instructions on how to obtain the reports.")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                send_emails = st.button("📧 Send Notification Emails", type="primary")
                            with col2:
                                download_reports = st.button("💾 Download All Reports", type="secondary")
                        elif email_method in ["Backblaze B2 + Zoho Mail API (Recommended)", "Backblaze B2 + SMTP"]:
                            st.success("✅ **Backblaze B2 Method**: PDFs will be stored in cloud storage and customers will receive secure download links!")
                            
                            # Test Backblaze connection first
                            if st.button("🔗 Test Backblaze B2 Connection"):
                                test_backblaze_connection()
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                send_emails = st.button("📧 Send Emails with Download Links", type="primary")
                            with col2:
                                download_reports = st.button("💾 Download All Reports", type="secondary")
                        else:  # SMTP method
                            st.success("✅ **SMTP Method**: This method supports PDF attachments!")
                            
                            if not smtp_password:
                                st.error("⚠️ Please configure SMTP password above before sending emails.")
                                send_emails = False
                                download_reports = False
                            else:
                                with st.expander("ℹ️ About Rate Limiting (Click to expand)"):
                                    st.markdown("""
                                    **Why does this happen?**
                                    - Zoho Mail has built-in spam protection
                                    - Sending too many emails quickly triggers rate limiting
                                    - This is normal for bulk email sending
                                    
                                    **How we prevent it:**
                                    - ⏱️ **Delay between emails**: 3 seconds (configurable)
                                    - 📦 **Batch processing**: 10 emails per batch (configurable)
                                    - ⏸️ **Longer breaks**: 30 seconds between batches
                                    - 🔄 **Automatic retry**: If rate limited, wait and retry once
                                    
                                    **Recommended settings:**
                                    - **Small lists (1-20)**: 3 seconds delay, batch size 10
                                    - **Medium lists (21-100)**: 5 seconds delay, batch size 5
                                    - **Large lists (100+)**: 10 seconds delay, batch size 3
                                    
                                    **If you still get rate limited:**
                                    - Increase the delay between emails
                                    - Reduce the batch size
                                    - Wait 1-2 hours before trying again
                                    """)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    send_emails = st.button("📧 Send Emails with PDF Attachments", type="primary")
                                with col2:
                                    download_reports = st.button("💾 Download All Reports", type="secondary")
                        
                        if download_reports:
                            # Initialize Backblaze B2
                            if not initialize_backblaze():
                                st.error("❌ Failed to connect to Backblaze B2")
                                return
                            
                            st.info("☁️ Using Backblaze B2 for PDF storage...")
                            
                            # Generate all reports for download
                            st.info("Generating all individual reports...")
                            download_links = []
                            for idx, (_, row) in enumerate(valid_emails.iterrows()):
                                try:
                                    individual_data = row.to_dict()
                                    analysis = analyze_individual_health(individual_data)
                                    # Use ENROLLEE ID as filename
                                    enrollee_id = str(row['ENROLLEE ID'])
                                    clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                                    output_path = f"reports/{clean_enrollee_id}.pdf"
                                    generate_individual_report(individual_data, analysis, output_path)
                                    
                                    # Upload to Backblaze B2
                                    company_name = individual_data.get('COMPANY', 'Bulk Reports')
                                    upload_success, upload_message, backblaze_url = upload_pdf_to_backblaze(
                                        output_path, enrollee_id, company_name
                                    )
                                    if upload_success:
                                        st.success(f"✅ Uploaded {row['NAME']}'s report to Backblaze B2")
                                    else:
                                        st.warning(f"⚠️ Failed to upload {row['NAME']}'s report to Backblaze B2: {upload_message}")
                                    
                                    download_links.append(output_path)
                                except Exception as e:
                                    st.error(f"Error generating report for {row['NAME']}: {str(e)}")
                            
                            if download_links:
                                st.success(f"✅ Generated {len(download_links)} individual reports!")
                                st.success("✅ All reports uploaded to Backblaze B2 cloud storage!")
                                st.info("All reports have been saved locally and uploaded to Backblaze B2 cloud storage.")
                        
                        if send_emails:
                            # Initialize Backblaze B2
                            if not initialize_backblaze():
                                st.error("❌ Failed to connect to Backblaze B2")
                                return
                            
                            st.info("☁️ Using Backblaze B2 for PDF storage...")
                            
                            # Batch sending configuration
                            st.subheader("⚙️ Batch Sending Configuration")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                batch_size = st.number_input(
                                    "Batch Size", 
                                    min_value=1, 
                                    max_value=50, 
                                    value=10,
                                    help="Number of emails to send before taking a longer break"
                                )
                            
                            with col2:
                                delay_seconds = st.number_input(
                                    "Delay Between Emails (seconds)", 
                                    min_value=1, 
                                    max_value=60, 
                                    value=3,
                                    help="Seconds to wait between each email"
                                )
                            
                            st.info(f"📊 **Sending Strategy**: Will send {batch_size} emails, then wait 30 seconds to prevent rate limiting.")
                            
                            with st.expander("ℹ️ About Rate Limiting (Click to expand)"):
                                st.markdown(f"""
                                **Why does this happen?**
                                - Zoho Mail has built-in spam protection
                                - Sending too many emails quickly triggers rate limiting
                                - This is normal for bulk email sending
                                
                                **How we prevent it:**
                                - ⏱️ **Delay between emails**: {delay_seconds} seconds
                                - 📦 **Batch processing**: {batch_size} emails per batch
                                - ⏸️ **Longer breaks**: 30 seconds between batches
                                - 🔄 **Automatic retry**: If rate limited, wait and retry once
                                
                                **Recommended settings:**
                                - **Small lists (1-20)**: 3 seconds delay, batch size 10
                                - **Medium lists (21-100)**: 5 seconds delay, batch size 5
                                - **Large lists (100+)**: 10 seconds delay, batch size 3
                                
                                **If you still get rate limited:**
                                - Increase the delay between emails
                                - Reduce the batch size
                                - Wait 1-2 hours before trying again
                                """)
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            success_count = 0
                            failed_count = 0
                            failed_emails = []
                            failed_emails_with_links = []  # Store failed emails with their download links
                            
                            total_emails = len(valid_emails)
                            
                            for idx, (_, row) in enumerate(valid_emails.iterrows()):
                                try:
                                    # Update progress
                                    progress = (idx + 1) / total_emails
                                    progress_bar.progress(progress)
                                    status_text.text(f"Processing {idx + 1}/{total_emails}: {row['NAME']}")
                                    
                                    # Add delay between emails to prevent rate limiting
                                    if idx > 0:  # Skip delay for first email
                                        status_text.text(f"Waiting {delay_seconds} seconds to prevent rate limiting...")
                                        time.sleep(delay_seconds)
                                    
                                    # Check if we need to take a longer break after batch
                                    if idx > 0 and idx % batch_size == 0:
                                        st.warning(f"⏸️ Completed batch of {batch_size} emails. Taking a 30-second break to prevent rate limiting...")
                                        time.sleep(30)
                                    
                                    # Get individual data
                                    individual_data = row.to_dict()
                                    
                                    # Convert numeric columns
                                    numeric_columns = ['AGE', 'SYSTOLIC', 'DIASTOLIC', 'BLOOD GLUCOSE', 'BMI', 'CHOLESTEROL']
                                    for col in numeric_columns:
                                        if col in individual_data and pd.notna(individual_data[col]):
                                            individual_data[col] = pd.to_numeric(individual_data[col], errors='coerce')
                                    
                                    # Handle PSA
                                    if 'PSA' in individual_data and pd.notna(individual_data['PSA']):
                                        psa_value = individual_data['PSA']
                                        if isinstance(psa_value, str):
                                            individual_data['PSA'] = psa_value
                                        else:
                                            individual_data['PSA'] = pd.to_numeric(psa_value, errors='coerce')
                                    
                                    # Analyze health
                                    analysis = analyze_individual_health(individual_data)
                                    
                                    # Generate report using ENROLLEE ID as filename
                                    enrollee_id = str(row['ENROLLEE ID'])
                                    # Clean the ID for filename but keep it readable
                                    clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                                    output_path = f"reports/{clean_enrollee_id}.pdf"
                                    
                                    # Create temporary file
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                        temp_path = tmp_file.name
                                    
                                    # Generate report to temporary file
                                    generate_individual_report(individual_data, analysis, temp_path)
                                    
                                    # Get company name for Backblaze B2 organization
                                    company_name = individual_data.get('COMPANY', 'Bulk Email Reports')
                                    
                                    # Upload to Backblaze B2 if using Backblaze method
                                    download_url = None
                                    if email_method in ["Backblaze B2 + Zoho Mail API (Recommended)", "Backblaze B2 + SMTP"]:
                                        upload_success, upload_message, backblaze_url = upload_pdf_to_backblaze(
                                            temp_path, enrollee_id, company_name
                                        )
                                        if upload_success:
                                            download_url = backblaze_url
                                            st.success(f"✅ Uploaded {row['NAME']}'s report to Backblaze B2")
                                            st.info(f"🔗 Download URL: {backblaze_url}")
                                        else:
                                            st.warning(f"⚠️ Failed to upload {row['NAME']}'s report to Backblaze B2: {upload_message}")
                                    
                                    # Prepare email content
                                    name = individual_data.get('NAME', 'Valued Employee')
                                    subject = f"Your Personalized Health Screening Report - Clearline HMO"
                                    content = f"""<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                        <p>Dear <strong>{name}</strong>,</p>
                                        
                                        <p>Thank you for participating in our health screening program. We are pleased to share your personalized health screening report with you.</p>
                                        
                                        <p>Your comprehensive report contains:</p>
                                        <ul>
                                            <li>Detailed analysis of your health metrics</li>
                                            <li>Personalized recommendations based on your results</li>
                                            <li>Educational content about maintaining good health</li>
                                            <li>Contact information for follow-up care</li>
                                        </ul>
                                        
                                        <p><strong>Important Notes:</strong></p>
                                        <ul>
                                            <li>This report is confidential and should be shared only with your healthcare provider</li>
                                            <li>We recommend discussing any concerns with your doctor</li>
                                            <li>Keep this report for your medical records</li>
                                        </ul>
                                        
                                        <p>If you have any questions about your results, please contact our medical team:</p>
                                        <p>📱 <strong>WhatsApp Telemedicine:</strong> 08076490056 (Chat with a medical doctor)<br/>
                                        📧 <strong>Email:</strong> hello@clearlinehmo.com</p>
                                        
                                        <p>We are committed to supporting your health and wellbeing.</p>
                                        
                                        <div style="margin-top: 40px;">
                                            <p>Best regards,</p>
                                            <p style="margin-top: 20px; font-weight: bold; color: #2c5aa0;">Clearline HMO Medical Team</p>
                                        </div>
                                        
                                        <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                                        <p style="font-size: 12px; color: #666; margin-top: 10px;">This is an automated message. Please do not reply to this email.</p>
                                    </div>"""
                                    
                                    # Send email using selected method
                                    if email_method == "SMTP (With PDF attachments)":
                                        success, message = send_email_via_smtp(
                                            to_email=row['EMAIL'],
                                            subject=subject,
                                            content=content,
                                            attachment_path=temp_path,
                                            smtp_password=smtp_password
                                        )
                                    elif email_method == "Backblaze B2 + SMTP":
                                        success, message = send_email_via_smtp(
                                            to_email=row['EMAIL'],
                                            subject=subject,
                                            content=content,
                                            download_url=download_url,
                                            smtp_password=smtp_password
                                        )
                                    elif email_method == "Backblaze B2 + Zoho Mail API (Recommended)":
                                        success, message = send_email_via_zoho(
                                            to_email=row['EMAIL'],
                                            subject=subject,
                                            content=content,
                                            download_url=download_url
                                        )
                                    else:  # Zoho API (legacy)
                                        success, message = send_email_via_zoho(
                                            to_email=row['EMAIL'],
                                            subject=subject,
                                            content=content,
                                            download_url=None
                                        )
                                    
                                    if success:
                                        success_count += 1
                                        st.success(f"✅ Sent to {row['NAME']} ({row['EMAIL']})")
                                    else:
                                        # Check if it's a rate limiting error
                                        if "Unusual sending activity" in message or "550" in message:
                                            st.warning(f"⚠️ Rate limit hit for {row['NAME']}. Waiting 30 seconds before continuing...")
                                            time.sleep(30)  # Wait 30 seconds for rate limit to reset
                                            
                                            # Retry once after waiting
                                            if email_method == "SMTP (With PDF attachments)":
                                                success, message = send_email_via_smtp(
                                                    to_email=row['EMAIL'],
                                                    subject=subject,
                                                    content=content,
                                                    attachment_path=temp_path,
                                                    smtp_password=smtp_password
                                                )
                                            elif email_method == "Backblaze B2 + SMTP":
                                                success, message = send_email_via_smtp(
                                                    to_email=row['EMAIL'],
                                                    subject=subject,
                                                    content=content,
                                                    download_url=download_url,
                                                    smtp_password=smtp_password
                                                )
                                            elif email_method == "Backblaze B2 + Zoho Mail API (Recommended)":
                                                success, message = send_email_via_zoho(
                                                    to_email=row['EMAIL'],
                                                    subject=subject,
                                                    content=content,
                                                    download_url=download_url
                                                )
                                            else:  # Zoho API (legacy)
                                                success, message = send_email_via_zoho(
                                                    to_email=row['EMAIL'],
                                                    subject=subject,
                                                    content=content,
                                                    download_url=None
                                                )
                                            
                                            if success:
                                                success_count += 1
                                                st.success(f"✅ Sent to {row['NAME']} ({row['EMAIL']}) - Retry successful")
                                            else:
                                                failed_count += 1
                                                failed_emails.append({
                                                    'Name': row['NAME'],
                                                    'Email': row['EMAIL'],
                                                    'Error': f"Rate limit retry failed: {message}"
                                                })
                                                # Store failed email with download link if available
                                                if download_url:
                                                    failed_emails_with_links.append({
                                                        'name': row['NAME'],
                                                        'email': row['EMAIL'],
                                                        'error': f"Rate limit retry failed: {message}",
                                                        'download_url': download_url
                                                    })
                                                st.error(f"❌ Failed to send to {row['NAME']} ({row['EMAIL']}) after retry: {message}")
                                        else:
                                            failed_count += 1
                                            failed_emails.append({
                                                'Name': row['NAME'],
                                                'Email': row['EMAIL'],
                                                'Error': message
                                            })
                                            # Store failed email with download link if available
                                            if download_url:
                                                failed_emails_with_links.append({
                                                    'name': row['NAME'],
                                                    'email': row['EMAIL'],
                                                    'error': message,
                                                    'download_url': download_url
                                                })
                                            st.error(f"❌ Failed to send to {row['NAME']} ({row['EMAIL']}): {message}")
                                    
                                    # Clean up temporary file
                                    try:
                                        os.unlink(temp_path)
                                    except:
                                        pass
                                    
                                    # Small delay to avoid rate limiting
                                    time.sleep(0.5)
                                    
                                except Exception as e:
                                    failed_count += 1
                                    failed_emails.append({
                                        'Name': row.get('NAME', 'Unknown'),
                                        'Email': row.get('EMAIL', 'Unknown'),
                                        'Error': str(e)
                                    })
                            
                            # Final results
                            progress_bar.progress(1.0)
                            status_text.text("✅ Email sending completed!")
                            
                            # Display results
                            col1, col2 = st.columns(2)
                            with col1:
                                st.success(f"✅ Successfully sent: {success_count} emails")
                            with col2:
                                st.error(f"❌ Failed to send: {failed_count} emails")
                            
                            # Show failed emails if any
                            if failed_emails:
                                st.subheader("❌ Failed Emails")
                                failed_df = pd.DataFrame(failed_emails)
                                st.dataframe(failed_df)
                                
                                # Download failed emails as CSV
                                csv = failed_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Failed Emails List",
                                    data=csv,
                                    file_name="failed_emails.csv",
                                    mime="text/csv"
                                )
                            
                            # Show failed emails with download links if any
                            if failed_emails_with_links:
                                st.subheader("🔗 Failed Emails with Download Links")
                                st.info("These emails failed to send, but the reports were uploaded successfully. You can manually send the download links to these customers.")
                                
                                for failed_email in failed_emails_with_links:
                                    with st.expander(f"📧 {failed_email['name']} ({failed_email['email']})"):
                                        st.write(f"**Error:** {failed_email['error']}")
                                        st.write(f"**Download Link:** {failed_email['download_url']}")
                                        
                                        # Copy button for the link
                                        if st.button(f"📋 Copy Link for {failed_email['name']}", key=f"copy_{failed_email['email']}"):
                                            st.write("Link copied to clipboard! (You can paste it manually)")
                                
                                # Download failed emails with links as CSV
                                failed_with_links_df = pd.DataFrame(failed_emails_with_links)
                                csv_with_links = failed_with_links_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Failed Emails with Links (CSV)",
                                    data=csv_with_links,
                                    file_name="failed_emails_with_links.csv",
                                    mime="text/csv"
                                )
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    elif page == "Backblaze B2 Setup":
        st.header("☁️ Backblaze B2 Cloud Storage Setup")
        
        st.markdown("""
        **Backblaze B2 Integration** allows you to store PDF reports in the cloud and send secure download links to customers instead of email attachments.
        
        ### Benefits:
        - ✅ **No file size limits** - Store large PDFs without email attachment restrictions
        - ✅ **Secure access** - Generate time-limited download links (24 hours)
        - ✅ **Cost effective** - Pay only for storage used
        - ✅ **Reliable delivery** - No email delivery issues with large attachments
        - ✅ **Better user experience** - Customers get direct download links
        """)
        
        # Configuration section
        st.subheader("🔧 Configuration")
        
        with st.expander("📖 Setup Instructions (Click to expand)"):
            st.markdown("""
            **Step 1: Create Backblaze B2 Account**
            1. Go to [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html)
            2. Sign up for a free account (10GB free storage)
            3. Create a new bucket for your health reports
            
            **Step 2: Get API Credentials**
            1. Go to [App Keys](https://secure.backblaze.com/user_account.htm)
            2. Create a new Application Key
            3. Copy the Key ID and Application Key
            
            **Step 3: Configure Environment**
            1. Copy `backblaze_credentials.env.example` to `backblaze_credentials.env`
            2. Fill in your credentials in the `.env` file
            3. Restart the application
            
            **Step 4: Test Connection**
            Use the test button below to verify your setup.
            """)
        
        # Test connection
        st.subheader("🧪 Test Connection")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔗 Test Backblaze B2 Connection", type="primary"):
                test_backblaze_connection()
        
        with col2:
            if st.button("📋 View Current Configuration"):
                st.info("Current Backblaze B2 Configuration:")
                st.code(f"""
Bucket Name: {backblaze_native_manager.config.BUCKET_NAME}
URL Expiry: {backblaze_native_manager.config.URL_EXPIRY_HOURS} hours
Key ID: {backblaze_native_manager.config.APPLICATION_KEY_ID[:10]}...
Application Key: {backblaze_native_manager.config.APPLICATION_KEY[:10]}...
                """)
        
        # File management
        st.subheader("📁 File Management")
        
        if st.button("📋 List Uploaded Files"):
            success, message, files = backblaze_native_manager.list_files()
            if success:
                if files:
                    st.success(f"Found {len(files)} files in Backblaze B2:")
                    for file_info in files[:10]:  # Show first 10 files
                        st.write(f"• {file_info['key']} ({file_info['size']} bytes)")
                    if len(files) > 10:
                        st.info(f"... and {len(files) - 10} more files")
                else:
                    st.info("No files found in Backblaze B2")
            else:
                st.error(f"Error listing files: {message}")
        
        # Usage statistics
        st.subheader("📊 Usage Information")
        
        st.info("""
        **How it works:**
        1. When you generate individual reports, they are automatically uploaded to Backblaze B2
        2. A secure download link is generated for each report
        3. The download link is included in the email sent to customers
        4. Links expire after 24 hours for security
        5. No need for the medical_portal.py script anymore!
        """)
        
        # Migration notice
        st.subheader("🔄 Migration from Local Storage")
        
        st.warning("""
        **Important:** Once you enable Backblaze B2 integration:
        - PDFs will be stored in the cloud instead of locally
        - Customers will receive download links instead of needing the portal
        - You can disable the medical_portal.py script
        - Local PDF files will still be created for backup
        """)

if __name__ == "__main__":
    main()
