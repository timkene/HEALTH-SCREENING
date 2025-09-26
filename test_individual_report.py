#!/usr/bin/env python3
"""
Test script for the individual health screening report generator
This script demonstrates how to use the new individual report functionality
"""

from HEALTH_SCREEN import get_individual_data, analyze_individual_health
from individual_report_generator import generate_individual_report

def test_individual_report():
    """Test the individual report generation"""
    
    # Example usage - replace with your actual file path and enrollee ID
    file_path = 'VACCIPHARM.xlsx'  # Replace with your Excel file path
    enrollee_id = '12345'  # Replace with actual enrollee ID
    
    try:
        print("Testing Individual Health Screening Report Generator")
        print("=" * 60)
        
        # Get individual data
        print(f"Fetching data for Enrollee ID: {enrollee_id}")
        individual_data = get_individual_data(file_path, enrollee_id)
        print(f"Found individual: {individual_data.get('NAME', 'Unknown')}")
        
        # Analyze health data
        print("Analyzing health parameters...")
        analysis = analyze_individual_health(individual_data)
        
        # Show available analyses
        available_tests = list(analysis.keys())
        print(f"Available health analyses: {', '.join(available_tests)}")
        
        # Generate individual report
        output_path = f"Test_Individual_Report_{enrollee_id}.pdf"
        print(f"Generating individual report: {output_path}")
        
        report_path = generate_individual_report(individual_data, analysis, output_path)
        print(f"✅ Individual report generated successfully: {report_path}")
        
    except FileNotFoundError:
        print("❌ Error: Excel file not found. Please check the file path.")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_individual_report()
