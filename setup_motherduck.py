#!/usr/bin/env python3
"""
Setup script for MotherDuck integration
This script helps you get started with MotherDuck database
"""

import os
import sys

def setup_motherduck():
    """Setup MotherDuck database and test connection"""
    
    print("🦆 MotherDuck Setup for Health Screening System")
    print("=" * 50)
    
    # Check for MotherDuck token
    token = os.environ.get('MOTHERDUCK_TOKEN')
    if not token:
        print("❌ MOTHERDUCK_TOKEN not found!")
        print("\n📋 To get started:")
        print("1. Go to https://motherduck.com/")
        print("2. Sign up for a free account")
        print("3. Get your API token")
        print("4. Set the environment variable:")
        print("   export MOTHERDUCK_TOKEN='your_token_here'")
        print("\nOr run this script with:")
        print("   MOTHERDUCK_TOKEN='your_token' python setup_motherduck.py")
        return False
    
    print(f"✅ Found MotherDuck token: {token[:10]}...")
    
    try:
        # Test database connection
        from database_config import get_db
        db = get_db()
        
        print("✅ Successfully connected to MotherDuck!")
        print("✅ Database tables created successfully!")
        
        # Test PDF storage
        from pdf_storage import get_pdf_storage
        pdf_storage = get_pdf_storage()
        print("✅ PDF storage system ready!")
        
        print("\n🎉 Setup complete! Your system is ready to use MotherDuck.")
        print("\n📝 Next steps:")
        print("1. Run HEALTH_SCREEN.py to upload Excel data")
        print("2. Generate reports (they'll be stored in MotherDuck)")
        print("3. Deploy medical_portal.py (it will read from MotherDuck)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up MotherDuck: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify your MotherDuck token is correct")
        print("3. Make sure you have the required packages installed:")
        print("   pip install duckdb motherduck")
        return False

if __name__ == "__main__":
    success = setup_motherduck()
    sys.exit(0 if success else 1)
