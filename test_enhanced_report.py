#!/usr/bin/env python3
"""
Test script for the enhanced individual health screening report with PSA and graphics
"""

from HEALTH_SCREEN import get_individual_data, analyze_individual_health
from individual_report_generator import generate_individual_report

def test_enhanced_individual_report():
    """Test the enhanced individual report with PSA and graphics"""
    
    # Test with the same data
    file_path = 'TEST ARIK.xlsx'
    enrollee_id = 'CL/ARIK/797297/2024-A'
    
    try:
        print("Testing Enhanced Individual Health Screening Report")
        print("=" * 60)
        
        # Get individual data
        print(f"Fetching data for Enrollee ID: {enrollee_id}")
        individual_data = get_individual_data(file_path, enrollee_id)
        print(f"Found individual: {individual_data.get('NAME', 'Unknown')}")
        print(f"Age: {individual_data.get('AGE', 'Unknown')} | Gender: {individual_data.get('GENDER', 'Unknown')}")
        
        # Analyze health data
        print("Analyzing health parameters...")
        analysis = analyze_individual_health(individual_data)
        
        # Show available analyses
        available_tests = list(analysis.keys())
        print(f"Available health analyses: {', '.join(available_tests)}")
        
        # Check if PSA is included
        if 'psa' in analysis:
            psa_data = analysis['psa']
            print(f"PSA Test: {psa_data['result']} (Value: {psa_data['value']})")
        else:
            print("PSA Test: Not available (likely not a man over 40 or test not performed)")
        
        # Generate enhanced individual report
        clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        output_path = f"Enhanced_Individual_Report_{clean_enrollee_id}.pdf"
        print(f"Generating enhanced individual report: {output_path}")
        
        report_path = generate_individual_report(individual_data, analysis, output_path)
        print(f"✅ Enhanced individual report generated successfully: {report_path}")
        
        print("\n🎨 Report Features:")
        print("• Personalized health overview with visual status indicator")
        print("• BMI analysis with visual BMI scale")
        print("• Blood pressure analysis with visual pressure zones")
        print("• Educational content for all health parameters")
        print("• PSA analysis (if applicable)")
        print("• Creative graphics and visual elements")
        print("• Professional PDF formatting")
        
    except FileNotFoundError:
        print("❌ Error: Excel file not found. Please check the file path.")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_enhanced_individual_report()
