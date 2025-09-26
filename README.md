# Health Screening Report Generator

This script analyzes health screening data from an Excel workbook and generates a comprehensive PDF report.

## Features

- Analyzes multiple health metrics:
  - Blood Pressure
  - Blood Sugar
  - Cholesterol
  - BMI
  - Urine Analysis (Glucose and Protein)
- Provides detailed breakdowns by gender and age
- Generates a professional PDF report with tables and statistics

## Requirements

- Python 3.7 or higher
- Required packages listed in `requirements.txt`

## Installation

1. Clone this repository or download the files
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Excel Workbook Format

The script expects an Excel workbook with the following sheets:

1. `DATA` - Contains basic staff information:
   - NAME
   - ENROLLEE ID
   - GENDER
   - AGE

2. `BLOOD PRESSURE` - Contains blood pressure readings:
   - NAME
   - ENROLLEE ID
   - SYSTOLIC
   - DIASTOLIC

3. `BLOOD GLUCOSE` - Contains blood sugar readings:
   - NAME
   - ENROLLEE ID
   - READINGS

4. `CHOLESTEROL` - Contains cholesterol readings:
   - NAME
   - ENROLLEE ID
   - READINGS

5. `BMI` - Contains BMI data:
   - NAME
   - ENROLLEE ID
   - BMI

6. `URINE` - Contains urine analysis results:
   - NAME
   - ENROLLEE ID
   - GLUCOSE
   - PROTEIN

## Usage

1. Prepare your Excel workbook according to the format above
2. Run the script:
   ```python
   from HEALTH_SCREEN import analyze_staff_data
   from report_generator import generate_report

   # Replace with your file path and company name
   file_path = 'your_data.xlsx'
   company_name = 'YOUR COMPANY NAME'
   output_path = f"{company_name.replace(' ', '_')}_Health_Screening_Report.pdf"

   # Generate the report
   results = analyze_staff_data(file_path, company_name)
   report_path = generate_report(results, output_path)
   print(f"Report generated successfully at: {report_path}")
   ```

## Report Format

The generated PDF report includes:

1. Title page with company name
2. Summary section with:
   - Total number of staff
   - Gender distribution
3. Health metrics analysis with:
   - Blood pressure distribution
   - Blood sugar levels
   - Cholesterol levels
   - BMI categories
   - Urine analysis results

Each metric includes:
- Overall distribution
- Distribution by gender
- Average age by category

## Reference Ranges

### Blood Pressure
- NORMAL: Systolic (100-140) and Diastolic (60-90)
- MODERATE HIGH: Systolic (141-160) or Diastolic (91-99)
- HIGH: Systolic (>160) or Diastolic (>99)
- LOW: Systolic (<100) or Diastolic (<60)

### Blood Sugar
- NORMAL: 70-99
- PRE_DIABETIC: 100-125
- DIABETIC: >125

### Cholesterol
- NORMAL: <200
- BORDERLINE HIGH: 200-239
- HIGH: >240

### BMI
- BELOW NORMAL: <18.5
- NORMAL: 18.5-25
- OVERWEIGHT: 25-30
- OBESITY: >30

### Urine Analysis
Both Glucose and Protein results are reported as either Positive or Negative 