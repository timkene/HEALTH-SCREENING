# 🏥 Clearline HMO Medical Report Portal - Complete Setup Guide

## 📋 Overview
This secure web portal allows customers to access their individual health screening reports by verifying their identity with Enrollee ID, email, and phone number.

## 🚀 Quick Start (5 Minutes)

### Step 1: Generate Customer Data
```bash
# Run the customer CSV generator
python generate_customer_csv.py
```
- Enter your Excel file path when prompted
- This creates `customers.csv` with all customer data

### Step 2: Generate Individual Reports
```bash
# Run the Streamlit app
streamlit run streamlit_health_app.py
```
- Go to "Bulk Email Reports"
- Click "Download All Reports"
- This generates all PDF reports with Enrollee ID as filename

### Step 3: Start the Portal
```bash
# Install Flask if not already installed
pip install flask pandas werkzeug

# Start the portal
python medical_portal.py
```
- Access at: `http://localhost:5000`
- Admin stats: `http://localhost:5000/admin/stats?password=admin123`

## 📁 Complete File Structure

```
HEALTH SCREEN/
├── 📊 Data Files
│   ├── customers.csv                    # Generated customer data
│   └── [your_excel_file].xlsx          # Original health screening data
│
├── 📄 PDF Reports
│   └── reports/                         # Individual PDF reports
│       ├── CL_ARIK_022_2017.pdf
│       ├── 12345.pdf
│       └── ...
│
├── 🌐 Web Portal
│   ├── medical_portal.py               # Main Flask application
│   ├── generate_customer_csv.py        # CSV generator script
│   └── templates/                      # HTML templates
│       ├── base.html
│       ├── index.html
│       ├── verify.html
│       ├── dashboard.html
│       └── error.html
│
├── 📊 Health Screening System
│   ├── streamlit_health_app.py         # Main Streamlit app
│   ├── individual_report_generator.py  # PDF report generator
│   ├── HEALTH_SCREEN.py               # Core analysis functions
│   └── report_generator.py            # Company report generator
│
└── 📝 Documentation
    ├── PORTAL_SETUP_GUIDE.md          # This guide
    └── SMTP_Setup_Guide.md            # Email setup guide
```

## 🔧 Detailed Setup Instructions

### 1. Prerequisites
```bash
# Install required packages
pip install flask pandas werkzeug streamlit reportlab openpyxl requests
```

### 2. Generate Customer Data
The `generate_customer_csv.py` script creates a CSV file with customer information:

**Input:** Excel file with columns: `ENROLLEE ID`, `NAME`, `EMAIL`, `TEL NO`
**Output:** `customers.csv` with columns: `ID`, `Name`, `Email`, `Phone`, `ReportFileName`

**Example customers.csv:**
```csv
ID,Name,Email,Phone,ReportFileName
CL/ARIK/022/2017,ALUFE GRACE OIZA,leocasey0@gmail.com,+1122334455,CL_ARIK_022_2017.pdf
12345,JOHN DOE,john@email.com,+1234567890,12345.pdf
```

### 3. Generate PDF Reports
Use the Streamlit app to generate all individual reports:

1. **Open Streamlit App:**
   ```bash
   streamlit run streamlit_health_app.py
   ```

2. **Generate Reports:**
   - Go to "Bulk Email Reports"
   - Upload your Excel file
   - Click "Download All Reports"
   - Reports will be saved with Enrollee ID as filename

### 4. Deploy the Portal

#### Local Development
```bash
python medical_portal.py
```

#### Production Deployment

**Option A: Using Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 medical_portal:app
```

**Option B: Using Docker**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "medical_portal:app"]
```

**Option C: Cloud Deployment**
- **Heroku:** Use the included `Procfile`
- **AWS:** Deploy on EC2 or Elastic Beanstalk
- **DigitalOcean:** Use App Platform or Droplets
- **Google Cloud:** Use App Engine or Compute Engine

## 🔒 Security Features

### Multi-Factor Authentication
- **Enrollee ID:** Unique patient identifier
- **Email Address:** Must match exactly (case-insensitive)
- **Phone Number:** Must match exactly

### Session Security
- **30-minute timeout:** Sessions expire automatically
- **Secure headers:** XSS protection, clickjacking prevention
- **Access logging:** All attempts logged for security monitoring

### File Protection
- **No direct access:** Reports can't be accessed via direct URLs
- **Session verification:** Must be logged in to access reports
- **Secure downloads:** Files served through Flask with proper headers

## 📊 Monitoring & Analytics

