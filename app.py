#!/usr/bin/env python3
"""
Medical Report Portal - Main Application Entry Point
This file is the main entry point for Railway deployment
"""

import os
import sys
from medical_portal_production import app

if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5001))
    
    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=port)
