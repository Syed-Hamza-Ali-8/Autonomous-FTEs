# 🚀 Quick Start Guide - AI Employee Vault

**Last Updated**: 2026-01-20

This guide will help you quickly test the AI Employee Vault application.

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.13+ (Gold Tier) or Python 3.14+ (Silver Tier)
- ✅ Git installed
- ✅ Terminal/Command line access
- ✅ WhatsApp account (for WhatsApp testing)
- ✅ LinkedIn account (for LinkedIn testing)

---

## 🥈 Silver Tier Testing

The Silver Tier includes LinkedIn posting and WhatsApp messaging automation using Playwright.

### Step 1: Activate Virtual Environment

```bash
source silver/.venv/bin/activate
```

**Note**: You should see `(silver)` prefix in your terminal prompt after activation.

---

### Step 2: Test WhatsApp Messaging

#### Option A: Send to Specific Contact/Number

```bash
python scripts/test_whatsapp_flexible.py "Receiver Name" "Your message"
```

**Examples**:

```bash
# Send to contact with emoji (use exact name as it appears in WhatsApp)
python scripts/test_whatsapp_flexible.py "Mr Honey 😎" "Hello from AI Employee!"

# Send to phone number
python scripts/test_whatsapp_flexible.py "+92 321 8267160" "Test message from automation"

# Send to group
python scripts/test_whatsapp_flexible.py "GIAIC FUTURE LEADER BOYS" "Group message"
```

**Important Notes**:
- ⚠️ Contact names must match **exactly** as they appear in WhatsApp (including emojis!)
- ⏱️ First run takes 30-180 seconds (WhatsApp Web loading messages)
- ⏱️ Subsequent runs take 30-60 seconds (faster with cached data)
- 🔍 Browser will stay open for 30 seconds after sending so you can verify

#### Option B: Quick Test with Default Values

```bash
python scripts/test_whatsapp_simple.py
```

**What it does**: Sends a test message to the hardcoded recipient in the script.

#### Find Available Contacts

If you're not sure about exact contact names:

```bash
python scripts/list_whatsapp_contacts_v2.py
```

**Output**: Lists all your WhatsApp contacts with exact names (including emojis).

---

### Step 3: Test LinkedIn Posting

```bash
python3 silver/scripts/test_linkedin_correct_flow.py
```

**What it does**:
- Generates professional business content
- Posts to your LinkedIn profile (or dry-run mode)
- Uses AI to create engaging posts with hashtags

**Options**:
```bash
# Dry-run mode (no actual posting)
python3 silver/scripts/test_linkedin_correct_flow.py --dry-run

# Actual posting (removes dry-run flag)
python3 silver/scripts/test_linkedin_correct_flow.py
```

---

## 🎯 Complete Testing Workflow

Here's a complete testing session from start to finish:

```bash
# 1. Navigate to project directory
cd /path/to/AI_Employee_Vault

# 2. Activate Silver Tier virtual environment
source silver/.venv/bin/activate

# 3. List WhatsApp contacts (to find exact names)
python scripts/list_whatsapp_contacts_v2.py

# 4. Send WhatsApp message
python scripts/test_whatsapp_flexible.py "Contact Name" "Your message"

# 5. Test LinkedIn posting (dry-run)
python3 silver/scripts/test_linkedin_correct_flow.py --dry-run

# 6. Deactivate virtual environment when done
deactivate
```

---

## 📊 Expected Results

### WhatsApp Test Success

```
======================================================================
WhatsApp Message Test - Flexible Version
======================================================================

Using provided arguments:
  Recipient: Mr Honey 😎
  Message: Hello from AI Employee!

1. Opening browser...
2. Going to WhatsApp Web...
3. Waiting for WhatsApp to load (smart wait for chat list)...
   ✅ Chat list loaded!
4. Searching for contact...
5. Looking for 'Mr Honey 😎'...
6. Sending message...

✅ Message sent successfully!

Check your WhatsApp to verify!
Keeping browser open for 30 seconds...

======================================================================
✅ WhatsApp test PASSED!
======================================================================
```

### LinkedIn Test Success

```
============================================================
LinkedIn Poster Test
============================================================

1️⃣  Initializing LinkedIn poster...
   ✅ LinkedIn poster initialized
   ✅ Session found at: silver/config/linkedin_session

2️⃣  Generating business content...
   ✅ Generated content for topic: digital transformation

------------------------------------------------------------
📊 Quick update on our digital transformation initiative:

✅ Streamlined communication workflows
✅ Reduced manual tasks by 70%
✅ Improved response times

Ready to transform your business operations? DM me to learn more!

#Automation #Efficiency #Sales
------------------------------------------------------------

🔍 DRY RUN MODE - No actual posting
   Content generated successfully!

============================================================
✅ Test completed successfully!
============================================================
```

---

## 🔧 Troubleshooting

### Problem: "Contact not found" (WhatsApp)

**Solution**: Contact name must match exactly, including emojis

```bash
# Find exact contact names
python scripts/list_whatsapp_contacts_v2.py
```

---

### Problem: "Timeout waiting for chat list" (WhatsApp)

**Solution**: WhatsApp is loading messages (can take up to 3 minutes on first load)

