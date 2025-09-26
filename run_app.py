#!/usr/bin/env python3
"""
Run script for the Clearline HMO Health Screening Streamlit App
"""

import subprocess
import sys
import os 

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_streamlit.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}") 
        return False
    return True

def run_streamlit_app():
    """Run the Streamlit app"""
    print("Starting Streamlit app...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_health_app.py"])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error running app: {e}")

if __name__ == "__main__":
    print("🏥 Clearline HMO Health Screening Report Generator")
    print("=" * 50)
    
    # Check if requirements are installed
    try:
        import streamlit
        import pandas
        import reportlab
        import requests
        print("✅ All required packages are available")
    except ImportError:
        print("📦 Installing required packages...")
        if not install_requirements():
            print("❌ Failed to install requirements. Please install manually:")
            print("pip install -r requirements_streamlit.txt")
            sys.exit(1)
    
    # Run the app
    run_streamlit_app()

# JZFaZSCZJKAv
