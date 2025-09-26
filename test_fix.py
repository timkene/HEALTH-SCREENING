#!/usr/bin/env python3
"""
Test script to verify the filename fix for special characters in Enrollee IDs
"""

from HEALTH_SCREEN import get_individual_data, analyze_individual_health
from individual_report_generator import generate_individual_report

def test_enrollee_id_fix():
    """Test the fix for special characters in Enrollee IDs"""
    
    # Test the filename cleaning logic
    enrollee_id = "CL/ARIK/797297/2024-A"
    clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    
    print(f"Original Enrollee ID: {enrollee_id}")
    print(f"Cleaned for filename: {clean_enrollee_id}")
    print(f"Output filename: Individual_Report_{clean_enrollee_id}.pdf")
    
    # Test with the actual Excel file
    file_path = 'TEST ARIK.xlsx'
    
    try:
        print(f"\nTesting with file: {file_path}")
        print(f"Looking for Enrollee ID: {enrollee_id}")
        
        # Get individual data
        individual_data = get_individual_data(file_path, enrollee_id)
        print(f"✅ Found individual: {individual_data.get('NAME', 'Unknown')}")
        
        # Analyze health data
        analysis = analyze_individual_health(individual_data)
        available_tests = list(analysis.keys())
        print(f"✅ Available health analyses: {', '.join(available_tests)}")
        
        # Generate individual report with cleaned filename
        output_path = f"Individual_Report_{clean_enrollee_id}.pdf"
        print(f"✅ Generating report: {output_path}")
        
        report_path = generate_individual_report(individual_data, analysis, output_path)
        print(f"✅ Individual report generated successfully: {report_path}")
        
    except FileNotFoundError:
        print(f"❌ Error: Excel file '{file_path}' not found.")
        print("Please make sure the file exists in the current directory.")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_enrollee_id_fix()
