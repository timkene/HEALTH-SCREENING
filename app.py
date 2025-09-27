#!/usr/bin/env python3
"""
Medical Report Portal - Main Application Entry Point
This file is the main entry point for Railway deployment
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_portal_production import app

if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Starting Medical Portal on port {port}")
    print(f"🌐 Access URL: http://0.0.0.0:{port}")
    
    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=port)
