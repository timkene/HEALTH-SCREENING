# Clearline HMO Health Screening Report Generator

## Overview
This enhanced health screening report generator now supports both **company-wide reports** and **individual personalized reports** for your health insurance clients.

## Features

### 1. Company Reports (Original Functionality)
- Generates comprehensive health screening reports for entire companies
- Analyzes all staff data collectively
- Provides statistical analysis and recommendations
- Creates professional PDF reports with charts and graphs

### 2. Individual Reports (New Feature)
- Generates personalized health reports for individual employees
- Uses enrollee ID to identify specific individuals
- Provides detailed, educational content about each health parameter
- Cross-references different health metrics
- Includes personalized recommendations and health guidance

## How to Use

### Running the Application
```bash
python HEALTH_SCREEN.py
```

### Menu Options
1. **Generate Company Report** - Creates reports for entire companies
2. **Generate Individual Report** - Creates personalized reports for individuals
3. **Exit** - Close the application

### Individual Report Process
1. Select option 2 from the menu
2. Enter the path to your Excel file (or press Enter for default)
3. Enter the Enrollee ID of the person you want to generate a report for
4. The system will generate a personalized PDF report

## Excel File Format
Your Excel file should contain the following columns:
- **NAME** - Employee's full name
- **ENROLLEE ID** - Unique identifier for each employee
- **WEIGHT** - Weight in kg
- **HEIGHT** - Height in cm
- **AGE** - Age in years
- **GENDER** - Male/Female
- **SYSTOLIC** - Systolic blood pressure
- **DIASTOLIC** - Diastolic blood pressure
- **BLOOD GLUCOSE** - Blood sugar level
- **BMI** - Body Mass Index
- **GLUCOSE** - Urine glucose (POSITIVE/NEGATIVE)
- **PROTEIN** - Urine protein (POSITIVE/NEGATIVE)
- **CHOLESTEROL** - Total cholesterol level
- **PSA** - Prostate Specific Antigen (optional)
- **EMAIL** - Email address
- **TEL NO** - Phone number

## Individual Report Features

### Personalized Header
- Employee's name prominently displayed
- Enrollee ID clearly shown
- Professional Clearline HMO branding

### Educational Content
Each health parameter includes:
- **Definition** - What the parameter measures
- **Normal Ranges** - Standard reference values
- **Personal Results** - Individual's specific values
- **Health Implications** - What the results mean
- **Cross-References** - How different parameters relate to each other
- **Personalized Recommendations** - Specific advice based on results

### Health Parameters Covered
1. **BMI (Body Mass Index)**
   - Weight status analysis
   - Health implications of different BMI categories
   - Weight management recommendations

2. **Blood Pressure**
   - Cardiovascular health assessment
   - Hypertension risk evaluation
   - Blood pressure management strategies

3. **Blood Sugar**
   - Diabetes risk assessment
   - Pre-diabetes identification
   - Blood sugar management guidance

4. **Cholesterol**
   - Heart disease risk evaluation
   - Lipid profile analysis
   - Cholesterol management recommendations

5. **Urine Analysis**
   - Kidney function assessment
   - Diabetes screening
   - Proteinuria evaluation

### Smart Analysis
- Only includes parameters that were actually tested
- Skips missing data gracefully
- Provides cross-references between different health metrics
- Offers personalized recommendations based on individual results

## File Structure
```
HEALTH_SCREEN.py              # Main application with menu system
individual_report_generator.py # Individual report generation module
report_generator.py           # Company report generation module
test_individual_report.py     # Test script for individual reports
README_Individual_Reports.md  # This documentation file
```

## Requirements
- Python 3.6+
- pandas
- reportlab
- openpyxl (for Excel file reading)

## Installation
```bash
pip install pandas reportlab openpyxl
```

## Example Usage

### Company Report
```python
# Run the main script
python HEALTH_SCREEN.py

# Select option 1
# Enter file path: VACCIPHARM.xlsx
# Enter company name: VACCIPHARM LIMITED
# Report generated: VACCIPHARM_LIMITED_Health_Screening_Report.pdf
```

### Individual Report
```python
# Run the main script
python HEALTH_SCREEN.py

# Select option 2
# Enter file path: VACCIPHARM.xlsx
# Enter enrollee ID: 12345
# Report generated: Individual_Report_12345.pdf
```

## Benefits of Individual Reports

1. **Personalized Education** - Each employee gets tailored health information
2. **Clear Understanding** - Easy-to-understand explanations of health parameters
3. **Actionable Recommendations** - Specific advice based on individual results
4. **Professional Presentation** - High-quality PDF reports suitable for sharing
5. **Comprehensive Coverage** - All health parameters explained in detail
6. **Cross-Referenced Analysis** - Shows how different health metrics relate

## Support
For technical support or questions about the health screening reports, contact:
- WhatsApp: 0814859935
- Email: [Your support email]

## Notes
- Individual reports are generated only for employees with valid Enrollee IDs
- Missing test results are handled gracefully (parameters are skipped if not available)
- All health information is based on current medical guidelines
- Reports are generated in PDF format for easy sharing and printing
