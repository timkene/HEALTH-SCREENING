import pandas as pd
import numpy as np
from report_generator import generate_report

def analyze_blood_pressure(data_df):
    """
    Analyzes blood pressure data and categorizes it into ranges
    """
    # Define blood pressure categories
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
    
    # Add BP category column
    data_df['BP_CATEGORY'] = data_df.apply(categorize_bp, axis=1)
    
    # Calculate overall distribution
    bp_distribution = data_df['BP_CATEGORY'].value_counts()
    bp_distribution_pct = (bp_distribution / len(data_df) * 100).round(2)
    
    # Calculate distribution by gender
    bp_by_gender = data_df.groupby(['GENDER', 'BP_CATEGORY']).size().unstack(fill_value=0)
    bp_by_gender_pct = (bp_by_gender.div(bp_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate average age by BP category
    avg_age_by_bp = data_df.groupby('BP_CATEGORY')['AGE'].mean().round(2)
    
    print("\nBlood Pressure Analysis:")
    print("\nOverall Distribution:")
    for category, count in bp_distribution.items():
        print(f"{category}: {count} ({bp_distribution_pct[category]}%)")
    
    print("\nDistribution by Gender:")
    print(bp_by_gender_pct)
    
    print("\nAverage Age by BP Category:")
    print(avg_age_by_bp)
    
    return {
        'distribution': bp_distribution.to_dict(),
        'distribution_pct': bp_distribution_pct.to_dict(),
        'by_gender': bp_by_gender.to_dict(),
        'by_gender_pct': bp_by_gender_pct.to_dict(),
        'avg_age': avg_age_by_bp.to_dict()
    }

def analyze_blood_sugar(data_df):
    """
    Analyzes blood sugar data and categorizes it into ranges
    """
    # Define blood sugar categories
    def categorize_glucose(reading):
        if reading > 125:
            return 'DIABETIC'
        elif 100 <= reading <= 125:
            return 'PRE_DIABETIC'
        else:
            return 'NORMAL'
    
    # Add glucose category column
    data_df['GLUCOSE_CATEGORY'] = data_df['BLOOD GLUCOSE'].apply(categorize_glucose)
    
    # Calculate overall distribution
    glucose_distribution = data_df['GLUCOSE_CATEGORY'].value_counts()
    glucose_distribution_pct = (glucose_distribution / len(data_df) * 100).round(2)
    
    # Calculate distribution by gender
    glucose_by_gender = data_df.groupby(['GENDER', 'GLUCOSE_CATEGORY']).size().unstack(fill_value=0)
    glucose_by_gender_pct = (glucose_by_gender.div(glucose_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate average age by glucose category
    avg_age_by_glucose = data_df.groupby('GLUCOSE_CATEGORY')['AGE'].mean().round(2)
    
    print("\nBlood Sugar Analysis:")
    print("\nOverall Distribution:")
    for category, count in glucose_distribution.items():
        print(f"{category}: {count} ({glucose_distribution_pct[category]}%)")
    
    print("\nDistribution by Gender:")
    print(glucose_by_gender_pct)
    
    print("\nAverage Age by Blood Sugar Category:")
    print(avg_age_by_glucose)
    
    return {
        'distribution': glucose_distribution.to_dict(),
        'distribution_pct': glucose_distribution_pct.to_dict(),
        'by_gender': glucose_by_gender.to_dict(),
        'by_gender_pct': glucose_by_gender_pct.to_dict(),
        'avg_age': avg_age_by_glucose.to_dict()
    }

def analyze_cholesterol(data_df):
    """
    Analyzes cholesterol data and categorizes it into ranges
    """
    # Define cholesterol categories
    def categorize_cholesterol(reading):
        if reading > 240:
            return 'HIGH'
        elif 200 <= reading <= 239:
            return 'BORDERLINE HIGH'
        else:
            return 'NORMAL'
    
    # Add cholesterol category column
    data_df['CHOLESTEROL_CATEGORY'] = data_df['CHOLESTEROL'].apply(categorize_cholesterol)
    
    # Calculate overall distribution
    chol_distribution = data_df['CHOLESTEROL_CATEGORY'].value_counts()
    chol_distribution_pct = (chol_distribution / len(data_df) * 100).round(2)
    
    # Calculate distribution by gender
    chol_by_gender = data_df.groupby(['GENDER', 'CHOLESTEROL_CATEGORY']).size().unstack(fill_value=0)
    chol_by_gender_pct = (chol_by_gender.div(chol_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate average age by cholesterol category
    avg_age_by_chol = data_df.groupby('CHOLESTEROL_CATEGORY')['AGE'].mean().round(2)
    
    print("\nCholesterol Analysis:")
    print("\nOverall Distribution:")
    for category, count in chol_distribution.items():
        print(f"{category}: {count} ({chol_distribution_pct[category]}%)")
    
    print("\nDistribution by Gender:")
    print(chol_by_gender_pct)
    
    print("\nAverage Age by Cholesterol Category:")
    print(avg_age_by_chol)
    
    return {
        'distribution': chol_distribution.to_dict(),
        'distribution_pct': chol_distribution_pct.to_dict(),
        'by_gender': chol_by_gender.to_dict(),
        'by_gender_pct': chol_by_gender_pct.to_dict(),
        'avg_age': avg_age_by_chol.to_dict()
    }

def analyze_bmi(data_df):
    """
    Analyzes BMI data and categorizes it into ranges
    """
    # Define BMI categories
    def categorize_bmi(bmi):
        if bmi > 30:
            return 'OBESITY'
        elif 25 <= bmi <= 30:
            return 'OVERWEIGHT'
        elif 18.5 <= bmi <= 25:
            return 'NORMAL'
        else:
            return 'BELOW NORMAL'
    
    # Add BMI category column
    data_df['BMI_CATEGORY'] = data_df['BMI'].apply(categorize_bmi)
    
    # Calculate overall distribution
    bmi_distribution = data_df['BMI_CATEGORY'].value_counts()
    bmi_distribution_pct = (bmi_distribution / len(data_df) * 100).round(2)
    
    # Calculate distribution by gender
    bmi_by_gender = data_df.groupby(['GENDER', 'BMI_CATEGORY']).size().unstack(fill_value=0)
    bmi_by_gender_pct = (bmi_by_gender.div(bmi_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate average age by BMI category
    avg_age_by_bmi = data_df.groupby('BMI_CATEGORY')['AGE'].mean().round(2)
    
    print("\nBMI Analysis:")
    print("\nOverall Distribution:")
    for category, count in bmi_distribution.items():
        print(f"{category}: {count} ({bmi_distribution_pct[category]}%)")
    
    print("\nDistribution by Gender:")
    print(bmi_by_gender_pct)
    
    print("\nAverage Age by BMI Category:")
    print(avg_age_by_bmi)
    
    return {
        'distribution': bmi_distribution.to_dict(),
        'distribution_pct': bmi_distribution_pct.to_dict(),
        'by_gender': bmi_by_gender.to_dict(),
        'by_gender_pct': bmi_by_gender_pct.to_dict(),
        'avg_age': avg_age_by_bmi.to_dict()
    }

def analyze_urine(data_df):
    """
    Analyzes urine data for glucose and protein presence
    Results are binary: POSITIVE or NEGATIVE
    """
    # Convert results to uppercase and standardize
    data_df['GLUCOSE'] = data_df['GLUCOSE'].str.upper()
    data_df['PROTEIN'] = data_df['PROTEIN'].str.upper()
    
    # Calculate glucose distribution
    glucose_distribution = data_df['GLUCOSE'].value_counts()
    glucose_distribution_pct = (glucose_distribution / len(data_df) * 100).round(2)
    
    # Calculate protein distribution
    protein_distribution = data_df['PROTEIN'].value_counts()
    protein_distribution_pct = (protein_distribution / len(data_df) * 100).round(2)
    
    # Calculate distribution by gender for glucose
    glucose_by_gender = data_df.groupby(['GENDER', 'GLUCOSE']).size().unstack(fill_value=0)
    glucose_by_gender_pct = (glucose_by_gender.div(glucose_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate distribution by gender for protein
    protein_by_gender = data_df.groupby(['GENDER', 'PROTEIN']).size().unstack(fill_value=0)
    protein_by_gender_pct = (protein_by_gender.div(protein_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate average age by glucose result
    avg_age_by_glucose = data_df.groupby('GLUCOSE')['AGE'].mean().round(2)
    
    # Calculate average age by protein result
    avg_age_by_protein = data_df.groupby('PROTEIN')['AGE'].mean().round(2)
    
    print("\nUrine Analysis:")
    print("\nGlucose Distribution:")
    for result in ['POSITIVE', 'NEGATIVE']:
        count = glucose_distribution.get(result, 0)
        pct = glucose_distribution_pct.get(result, 0)
        print(f"Glucose {result}: {count} ({pct}%)")
    
    print("\nProtein Distribution:")
    for result in ['POSITIVE', 'NEGATIVE']:
        count = protein_distribution.get(result, 0)
        pct = protein_distribution_pct.get(result, 0)
        print(f"Protein {result}: {count} ({pct}%)")
    
    print("\nGlucose Distribution by Gender:")
    print(glucose_by_gender_pct)
    
    print("\nProtein Distribution by Gender:")
    print(protein_by_gender_pct)
    
    print("\nAverage Age by Glucose Result:")
    print(avg_age_by_glucose)
    
    print("\nAverage Age by Protein Result:")
    print(avg_age_by_protein)
    
    return {
        'glucose': {
            'distribution': glucose_distribution.to_dict(),
            'distribution_pct': glucose_distribution_pct.to_dict(),
            'by_gender': glucose_by_gender.to_dict(),
            'by_gender_pct': glucose_by_gender_pct.to_dict(),
            'avg_age': avg_age_by_glucose.to_dict()
        },
        'protein': {
            'distribution': protein_distribution.to_dict(),
            'distribution_pct': protein_distribution_pct.to_dict(),
            'by_gender': protein_by_gender.to_dict(),
            'by_gender_pct': protein_by_gender_pct.to_dict(),
            'avg_age': avg_age_by_protein.to_dict()
        }
    }

def analyze_staff_data(file_path, company_name):
    """
    Analyzes staff data from an Excel workbook to extract:
    1. Total number of staff
    2. Gender distribution
    3. Age distribution
    4. Age distribution by gender
    5. Blood pressure analysis
    6. Blood sugar analysis
    7. Cholesterol analysis (if available)
    8. BMI analysis
    9. Urine analysis
    
    Parameters:
    file_path (str): Path to the Excel workbook
    company_name (str): Name of the company for the report
    
    Returns:
    dict: Analysis results
    """
    # Read the Excel file
    data_df = pd.read_excel(file_path)
    
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
        # Clean whitespace and empty strings to NaN, and standardize casing
        def _clean_urine_value(val):
            if isinstance(val, str):
                stripped = val.strip()
                if stripped == "":
                    return pd.NA
                return stripped.upper()
            return val
        data_df['GLUCOSE'] = data_df['GLUCOSE'].apply(_clean_urine_value)
        data_df['PROTEIN'] = data_df['PROTEIN'].apply(_clean_urine_value)
        # Determine if there is at least one row with both glucose and protein present
        urine_non_empty = data_df.dropna(subset=['GLUCOSE', 'PROTEIN'])
        has_urine = len(urine_non_empty) > 0
    
    # 1. Calculate total number of staff
    total_staff = len(data_df)
    print(f"Total number of staff: {total_staff}")
    
    # 2. Calculate gender distribution
    gender_counts = data_df['GENDER'].value_counts()
    gender_distribution = pd.DataFrame({
        'GENDER': gender_counts.index,
        'NO OF STAFF': gender_counts.values,
        '%OF TOTAL': (gender_counts.values / total_staff * 100).round(2)
    })
    print("\nGender Distribution:")
    print(gender_distribution)
    
    # Calculate average age by gender
    avg_age_by_gender = data_df.groupby('GENDER')['AGE'].mean().round(2)
    print("\nAverage Age by Gender:")
    print(avg_age_by_gender)
    
    # 3. Calculate age distribution with bins
    age_bins = [0, 20, 30, 40, 50, 60, 70]
    age_labels = ['0-20', '21-30', '31-40', '41-50', '51-60', '61-70']
    data_df['AGE_GROUP'] = pd.cut(data_df['AGE'], bins=age_bins, labels=age_labels, right=True)
    
    # Calculate age distribution by gender
    age_by_gender = data_df.groupby(['GENDER', 'AGE_GROUP']).size().unstack(fill_value=0)
    age_by_gender_pct = (age_by_gender.div(age_by_gender.sum(axis=1), axis=0) * 100).round(2)
    
    # Calculate overall age distribution
    age_distribution = data_df['AGE_GROUP'].value_counts().reindex(age_labels, fill_value=0)
    age_distribution_pct = (age_distribution / len(data_df) * 100).round(2)
    
    age_distribution_data = {
        'Overall Distribution': age_distribution.to_dict(),
        'Distribution Percentage': age_distribution_pct.to_dict(),
        'By Gender': age_by_gender.to_dict(),
        'By Gender Percentage': age_by_gender_pct.to_dict(),
        'Average Age by Gender': avg_age_by_gender.to_dict()
    }
    
    print("\nAge Distribution:")
    print("Overall Distribution:")
    for age_group, count in age_distribution.items():
        print(f"{age_group}: {count} ({age_distribution_pct[age_group]}%)")
    
    print("\nDistribution by Gender:")
    print(age_by_gender_pct)
    
    # Determine availability flags for all metrics
    has_bp = data_df[['SYSTOLIC', 'DIASTOLIC']].dropna(how='any').shape[0] > 0
    has_glucose = data_df['BLOOD GLUCOSE'].dropna().shape[0] > 0
    has_bmi = data_df['BMI'].dropna().shape[0] > 0

    # 5. Blood Pressure Analysis - only for rows with valid BP data
    bp_analysis = None
    if has_bp:
        bp_data = data_df.dropna(subset=['SYSTOLIC', 'DIASTOLIC'])
        bp_analysis = analyze_blood_pressure(bp_data)
    
    # 6. Blood Sugar Analysis - only for rows with valid glucose data
    glucose_analysis = None
    if has_glucose:
        glucose_data = data_df.dropna(subset=['BLOOD GLUCOSE'])
        glucose_analysis = analyze_blood_sugar(glucose_data)
    
    # 7. Cholesterol Analysis - only for rows with valid cholesterol data
    chol_analysis = None
    if has_cholesterol:
        chol_data = data_df.dropna(subset=['CHOLESTEROL'])
        chol_analysis = analyze_cholesterol(chol_data)
    
    # 8. BMI Analysis - only for rows with valid BMI data
    bmi_analysis = None
    if has_bmi:
        bmi_data = data_df.dropna(subset=['BMI'])
        bmi_analysis = analyze_bmi(bmi_data)
    
    # 9. Urine Analysis - only for rows with valid urine data
    urine_analysis = None
    if has_urine:
        urine_data = data_df.dropna(subset=['GLUCOSE', 'PROTEIN'])
        urine_analysis = analyze_urine(urine_data)
    
    results = {
        'company_name': company_name,
        'total_staff': total_staff,
        'gender_distribution': gender_distribution.to_dict(),
        'age_distribution': age_distribution_data,
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

def get_individual_data(file_path, enrollee_id):
    """
    Gets individual data from Excel file based on enrollee ID
    """
    data_df = pd.read_excel(file_path)
    
    # Find the row with the matching enrollee ID
    individual_row = data_df[data_df['ENROLLEE ID'] == enrollee_id]
    
    if individual_row.empty:
        raise ValueError(f"No individual found with Enrollee ID: {enrollee_id}")
    
    # Convert to dictionary for easier access
    individual_data = individual_row.iloc[0].to_dict()
    
    # Convert numeric columns (excluding PSA which can be text like POSITIVE/NEGATIVE)
    numeric_columns = ['AGE', 'SYSTOLIC', 'DIASTOLIC', 'BLOOD GLUCOSE', 'BMI', 'CHOLESTEROL']
    for col in numeric_columns:
        if col in individual_data and pd.notna(individual_data[col]):
            individual_data[col] = pd.to_numeric(individual_data[col], errors='coerce')
    
    # Handle PSA separately - it can be text (POSITIVE/NEGATIVE) or numeric
    if 'PSA' in individual_data and pd.notna(individual_data['PSA']):
        psa_value = individual_data['PSA']
        if isinstance(psa_value, str):
            # Keep as string if it's POSITIVE/NEGATIVE
            individual_data['PSA'] = psa_value
        else:
            # Convert to numeric if it's a number
            individual_data['PSA'] = pd.to_numeric(psa_value, errors='coerce')
    
    return individual_data

def analyze_individual_health(individual_data):
    """
    Analyzes individual health data and provides personalized insights
    """
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
    
    # PSA Analysis (only for men above 40)
    if pd.notna(individual_data.get('PSA')):
        psa_value = individual_data['PSA']
        if isinstance(psa_value, str):
            psa_result = psa_value.upper()
        else:
            # If it's a numeric value, interpret it
            if psa_value > 4.0:  # Normal threshold is around 4.0 ng/mL
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

def show_menu():
    """
    Displays the main menu for report selection
    """
    print("\n" + "="*60)
    print("CLEARLINE HMO - HEALTH SCREENING REPORT GENERATOR")
    print("="*60)
    print("1. Generate Company Report")
    print("2. Generate Individual Report")
    print("3. Exit")
    print("="*60)
    
    while True:
        choice = input("\nPlease select an option (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def get_company_info():
    """
    Gets company information from user
    """
    file_path = input("Enter the path to your Excel file: ").strip()
    if not file_path:
        file_path = 'VACCIPHARM.xlsx'  # Default file
    
    company_name = input("Enter company name: ").strip()
    if not company_name:
        company_name = 'VACCIPHARM LIMITED'  # Default name
    
    return file_path, company_name

def get_individual_info():
    """
    Gets individual information from user
    """
    file_path = input("Enter the path to your Excel file: ").strip()
    if not file_path:
        file_path = 'VACCIPHARM.xlsx'  # Default file
    
    enrollee_id = input("Enter the Enrollee ID: ").strip()
    if not enrollee_id:
        raise ValueError("Enrollee ID is required")
    
    return file_path, enrollee_id

if __name__ == "__main__":
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Company Report
            try:
                file_path, company_name = get_company_info()
                output_path = f"reports/{company_name.replace(' ', '_')}_Health_Screening_Report.pdf"
                
                print(f"\nGenerating company report for {company_name}...")
                results = analyze_staff_data(file_path, company_name)
                print("Data analysis completed successfully!")
                
                report_path = generate_report(results, output_path)
                print(f"Company report generated successfully! Path: {report_path}")
                
            except Exception as e:
                print(f"An error occurred: {e}")
        
        elif choice == '2':
            # Individual Report
            try:
                file_path, enrollee_id = get_individual_info()
                
                print(f"\nGenerating individual report for Enrollee ID: {enrollee_id}...")
                individual_data = get_individual_data(file_path, enrollee_id)
                analysis = analyze_individual_health(individual_data)
                
                # Generate individual report using ENROLLEE ID as filename
                from individual_report_generator import generate_individual_report
                # Clean enrollee ID for filename by replacing special characters
                clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                output_path = f"reports/{clean_enrollee_id}.pdf"
                report_path = generate_individual_report(individual_data, analysis, output_path)
                print(f"Individual report generated successfully! Path: {report_path}")
                
            except Exception as e:
                print(f"An error occurred: {e}")
        
        elif choice == '3':
            print("Thank you for using Clearline HMO Health Screening Report Generator!")
            break
        
        # Ask if user wants to continue
        continue_choice = input("\nWould you like to generate another report? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            print("Thank you for using Clearline HMO Health Screening Report Generator!")
            break