### Access Logs
All portal activity is logged to `portal_access.log`:
```
2024-01-15 10:30:15 - SUCCESS - VERIFICATION_SUCCESS - Customer: CL_ARIK_022_2017 - IP: 192.168.1.100
2024-01-15 10:31:22 - SUCCESS - REPORT_DOWNLOAD - Customer: CL_ARIK_022_2017 - IP: 192.168.1.100
```

### Admin Dashboard
Access statistics at: `http://your-domain.com/admin/stats?password=admin123`

**Features:**
- Total access attempts
- Successful logins
- Report downloads and views
- Recent activity log

## 📧 Sharing the Portal with Customers

### Email Template
```html
Subject: Your Health Screening Report is Ready - Clearline HMO

Dear [Customer Name],

Your personalized health screening report is now available in our secure portal.

🔐 Access Your Report:
1. Visit: https://your-domain.com/
2. Enter your Enrollee ID: [Customer ID]
3. Enter your email: [Customer Email]
4. Enter your phone: [Customer Phone]

📋 Your Report Contains:
• Detailed analysis of your health metrics
• Personalized recommendations
• Educational content about maintaining good health
• Contact information for follow-up care

🩺 Need Medical Consultation?
WhatsApp Telemedicine: 08076490056 (Chat with a medical doctor)
Email: hello@clearlinehmo.com

Your health information is protected and confidential.

Best regards,
Clearline HMO Medical Team
```

### SMS Template
```
Your health report is ready! Access at: https://your-domain.com/
Use your Enrollee ID: [ID], Email: [Email], Phone: [Phone]
Questions? WhatsApp: 08076490056
```

## 🛠️ Troubleshooting

### Common Issues

**1. "Customer data file not found"**
```bash
# Solution: Generate the CSV file
python generate_customer_csv.py
```

**2. "Report file not found"**
```bash
# Solution: Generate the PDF reports
# Use Streamlit app → Bulk Email Reports → Download All Reports
```

**3. "Invalid credentials"**
- Check that the customer data in CSV matches exactly
- Ensure email addresses are in lowercase
- Verify phone numbers match exactly

**4. "Port already in use"**
```bash
# Solution: Change port or kill existing process
python medical_portal.py  # Will use port 5000
# Or kill process: sudo lsof -t -i:5000 | xargs kill
```

**5. "Template not found"**
- Ensure `templates/` folder exists
- All HTML files should be in the `templates/` folder

### Performance Optimization

**For Large Customer Bases (1000+ customers):**
1. **Use a database** instead of CSV (PostgreSQL, MySQL)
2. **Implement caching** for customer data
3. **Use CDN** for static files
4. **Load balancing** for multiple servers

**For High Traffic:**
1. **Rate limiting** to prevent abuse
2. **Redis** for session storage
3. **Nginx** as reverse proxy
4. **SSL/TLS** encryption

## 🔐 Security Best Practices

### Production Deployment
1. **Change admin password** in `medical_portal.py`
2. **Use HTTPS** with SSL certificate
3. **Regular backups** of customer data and reports
4. **Monitor access logs** for suspicious activity
5. **Update dependencies** regularly

### Data Protection
1. **Encrypt sensitive data** at rest
2. **Secure file permissions** (600 for reports)
3. **Regular security audits**
4. **GDPR compliance** for data handling

## 📱 Mobile Optimization

The portal is fully responsive and works on:
- ✅ Desktop computers
- ✅ Tablets
- ✅ Mobile phones
- ✅ All modern browsers

## 🚀 Advanced Features (Future Enhancements)

### Planned Features
1. **Email notifications** when reports are ready
2. **SMS verification** for additional security
3. **Report sharing** with healthcare providers
4. **Multi-language support**
5. **API endpoints** for integration
6. **Advanced analytics** dashboard

### Integration Options
1. **Electronic Health Records (EHR)**
2. **Practice Management Systems**
3. **Telemedicine platforms**
4. **Health monitoring devices**

## 📞 Support & Maintenance

### Regular Maintenance
- **Weekly:** Check access logs for issues
- **Monthly:** Update dependencies
- **Quarterly:** Security audit and backup verification

### Support Contacts
- **Technical Issues:** Development team
- **Medical Questions:** WhatsApp 08076490056
- **General Support:** hello@clearlinehmo.com

---

## 🎉 You're All Set!

Your medical report portal is now ready for production use. Customers can securely access their health reports using their Enrollee ID, email, and phone number.

**Next Steps:**
1. Test the portal thoroughly
2. Deploy to production server
3. Share portal link with customers
4. Monitor usage and feedback
5. Plan for future enhancements

**Remember:** Always keep your customer data and reports secure, and regularly backup your system!
