#!/usr/bin/env python3
"""
Script to upload customer data and reports to cloud platforms
"""

import os
import pandas as pd
import base64
import requests
import json

def upload_to_heroku():
    """Upload data to Heroku using Heroku CLI"""
    print("🚀 Uploading data to Heroku...")
    
    # Upload customers.csv
    print("📊 Uploading customers.csv...")
    os.system("heroku run 'python -c \"import pandas as pd; print(\\\"Customers data ready\\\")\"'")
    
    # Upload reports (this would need to be done manually or via a more complex script)
    print("📁 Reports need to be uploaded manually to the reports/ folder")
    print("   You can use: heroku run bash")
    print("   Then: mkdir -p reports && exit")
    print("   Then upload files via Heroku dashboard or git")

def create_upload_package():
    """Create a package for easy upload"""
    print("📦 Creating upload package...")
    
    # Create upload directory
    upload_dir = "upload_package"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Copy necessary files
    files_to_copy = [
        "customers.csv",
        "medical_portal_production.py",
        "requirements.txt",
        "Procfile",
        "runtime.txt",
        ".gitignore"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            os.system(f"cp {file} {upload_dir}/")
            print(f"✅ Copied {file}")
        else:
            print(f"⚠️  {file} not found")
    
    # Copy templates directory
    if os.path.exists("templates"):
        os.system(f"cp -r templates {upload_dir}/")
        print("✅ Copied templates/")
    
    # Copy reports directory
    if os.path.exists("reports"):
        os.system(f"cp -r reports {upload_dir}/")
        print("✅ Copied reports/")
    
    print(f"\n📦 Upload package created in: {upload_dir}/")
    print("You can now upload this folder to your cloud platform!")

def create_github_repo_instructions():
    """Create instructions for GitHub setup"""
    instructions = """
# GitHub Repository Setup Instructions

## 1. Create New Repository
1. Go to https://github.com/new
2. Repository name: `medical-portal`
3. Description: `Clearline HMO Medical Report Portal`
4. Make it Public or Private (your choice)
5. Don't initialize with README (we have files already)

## 2. Upload Files
1. Clone the repository locally:
   ```bash
   git clone https://github.com/yourusername/medical-portal.git
   cd medical-portal
   ```

2. Copy all files from this project to the repository folder

3. Commit and push:
   ```bash
   git add .
   git commit -m "Initial commit - Medical Report Portal"
   git push origin main
   ```

## 3. Required Files Checklist
- [ ] medical_portal_production.py
- [ ] requirements.txt
- [ ] Procfile
- [ ] runtime.txt
- [ ] .gitignore
- [ ] customers.csv
- [ ] reports/ folder (with PDF files)
- [ ] templates/ folder (with HTML files)

## 4. Deploy to Cloud Platform
Choose one of these platforms:
- **Heroku:** https://devcenter.heroku.com/articles/getting-started-with-python
- **Railway:** https://railway.app
- **Render:** https://render.com
- **DigitalOcean:** https://docs.digitalocean.com/products/app-platform/

## 5. Environment Variables
Set these in your cloud platform:
- SECRET_KEY=your-secret-key-here
- ADMIN_PASSWORD=your-admin-password
- LOG_LEVEL=INFO

## 6. Test Your Deployment
1. Visit your deployed URL
2. Test customer login
3. Test report download
4. Check admin stats

## 7. Share with Customers
Send the portal URL to your customers with their credentials!
"""
    
    with open("GITHUB_SETUP.md", "w") as f:
        f.write(instructions)
    
    print("📝 Created GITHUB_SETUP.md with detailed instructions")

def main():
    """Main function"""
    print("🏥 Medical Report Portal - Data Upload Helper")
    print("=" * 50)
    
    print("\nChoose an option:")
    print("1. Create upload package for manual upload")
    print("2. Create GitHub setup instructions")
    print("3. Show deployment options")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        create_upload_package()
    elif choice == "2":
        create_github_repo_instructions()
    elif choice == "3":
        print_deployment_options()
    else:
        print("Invalid choice. Please run the script again.")

def print_deployment_options():
    """Print deployment options"""
    print("\n🚀 Deployment Options:")
    print("=" * 30)
    
    print("\n1. Heroku (Recommended for beginners)")
    print("   - Free tier: 550 hours/month")
    print("   - Paid: $7/month")
    print("   - Setup time: 10 minutes")
    print("   - URL: https://devcenter.heroku.com")
    
    print("\n2. Railway")
    print("   - Cost: $5/month")
    print("   - Setup time: 5 minutes")
    print("   - URL: https://railway.app")
    
    print("\n3. Render")
    print("   - Free tier: 750 hours/month")
    print("   - Paid: $7/month")
    print("   - Setup time: 10 minutes")
    print("   - URL: https://render.com")
    
    print("\n4. DigitalOcean App Platform")
    print("   - Cost: $5/month")
    print("   - Setup time: 15 minutes")
    print("   - URL: https://cloud.digitalocean.com")
    
    print("\n📋 What you need to upload:")
    print("- customers.csv (your customer data)")
    print("- reports/ folder (all PDF reports)")
    print("- All Python files and templates")
    
    print("\n🔗 After deployment, you'll get a URL like:")
    print("- https://your-app.herokuapp.com")
    print("- https://your-app.railway.app")
    print("- https://your-app.onrender.com")

if __name__ == "__main__":
    main()
