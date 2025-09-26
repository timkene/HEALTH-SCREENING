#!/usr/bin/env python3
"""
Deployment script for the Medical Report Portal
Automates the setup process
"""

import os
import sys
import subprocess
import pandas as pd
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description} found: {file_path}")
        return True
    else:
        print(f"❌ {description} not found: {file_path}")
        return False

def setup_portal():
    """Main setup function"""
    print("🏥 Clearline HMO Medical Report Portal - Deployment Script")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    
    print(f"✅ Python version: {sys.version}")
    
    # Install requirements
    if not run_command("pip install -r requirements_portal.txt", "Installing requirements"):
        print("⚠️  Some packages may not have installed correctly")
    
    # Check for Excel file
    excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
    if not excel_files:
        print("❌ No Excel files found. Please place your health screening Excel file in this directory.")
        return False
    
    excel_file = excel_files[0]
    print(f"📊 Found Excel file: {excel_file}")
    
    # Generate customer CSV
    if not check_file_exists('customers.csv', 'Customer CSV file'):
        print("🔄 Generating customer CSV...")
        if not run_command(f"python generate_customer_csv.py", "Generating customer data"):
            return False
    
    # Check for reports folder
    if not os.path.exists('reports'):
        print("📁 Creating reports folder...")
        os.makedirs('reports', exist_ok=True)
    
    # Check for PDF reports
    if os.path.exists('reports'):
        pdf_files = [f for f in os.listdir('reports') if f.endswith('.pdf')]
        if len(pdf_files) == 0:
            print("⚠️  No PDF reports found in reports/ folder")
            print("   Please generate reports using the Streamlit app first:")
            print("   1. Run: streamlit run streamlit_health_app.py")
            print("   2. Go to 'Bulk Email Reports'")
            print("   3. Click 'Download All Reports'")
        else:
            print(f"✅ Found {len(pdf_files)} PDF reports")
    
    # Check for templates
    if not os.path.exists('templates'):
        print("❌ Templates folder not found. Please ensure all HTML templates are in the templates/ folder")
        return False
    
    template_files = ['base.html', 'index.html', 'verify.html', 'dashboard.html', 'error.html']
    missing_templates = [f for f in template_files if not os.path.exists(f'templates/{f}')]
    if missing_templates:
        print(f"❌ Missing templates: {missing_templates}")
        return False
    
    print("✅ All templates found")
    
    # Create startup script
    startup_script = """#!/bin/bash
# Medical Report Portal Startup Script

echo "🏥 Starting Clearline HMO Medical Report Portal..."

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install requirements if needed
pip install -r requirements_portal.txt

# Start the portal
echo "Starting portal on http://localhost:5000"
python medical_portal.py
"""
    
    with open('start_portal.sh', 'w') as f:
        f.write(startup_script)
    
    # Make it executable on Unix systems
    if os.name != 'nt':  # Not Windows
        os.chmod('start_portal.sh', 0o755)
    
    print("✅ Created startup script: start_portal.sh")
    
    # Final checks
    print("\n🔍 Final System Check:")
    print("=" * 30)
    
    checks = [
        ('customers.csv', 'Customer data file'),
        ('templates/', 'Templates folder'),
        ('reports/', 'Reports folder'),
        ('medical_portal.py', 'Main portal script'),
        ('generate_customer_csv.py', 'CSV generator script')
    ]
    
    all_good = True
    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_good = False
    
    if all_good:
        print("\n🎉 Portal setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Generate PDF reports using Streamlit app")
        print("2. Start the portal: python medical_portal.py")
        print("3. Access at: http://localhost:5000")
        print("4. Share the link with customers")
        
        print("\n🚀 Quick Start Commands:")
        print("   # Generate reports (if not done already)")
        print("   streamlit run streamlit_health_app.py")
        print("")
        print("   # Start portal")
        print("   python medical_portal.py")
        print("")
        print("   # Or use the startup script")
        if os.name != 'nt':
            print("   ./start_portal.sh")
        else:
            print("   start_portal.bat")
        
        return True
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        return False

def main():
    """Main function"""
    try:
        success = setup_portal()
        if success:
            print("\n✅ Deployment completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Deployment failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
