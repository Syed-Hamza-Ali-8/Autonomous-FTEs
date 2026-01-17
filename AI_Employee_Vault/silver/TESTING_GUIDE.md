# Testing Gmail, WhatsApp, and LinkedIn - Quick Guide

## Overview

This guide will help you test all three communication integrations:
- 📧 Gmail (email sending)
- 💬 WhatsApp (messaging)
- 🔗 LinkedIn (posting)

## Quick Start

```bash
# Run the comprehensive test
python3 silver/scripts/test_all_integrations.py
```

The script will test each integration interactively, asking for confirmation before taking any real actions.

---

## What Each Test Does

### 1️⃣ LinkedIn Test

**What it tests:**
- LinkedIn session is valid
- Browser automation works
- Post submission flow is correct

**What happens:**
- Opens browser (visible)
- Navigates to LinkedIn
- Creates a test post
- Submits the post
- Verifies success

**Expected time:** 10-15 seconds

**Verification:** Check your LinkedIn profile to see the test post

### 2️⃣ WhatsApp Test

**What it tests:**
- WhatsApp Web session is valid
- Browser automation works
- Message sending is functional

**What happens:**
- Opens browser (visible)
- Navigates to WhatsApp Web
- Finds the contact/number you specify
- Sends a test message
- Verifies success

**Expected time:** 10-15 seconds

**Verification:** Check WhatsApp to see the test message

### 3️⃣ Gmail Test

**What it tests:**
- Gmail API credentials are valid
- OAuth authentication works
- Email sending is functional

**What happens:**
- Authenticates with Gmail API
- Sends a test email to the address you specify
- Returns message ID
- Verifies success

**Expected time:** 2-5 seconds

**Verification:** Check the recipient's inbox

---

## Prerequisites

### LinkedIn ✅ (Already Set Up)

You already have a LinkedIn session at:
```
silver/config/linkedin_session/
```

**Status:** ✅ Ready to test

### WhatsApp ✅ (Already Set Up)

You already have a WhatsApp session at:
```
silver/config/whatsapp_session/
```

**Status:** ✅ Ready to test

### Gmail ❌ (Needs Setup)

**Status:** ⚠️ Requires Gmail API setup

**To set up Gmail:**

1. **Install Google API client:**
   ```bash
   pip install google-auth google-api-python-client
   ```

2. **Get Gmail API credentials:**
   - Go to: https://console.cloud.google.com/
   - Create a new project (or select existing)
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download `credentials.json`

3. **Run setup script:**
   ```bash
   python3 silver/scripts/setup_gmail.py
   ```

4. **Follow the prompts:**
   - Browser will open for Google authentication
   - Grant permissions to your app
   - Token will be saved automatically

**Quick guide:** https://developers.google.com/gmail/api/quickstart/python

---

## Running the Tests

### Option 1: Test All (Recommended)

```bash
python3 silver/scripts/test_all_integrations.py
```

**What happens:**
1. Tests LinkedIn (asks for confirmation)
2. Tests WhatsApp (asks for confirmation)
3. Tests Gmail (asks for confirmation)
4. Shows summary of results

**Interactive:** You'll be asked to confirm before each test

### Option 2: Test Individually

**LinkedIn only:**
```bash
python3 silver/scripts/test_linkedin_correct_flow.py
```

**WhatsApp only:**
```bash
# Create a quick test script
python3 -c "
from silver.src.actions.whatsapp_sender import WhatsAppSender
sender = WhatsAppSender('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
result = sender.send_message(
    to='YOUR_CONTACT_NAME',
    message='Test from AI Employee',
    headless=False
)
print(result)
"
```

**Gmail only:**
```bash
python3 silver/scripts/test_email.py --live
```

---

## Expected Output

### Successful Test

```
🧪 COMPREHENSIVE INTEGRATION TEST
======================================================================

1️⃣  TESTING LINKEDIN POSTING
======================================================================

✅ LinkedIn session found

📝 Test content:
🧪 Testing LinkedIn automation from AI Employee system!
...

⚠️  This will post to your LinkedIn profile!
Continue with LinkedIn test? (yes/no): yes

Posting to LinkedIn...
(Browser will open - this may take 10-15 seconds)

✅ LinkedIn post successful!
   Timestamp: 2026-01-17T15:00:00

🔍 Verify: Check your LinkedIn profile to see the post

Press Enter to continue to WhatsApp test...

2️⃣  TESTING WHATSAPP MESSAGING
======================================================================

✅ WhatsApp session found

Enter test recipient:
  - Phone number (e.g., +1234567890)
  - Or contact name (e.g., 'John Doe')

Recipient: John Doe

📝 Test message:
🧪 Test message from AI Employee system
...

⚠️  This will send a WhatsApp message to: John Doe
Continue with WhatsApp test? (yes/no): yes

Sending WhatsApp message...
(Browser will open - this may take 10-15 seconds)

✅ WhatsApp message sent successfully!
   Timestamp: 2026-01-17T15:01:00

🔍 Verify: Check WhatsApp to see the message

Press Enter to continue to Gmail test...

3️⃣  TESTING GMAIL SENDING
======================================================================

✅ Gmail credentials found
✅ Gmail API available

Enter recipient email address: test@example.com

📧 Test email:
   To: test@example.com
   Subject: Test Email from AI Employee
   Body: Hello!...

⚠️  This will send a real email to: test@example.com
Continue with Gmail test? (yes/no): yes

Sending email...

✅ Email sent successfully!
   Message ID: <abc123@mail.gmail.com>
   Timestamp: 2026-01-17T15:02:00

🔍 Verify: Check the recipient's inbox

======================================================================
📊 TEST SUMMARY
======================================================================

LinkedIn:  ✅ PASSED
WhatsApp:  ✅ PASSED
Gmail:     ✅ PASSED

Total: 3 passed, 0 failed, 0 skipped

✅ All tested integrations are working!
```

