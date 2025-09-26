# Clearline HMO Medical Report Portal

A secure web portal for customers to access their individual medical reports.

## Features

- 🔐 Secure multi-factor authentication (ID + Email + Phone)
- 📱 Mobile-responsive design
- 🏥 Clearline HMO branding
- 📊 Individual medical report access
- 🔒 Session-based security

## Quick Deploy

### Railway
1. Connect this repository to Railway
2. Railway will auto-detect Python and install dependencies
3. Deploy automatically

### Manual Setup
```bash
pip install -r requirements_portal.txt
python medical_portal.py
```

## Required Files

- `customers.csv` - Customer data (upload separately)
- `reports/` - PDF reports folder (upload separately)
- `templates/` - HTML templates
- `static/` - Static assets (logo, etc.)

## Environment Variables

- `SECRET_KEY` - Flask secret key
- `REPORTS_FOLDER` - Path to reports folder (default: reports)
- `CUSTOMER_DATA_FILE` - Path to customers.csv (default: customers.csv)

## Admin Access

Visit `/admin/stats?password=admin123` for usage statistics.