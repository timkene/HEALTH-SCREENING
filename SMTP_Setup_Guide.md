# SMTP Setup Guide for Health Screening App

## 🚀 Quick Setup for PDF Attachments

The SMTP method allows you to send individual health reports as PDF attachments via email. Here's how to set it up:

## 📧 Zoho Mail SMTP Configuration

### Step 1: Generate App Password
1. **Log into your Zoho Mail account** (hello@clearlinehmo.com)
2. **Go to Settings** → **Security** → **App Passwords**
3. **Click "Generate New Password"**
4. **Enter a name** (e.g., "Health Screening App")
5. **Copy the generated password** (format: `abcd efgh ijkl mnop`)

### Step 2: Configure in the App
1. **Open the Streamlit app**
2. **Go to "Bulk Email Reports"**
3. **Select "SMTP (With PDF attachments)"**
4. **Paste your App Password** (remove spaces)
5. **Test the connection**

## ⚙️ SMTP Settings

- **Server:** `smtp.zoho.com`
- **Port:** `587`
- **Security:** `TLS`
- **Username:** `hello@clearlinehmo.com`
- **Password:** `[Your App Password]`

## 🔧 Troubleshooting

### Common Issues:
1. **"Authentication failed"** → Check your App Password
2. **"Connection refused"** → Check internet connection
3. **"SMTP Error"** → Verify SMTP settings

### Solutions:
- ✅ Use App Password, NOT regular password
- ✅ Remove spaces from App Password
- ✅ Ensure 2FA is enabled on Zoho account
- ✅ Check firewall settings

## 📋 Testing

1. **Test SMTP Connection** - Verifies login
2. **Test Email with Attachment** - Sends test PDF to leocasey0@gmail.com

## 🎯 Benefits of SMTP Method

- ✅ **PDF Attachments** - Real PDF files attached to emails
- ✅ **Reliable** - Standard email protocol
- ✅ **Professional** - Recipients get actual reports
- ✅ **No API Limits** - Standard email sending

## 🔒 Security Notes

- App Passwords are safer than regular passwords
- Can be revoked anytime from Zoho settings
- Specific to this application only
- Never share your App Password

---

**Need Help?** Contact the development team or check Zoho Mail documentation.