- ⏱️ First load: Wait 150-180 seconds
- ⏱️ Subsequent loads: Wait 30-60 seconds
- 🔄 If stuck: Reset session with `python scripts/reset_whatsapp_session.py`

---

### Problem: "QR code appears" (WhatsApp)

**Solution**: Session expired, need to re-authenticate

```bash
python scripts/setup_whatsapp.py
# Scan QR code with your phone
```

---

### Problem: "Module not found" or "Command not found"

**Solution**: Virtual environment not activated

```bash
# Make sure you're in the project directory
cd /path/to/AI_Employee_Vault

# Activate virtual environment
source silver/.venv/bin/activate

# You should see (silver) prefix in your terminal
```

---

### Problem: LinkedIn session expired

**Solution**: Re-authenticate

```bash
# Run the setup script to log in again
python3 silver/scripts/setup_linkedin.py
```

---

## 📁 Project Structure

```
AI_Employee_Vault/
├── silver/                          # Silver Tier (Playwright automation)
│   ├── .venv/                       # Virtual environment
│   ├── scripts/
│   │   ├── test_whatsapp_flexible.py    # WhatsApp test (with arguments)
│   │   ├── test_whatsapp_simple.py      # WhatsApp test (hardcoded)
│   │   ├── test_linkedin_correct_flow.py # LinkedIn test
│   │   ├── list_whatsapp_contacts_v2.py # List contacts
│   │   └── reset_whatsapp_session.py    # Reset WhatsApp session
│   ├── config/
│   │   ├── whatsapp_session/        # WhatsApp Web session data
│   │   └── linkedin_session/        # LinkedIn session data
│   └── SILVER_TIER_TEST_RESULTS_FINAL.md # Detailed test results
├── gold/                            # Gold Tier (MCP servers)
│   └── .venv/                       # Virtual environment (Python 3.13)
└── QUICKSTART.md                    # This file
```

---

## 🥇 Gold Tier Testing (Coming Soon)

The Gold Tier includes MCP servers for Odoo and Social Media integration.

```bash
# Activate Gold Tier virtual environment
source gold/.venv/bin/activate

# Test Odoo MCP server
# (Instructions will be added)

# Test Social Media MCP server
# (Instructions will be added)
```

---

## 📚 Additional Resources

### Silver Tier Documentation

- **`silver/WHATSAPP_USAGE_GUIDE.md`** - Complete WhatsApp automation guide
- **`silver/SILVER_TIER_TEST_RESULTS_FINAL.md`** - Detailed test results and metrics
- **`silver/WHATSAPP_LOADING_ISSUE.md`** - Troubleshooting guide
- **`silver/README.md`** - Silver Tier overview

### Gold Tier Documentation

- **`gold/README.md`** - Gold Tier overview
- **`gold/GOLD_TIER_TEST_RESULTS.md`** - Test results and Python 3.13 requirement

---

## 🎯 Quick Reference

### Silver Tier Commands

| Task | Command |
|------|---------|
| **Activate venv** | `source silver/.venv/bin/activate` |
| **WhatsApp (flexible)** | `python scripts/test_whatsapp_flexible.py "Name" "Message"` |
| **WhatsApp (simple)** | `python scripts/test_whatsapp_simple.py` |
| **LinkedIn** | `python3 silver/scripts/test_linkedin_correct_flow.py` |
| **List contacts** | `python scripts/list_whatsapp_contacts_v2.py` |
| **Reset WhatsApp** | `python scripts/reset_whatsapp_session.py` |
| **Deactivate venv** | `deactivate` |

---

## 💡 Tips for Demo/Testing

1. **Pre-load WhatsApp** before demo (takes 30-180 seconds on first load)
   ```bash
   python scripts/list_whatsapp_contacts_v2.py
   # Let it load, then close browser
   ```

2. **Use dry-run mode** for LinkedIn to avoid accidental posts
   ```bash
   python3 silver/scripts/test_linkedin_correct_flow.py --dry-run
   ```

3. **Keep browser visible** to show the automation in action
   - Both scripts open a visible browser window
   - Browser stays open for 30 seconds after completion

4. **Have contact list ready** to show available contacts
   ```bash
   python scripts/list_whatsapp_contacts_v2.py
   ```

---

## ✅ Success Checklist

Before your demo/presentation, verify:

- [ ] Virtual environment activates successfully
- [ ] WhatsApp Web loads and shows chat list
- [ ] Can send WhatsApp message to at least one contact
- [ ] LinkedIn session is authenticated
- [ ] LinkedIn content generation works
- [ ] All scripts complete without errors

---

## 🆘 Need Help?

If you encounter issues not covered in this guide:

1. Check the detailed documentation in `silver/` directory
2. Review error messages carefully
3. Ensure virtual environment is activated
4. Verify Python version: `python --version` or `python3 --version`
5. Check that all dependencies are installed

---

## 🎉 You're Ready!

You now have everything you need to test the AI Employee Vault Silver Tier automation.

**Happy Testing!** 🚀

---

*Last Updated: 2026-01-20*
*Silver Tier Status: ✅ Fully Working*
*Gold Tier Status: ✅ Fully Working*