### If Gmail Not Set Up

```
3️⃣  TESTING GMAIL SENDING
======================================================================

❌ Gmail credentials not found

Setup required:
  1. Go to: https://console.cloud.google.com/
  2. Create a project and enable Gmail API
  3. Download credentials.json
  4. Run: python3 silver/scripts/setup_gmail.py

📚 Full guide: https://developers.google.com/gmail/api/quickstart

======================================================================
📊 TEST SUMMARY
======================================================================

LinkedIn:  ✅ PASSED
WhatsApp:  ✅ PASSED
Gmail:     ⏭️  SKIPPED

Total: 2 passed, 0 failed, 1 skipped
```

---

## Troubleshooting

### LinkedIn Issues

**Problem:** "Session expired" or "Not logged in"

**Solution:**
```bash
# Re-authenticate
python3 silver/scripts/setup_linkedin.py
```

**Problem:** "Modal still open - post did NOT submit"

**Solution:** This is the issue we fixed. Make sure you're using the updated code with the Done→Post flow.

### WhatsApp Issues

**Problem:** "Session expired" or "Not logged in"

**Solution:**
```bash
# Re-authenticate
python3 silver/scripts/setup_whatsapp.py
```

**Problem:** "Contact not found"

**Solution:**
- Use exact contact name as it appears in WhatsApp (including emojis!)
  - Example: If your contact is "Mr Honey 😎", you must include the emoji
- Or use phone number with country code: +1234567890
- Run the debug script to see available contacts: `python3 silver/scripts/test_whatsapp_debug.py`

### Gmail Issues

**Problem:** "Gmail credentials not found"

**Solution:** Follow the Gmail setup steps above

**Problem:** "Invalid credentials" or "Token expired"

**Solution:**
```bash
# Delete old token and re-authenticate
rm silver/config/gmail_token.json
python3 silver/scripts/setup_gmail.py
```

**Problem:** "API not enabled"

**Solution:**
- Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com
- Click "Enable"

---

## Safety Notes

⚠️ **Important:**

1. **LinkedIn:** Use a test/fake account to avoid ToS violations
2. **WhatsApp:** Test with your own number or a friend who knows you're testing
3. **Gmail:** Test with your own email or a test account
4. **Rate Limits:** Don't run tests too frequently (max once per hour)

---

## What Happens After Tests Pass

Once all tests pass, your AI Employee can:

1. **Automatically send emails** when approved via HITL
2. **Automatically post to LinkedIn** when approved via HITL
3. **Automatically send WhatsApp messages** when approved via HITL

All actions will go through the approval workflow:
```
Action Needed → Approval Request → User Approves → Action Executes
```

---

## Next Steps After Testing

### If All Tests Pass ✅

1. **Start the approval checker:**
   ```bash
   python3 -m silver.src.approval.approval_checker
   ```

2. **Create a test approval request:**
   ```python
   from silver.src.approval.approval_manager import ApprovalManager

   manager = ApprovalManager(vault_path, config_path)

   # Test LinkedIn post approval
   manager.create_approval_request(
       action_type="post_linkedin",
       action_details={
           "content": "Real post from AI Employee!",
           "external_recipient": True,
           "reversible": False,
       }
   )
   ```

3. **Approve it in Obsidian:**
   - Open `Pending_Approval/approval_*.md`
   - Change `status: pending` to `status: approved`
   - Save
   - Watch it execute automatically!

### If Some Tests Fail ⚠️

1. **LinkedIn fails:** Re-run setup, check session
2. **WhatsApp fails:** Re-run setup, check session
3. **Gmail fails:** Complete Gmail API setup

---

## Summary

**Current Status:**
- LinkedIn: ✅ Session exists, ready to test
- WhatsApp: ✅ Session exists, ready to test
- Gmail: ⚠️ Needs API setup

**To test everything:**
```bash
python3 silver/scripts/test_all_integrations.py
```

**Expected time:** 5-10 minutes (including confirmations)

**What you'll verify:**
- All three integrations work
- Browser automation is functional
- Sessions are valid
- Actions execute successfully

---

Ready to test? Run:
```bash
python3 silver/scripts/test_all_integrations.py
```
