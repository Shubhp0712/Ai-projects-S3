# Email Configuration Setup for hello-py.py

## Quick Setup Instructions

To enable email functionality, edit the email configuration in hello-py.py around lines 33-38:

```python
# Email Configuration - Set your fixed email credentials here
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587
DEFAULT_FROM_EMAIL = "your.sender@gmail.com"      # Replace with your sender email
DEFAULT_TO_EMAIL = "your.receiver@gmail.com"      # Replace with your receiver email  
DEFAULT_EMAIL_PASSWORD = "your_app_password"      # Replace with your app password
```

## Configuration Steps:

### 1. Update DEFAULT_FROM_EMAIL
Replace `"your.sender@gmail.com"` with your actual Gmail address:
```python
DEFAULT_FROM_EMAIL = "mithi.automation@gmail.com"  # Example
```

### 2. Update DEFAULT_TO_EMAIL 
Replace `"your.receiver@gmail.com"` with the recipient email:
```python
DEFAULT_TO_EMAIL = "reports@company.com"  # Example
```

### 3. Update DEFAULT_EMAIL_PASSWORD
Replace `"your_app_password"` with your Gmail app password:
```python
DEFAULT_EMAIL_PASSWORD = "abcd efgh ijkl mnop"  # 16-character app password
```

## What Happens After Configuration:

1. **When script runs**: It will show `📧 Email service configured: sender@gmail.com -> receiver@gmail.com`
2. **During execution**: Terminal output is captured for email inclusion
3. **After XML generation**: Email is automatically sent with:
   - Test execution summary (pass/fail counts, success rate)
   - Terminal output (last 2000 characters)
   - Complete XML report as attachment
4. **Success confirmation**: `📧 Test report emailed successfully!` message

## Email Content Will Include:
- **Subject**: "Test Automation Report - [Project Name]"
- **Body**: Test summary + terminal output
- **Attachment**: Complete XML report file

## Gmail App Password Setup:
1. Enable 2-factor authentication on Gmail
2. Go to Google Account → Security → App passwords
3. Generate app password for "Mail"
4. Use the 16-character password (format: `xxxx xxxx xxxx xxxx`)

## Usage After Setup:
Simply run your normal command:
```bash
python hello-py.py .
```

The email will be sent automatically when the XML report is generated!

## If Email is Not Configured:
- Script shows: `📧 Email service disabled (update email configuration in script)`
- All other functionality works normally
- No emails are sent