#!/usr/bin/env python3
"""
Script to generate customer CSV file for the medical report portal
from the existing Excel health screening data.
"""

import pandas as pd
import os
from datetime import datetime

def generate_customer_csv(excel_file_path, output_csv_path='customers.csv'):
    """
    Generate customer CSV file from Excel health screening data
    
    Args:
        excel_file_path (str): Path to the Excel file with health screening data
        output_csv_path (str): Path where to save the customer CSV file
    """
    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_file_path}")
        df = pd.read_excel(excel_file_path)
        
        # Check for required columns
        required_columns = ['ENROLLEE ID', 'NAME', 'EMAIL']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        # Create customer data
        customers_data = []
        
        for idx, row in df.iterrows():
            # Skip rows with missing essential data
            if pd.isna(row['ENROLLEE ID']) or pd.isna(row['NAME']) or pd.isna(row['EMAIL']):
                continue
            
            # Get enrollee ID and clean it for filename
            enrollee_id = str(row['ENROLLEE ID']).strip()
            clean_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # Get customer details
            name = str(row['NAME']).strip()
            email = str(row['EMAIL']).strip().lower()
            
            # Get phone number (use TEL NO if available, otherwise use a placeholder)
            phone = str(row.get('TEL NO', '')).strip() if 'TEL NO' in df.columns else 'Not Provided'
            if phone == 'nan' or phone == '':
                phone = 'Not Provided'
            
            # Create report filename (using the same naming convention as the main system)
            report_filename = f"{clean_id}.pdf"
            
            customers_data.append({
                'ID': enrollee_id,
                'Name': name,
                'Email': email,
                'Phone': phone,
                'ReportFileName': report_filename
            })
        
        # Create DataFrame and save to CSV
        customers_df = pd.DataFrame(customers_data)
        customers_df.to_csv(output_csv_path, index=False)
        
        print(f"✅ Successfully generated customer CSV: {output_csv_path}")
        print(f"📊 Total customers: {len(customers_data)}")
        print(f"📁 Report files should be named: {clean_id}.pdf (example)")
        
        # Show sample data
        print("\n📋 Sample customer data:")
        print(customers_df.head())
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating customer CSV: {str(e)}")
        return False

def main():
    """Main function to run the script"""
    print("🏥 Medical Report Portal - Customer CSV Generator")
    print("=" * 50)
    
    # Get Excel file path from user
    excel_file = input("Enter path to Excel file with health screening data: ").strip()
    
    if not excel_file:
        # Try to find Excel files in current directory
        excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
        if excel_files:
            print(f"Found Excel files: {excel_files}")
            excel_file = excel_files[0]
            print(f"Using: {excel_file}")
        else:
            print("❌ No Excel file specified and none found in current directory")
            return
    
    if not os.path.exists(excel_file):
        print(f"❌ File not found: {excel_file}")
        return
    
    # Generate CSV
    success = generate_customer_csv(excel_file)
    
    if success:
        print("\n🎉 Customer CSV generated successfully!")
        print("\n📝 Next steps:")
        print("1. Generate individual reports using the Streamlit app")
        print("2. Place the PDF reports in the 'reports/' folder")
        print("3. Start the Flask portal: python medical_portal.py")
        print("4. Share the portal link with customers")
    else:
        print("\n❌ Failed to generate customer CSV")

if __name__ == "__main__":
    main()
