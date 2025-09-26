# Clearline HMO Health Screening Report Generator - Streamlit App

A modern web application for generating health screening reports for companies and individuals, with integrated email functionality.

## Features

### 🏢 Company Reports
- Upload Excel files with health screening data
- Generate comprehensive PDF reports
- Analyze blood pressure, blood sugar, BMI, cholesterol, and urine tests
- Download reports instantly

### 👤 Individual Reports
- Select specific enrollees from uploaded data
- Generate personalized health reports
- Download individual PDF reports

### 📧 Bulk Email Reports
- Send individual reports to multiple employees via email
- Automatic email generation using Zoho Mail API
- Progress tracking and error reporting
- Skip rows without valid email addresses
- Download list of failed email addresses

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Run the application:**
   ```bash
   python run_app.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run streamlit_health_app.py
   ```

## Usage

### 1. Company Reports
1. Navigate to "Company Report" page
2. Upload your Excel file with health screening data
3. Enter the company name
4. Click "Generate Company Report"
5. Download the generated PDF

### 2. Individual Reports
1. Navigate to "Individual Reports" page
2. Upload your Excel file
3. Select an enrollee ID from the dropdown
4. Click "Generate Individual Report"
5. Download the personalized PDF

### 3. Bulk Email Reports
1. Navigate to "Bulk Email Reports" page
2. Upload your Excel file (must include EMAIL column)
3. Preview the email list
4. Click "Send Individual Reports via Email"
5. Monitor progress and view results

## Excel File Requirements

Your Excel file should contain the following columns:
- `NAME` - Employee name
- `ENROLLEE ID` - Unique identifier
- `EMAIL` - Email address (for bulk email feature)
- `AGE` - Employee age
- `GENDER` - Employee gender
- `SYSTOLIC` - Blood pressure systolic reading
- `DIASTOLIC` - Blood pressure diastolic reading
- `BLOOD GLUCOSE` - Blood sugar level
- `BMI` - Body Mass Index
- `CHOLESTEROL` - Cholesterol level (optional)
- `GLUCOSE` - Urine glucose test result (optional)
- `PROTEIN` - Urine protein test result (optional)
- `PSA` - PSA test result (optional)

## Email Configuration

The app uses Zoho Mail API for sending emails. The configuration is set in the `streamlit_health_app.py` file:

```python
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REFRESH_TOKEN = "your_refresh_token"
ACCOUNT_ID = "your_account_id"
```

## Features

- **Responsive Design**: Works on desktop and mobile devices
- **Progress Tracking**: Real-time progress bars for bulk operations
- **Error Handling**: Comprehensive error reporting and recovery
- **Data Validation**: Automatic validation of uploaded data
- **Email Integration**: Seamless email delivery via Zoho Mail
- **Report Customization**: Personalized reports for each individual

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Email Sending Fails**: Check your Zoho Mail API credentials

3. **File Upload Issues**: Ensure your Excel file has the required columns

4. **Report Generation Fails**: Check that your data contains valid numeric values

### Support

For technical support, contact the development team or check the application logs for detailed error messages.

## Security Notes

- Email credentials are hardcoded in the application
- Consider using environment variables for production deployment
- Ensure your Zoho Mail API has appropriate rate limits configured

## License

This application is proprietary to Clearline HMO.
