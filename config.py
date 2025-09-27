#!/usr/bin/env python3
"""
Configuration file for MotherDuck integration
"""

import os

# MotherDuck Configuration
MOTHERDUCK_TOKEN = os.environ.get('MOTHERDUCK_TOKEN')

if not MOTHERDUCK_TOKEN:
    print("⚠️  WARNING: MOTHERDUCK_TOKEN not found in environment variables")
    print("Please set your MotherDuck token:")
    print("export MOTHERDUCK_TOKEN='your_token_here'")
    print("Or get one from: https://motherduck.com/")

# Database Configuration
DATABASE_URL = f"md:health_screening?motherduck_token={MOTHERDUCK_TOKEN}"

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

# Application Configuration
REPORTS_FOLDER = 'reports'
CUSTOMER_DATA_FILE = 'customers.csv'
UPLOAD_FOLDER = 'uploads'
LOG_FILE = 'portal_access.log'
