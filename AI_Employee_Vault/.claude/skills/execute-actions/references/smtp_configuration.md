# SMTP Configuration Guide

## Overview

This guide covers SMTP configuration for the MCP email server, including setup for popular email providers.

## Gmail Configuration

### Prerequisites

- Gmail account
- 2-Factor Authentication enabled
- App Password generated

### Step 1: Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Follow the setup wizard

### Step 2: Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (Custom name)"
3. Enter "AI Employee Vault"
4. Click "Generate"
5. Copy the 16-character password

### Step 3: Configure .env

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App Password (remove spaces)
```

### Gmail Limits

- **Free tier**: 500 emails per day
- **Google Workspace**: 2,000 emails per day
- **Rate limit**: ~100 emails per hour recommended

### Troubleshooting Gmail

**Error: 535 Authentication Failed**
- Solution: Use App Password, not regular password
- Verify 2FA is enabled

**Error: 550 Recipient Rejected**
- Solution: Verify recipient email address
- Check if recipient has blocked you

**Error: 421 Service Not Available**
- Solution: You've hit rate limit, wait 1 hour
- Reduce sending frequency

## Outlook/Hotmail Configuration

### Prerequisites

- Outlook.com or Hotmail account
- No 2FA required (but recommended)

### Configuration

```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Outlook Limits

- **Free tier**: 300 emails per day
- **Rate limit**: ~100 emails per hour

### Troubleshooting Outlook

**Error: 535 Authentication Failed**
- Solution: Check username/password
- Disable "Less secure app access" if enabled

**Error: 554 Transaction Failed**
- Solution: Your account may be flagged for spam
- Contact Outlook support

## SendGrid Configuration

### Prerequisites

- SendGrid account (free tier available)
- API key generated

### Step 1: Create API Key

1. Go to [SendGrid API Keys](https://app.sendgrid.com/settings/api_keys)
2. Click "Create API Key"
3. Select "Full Access" or "Mail Send" only
4. Copy the API key

### Step 2: Configure .env

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=apikey  # Literal string "apikey"
SMTP_PASSWORD=SG.abc123xyz...  # Your API key
```

### SendGrid Limits

- **Free tier**: 100 emails per day
- **Essentials**: 40,000 emails per month ($19.95/month)
- **Pro**: 100,000 emails per month ($89.95/month)

### Troubleshooting SendGrid

**Error: 535 Authentication Failed**
- Solution: Verify API key is correct
- Username must be literal string "apikey"

**Error: 550 Recipient Rejected**
- Solution: Verify sender email is verified in SendGrid
- Add sender in SendGrid dashboard

## Mailgun Configuration

### Prerequisites

- Mailgun account (free tier available)
- Domain verified (or use sandbox domain)

### Configuration

```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-smtp-password
```

### Mailgun Limits

- **Free tier**: 5,000 emails per month (first 3 months)
- **Foundation**: $35/month for 50,000 emails

## Custom SMTP Server

### Configuration

```bash
SMTP_HOST=smtp.your-domain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_SECURE=false  # true for port 465
SMTP_USER=your-username
SMTP_PASSWORD=your-password
```

### Common Ports

- **25**: Unencrypted (not recommended)
- **465**: SSL/TLS (SMTP_SECURE=true)
- **587**: STARTTLS (SMTP_SECURE=false, recommended)
- **2525**: Alternative to 587 (some providers)

## Testing SMTP Connection

### Python Test Script

```python
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def test_smtp_connection():
    """Test SMTP connection and send test email."""
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(
            os.getenv('SMTP_HOST'),
            int(os.getenv('SMTP_PORT'))
        )
        server.starttls()

        # Login
        server.login(
            os.getenv('SMTP_USER'),
            os.getenv('SMTP_PASSWORD')
        )

        # Send test email
        msg = MIMEText('Test email from AI Employee Vault')
        msg['Subject'] = 'SMTP Test'
        msg['From'] = os.getenv('SMTP_USER')
        msg['To'] = os.getenv('SMTP_USER')  # Send to self

        server.send_message(msg)
        server.quit()

        print("✅ SMTP connection successful!")
        print(f"✅ Test email sent to {os.getenv('SMTP_USER')}")

    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")

if __name__ == '__main__':
    test_smtp_connection()
```

### Node.js Test Script

```javascript
const nodemailer = require('nodemailer');
require('dotenv').config();

async function testSMTP() {
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: process.env.SMTP_PORT,
    secure: process.env.SMTP_SECURE === 'true',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASSWORD
    }
  });

  try {
    // Verify connection
    await transporter.verify();
    console.log('✅ SMTP connection successful!');

    // Send test email
    const info = await transporter.sendMail({
      from: process.env.SMTP_USER,
      to: process.env.SMTP_USER,
      subject: 'SMTP Test',
      text: 'Test email from AI Employee Vault'
    });

    console.log(`✅ Test email sent: ${info.messageId}`);
  } catch (error) {
    console.error(`❌ SMTP connection failed: ${error.message}`);
  }
}

testSMTP();
```

## Security Best Practices

### 1. Use App Passwords

For Gmail and other providers that support it, always use App Passwords instead of regular passwords.

### 2. Store Credentials Securely

```bash
# .env file (gitignored)
SMTP_PASSWORD=your-password

# Never commit credentials to git
echo ".env" >> .gitignore
```

### 3. Use TLS/SSL

Always use encrypted connections:
- Port 587 with STARTTLS (recommended)
- Port 465 with SSL/TLS

### 4. Rotate Credentials Regularly

- Change SMTP passwords every 90 days
- Regenerate API keys quarterly
- Revoke unused credentials immediately

### 5. Limit Permissions

- Use API keys with minimal permissions (Mail Send only)
- Don't use admin accounts for SMTP

## Monitoring

### Check SMTP Health

```bash
# Test SMTP connection
python silver/scripts/test_smtp.py

# Check MCP server logs
tail -f silver/mcp/email-server/logs/smtp.log
```

### Monitor Sending Limits

Track daily email count to avoid hitting limits:

```python
def check_daily_limit():
    """Check if approaching daily email limit."""
    today = datetime.now().date()
    count = get_email_count_for_date(today)

    if count > 400:  # 80% of Gmail's 500/day limit
        print(f"⚠️  Warning: {count}/500 emails sent today")
```

## Troubleshooting

### Common Issues

1. **Authentication Failed (535)**
   - Check username/password
   - Use App Password for Gmail
   - Verify 2FA is enabled

2. **Connection Timeout (ETIMEDOUT)**
   - Check firewall settings
   - Verify SMTP port is correct
   - Check if ISP blocks SMTP ports

3. **Connection Refused (ECONNREFUSED)**
   - SMTP server may be down
   - Check SMTP_HOST is correct
   - Verify port is open

4. **TLS Error**
   - Update Node.js/Python to latest version
   - Check SSL certificate is valid
   - Try different port (587 vs 465)

### Debug Mode

Enable debug logging in Nodemailer:

```javascript
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASSWORD
  },
  debug: true,  // Enable debug output
  logger: true  // Log to console
});
```

## References

- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [Outlook SMTP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353)
- [SendGrid SMTP Documentation](https://docs.sendgrid.com/for-developers/sending-email/integrating-with-the-smtp-api)
- [Mailgun SMTP Documentation](https://documentation.mailgun.com/en/latest/user_manual.html#sending-via-smtp)
- [Nodemailer Documentation](https://nodemailer.com/smtp/)
