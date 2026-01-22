# WhatsApp Automation - Usage Guide

**Date**: 2026-01-20
**Status**: ✅ **Fully Working**

---

## 🎯 Quick Start

### For Testing/Demo (Recommended)

```bash
cd silver
source .venv/bin/activate

# Simple test with hardcoded values
python scripts/test_whatsapp_simple.py
```

### For Custom Messages

```bash
cd silver
source .venv/bin/activate

# Send custom message
python scripts/test_whatsapp_flexible.py "Mr Honey 😎" "Your custom message here"

# Use default message
python scripts/test_whatsapp_flexible.py "Mr Honey 😎"

# Use all defaults
python scripts/test_whatsapp_flexible.py
```

---

## 📋 Available Scripts

### 1. `test_whatsapp_simple.py` - Simple Test Script

**Purpose**: Quick testing with hardcoded recipient and message

**Usage**:
```bash
python scripts/test_whatsapp_simple.py
```

**Configuration**: Edit the file to change recipient/message:
```python
recipient = "Mr Honey 😎"  # Include emojis as they appear in WhatsApp!
message = "🧪 Test from AI Employee - WhatsApp working!"
```

**Best for**:
- Quick testing
- Hackathon demos
- Verifying WhatsApp is working

---

### 2. `test_whatsapp_flexible.py` - Flexible Test Script

**Purpose**: Send messages with command-line arguments

**Usage**:
```bash
# All defaults
python scripts/test_whatsapp_flexible.py

# Custom recipient
python scripts/test_whatsapp_flexible.py "Contact Name"

# Custom recipient and message
python scripts/test_whatsapp_flexible.py "Contact Name" "Your message"
```

**Examples**:
```bash
# Send to Mr Honey with custom message
python scripts/test_whatsapp_flexible.py "Mr Honey 😎" "Hello from automation!"

# Send to phone number
python scripts/test_whatsapp_flexible.py "+92 321 8267160" "Test message"

# Send to group
python scripts/test_whatsapp_flexible.py "GIAIC FUTURE LEADER BOYS" "Group message"
```

**Best for**:
- Automation
- Multiple recipients
- Integration with other systems
- Production use

---

### 3. `list_whatsapp_contacts_v2.py` - Contact Lister

**Purpose**: List all available WhatsApp contacts

**Usage**:
```bash
python scripts/list_whatsapp_contacts_v2.py
```

**Output**: Shows first 20 contacts with exact names (including emojis)

**Best for**:
- Finding exact contact names
- Discovering available contacts
- Debugging contact name issues

---

### 4. Production WhatsApp Sender (Advanced)

**Purpose**: Full-featured WhatsApp sender with error handling

**Usage**:
```python
from src.actions.whatsapp_sender import WhatsAppSender

sender = WhatsAppSender(vault_path="/path/to/vault")

result = sender.send_message(
    to="Mr Honey 😎",
    message="Hello from production script!",
    wait_for_delivery=True
)

if result['success']:
    print(f"Message sent! ID: {result['message_id']}")
else:
    print(f"Failed: {result['error']}")
```

**Best for**:
- Production deployments
- Error handling
- Delivery confirmation
- Integration with larger systems

---

## ⚠️ Important Notes

### 1. Contact Names Must Match Exactly

**Including Emojis!**

❌ Wrong:
```python
recipient = "Mr Honey"  # Missing emoji
```

✅ Correct:
```python
recipient = "Mr Honey 😎"  # Includes emoji as it appears in WhatsApp
```

**How to find exact names**:
```bash
python scripts/list_whatsapp_contacts_v2.py
```

---

### 2. WhatsApp Loading Time

WhatsApp Web takes **30-180 seconds** to load, depending on:
- Message history size
- Network speed
- Number of chats

**First load**: 150-180 seconds (downloading all messages)
**Subsequent loads**: 30-60 seconds (faster with cached data)

**Progress indicators**:
- 0% → Initial connection
- 28% → Authenticating
- 75% → Loading messages
- 100% → Ready to use

---

### 3. Session Management

**Session location**: `silver/config/whatsapp_session/`

**If WhatsApp gets stuck loading**:
```bash
# Reset session
python scripts/reset_whatsapp_session.py

# Re-authenticate
python scripts/setup_whatsapp.py
# Scan QR code with your phone
```

---

## 🔧 Troubleshooting

### Problem: "Contact not found"

**Solution**: Use exact contact name including emojis
```bash
# List all contacts to find exact name
python scripts/list_whatsapp_contacts_v2.py
```

---

### Problem: "Timeout waiting for chat list"

**Solution**: WhatsApp is still loading messages
- Wait longer (up to 3 minutes on first load)
- Or reset session if stuck at same percentage

---

### Problem: "ERR_ABORTED" or browser won't open

**Solution**: Another script is using the session
- Wait 10 seconds for previous script to close
- Or kill any running Chromium processes

---

### Problem: "QR code appears" (not logged in)

**Solution**: Session expired or cleared
```bash
python scripts/setup_whatsapp.py
# Scan QR code with your phone
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **First Load** | 150-180 seconds |
| **Subsequent Loads** | 30-60 seconds |
| **Message Send Time** | 2-3 seconds |
| **Contact Search** | 1-2 seconds |
| **Total Test Time** | 35-65 seconds (after initial load) |

---

## 🎯 Recommended Workflow

### For Hackathon Demo

1. **Pre-demo setup** (do this before presenting):
   ```bash
   # Open WhatsApp and let it fully load
   python scripts/list_whatsapp_contacts_v2.py
   # Wait for it to load, then close browser
   ```

2. **During demo**:
   ```bash
   # Quick test (will load faster since recently opened)
   python scripts/test_whatsapp_simple.py
   ```

3. **Show flexibility**:
   ```bash
   # Send custom message
   python scripts/test_whatsapp_flexible.py "Contact Name" "Custom message"
   ```

---

### For Production Use

1. **Use the production class**:
   ```python
   from src.actions.whatsapp_sender import WhatsAppSender
   ```

2. **Configure environment variables**:
   ```bash
   WHATSAPP_HEADLESS=true    # Run without visible browser
   WHATSAPP_TIMEOUT=30000    # 30 seconds timeout
   ```

3. **Implement error handling**:
   ```python
   result = sender.send_message(to=recipient, message=message)
   if not result['success']:
       # Handle error
       log_error(result['error'])
   ```

---

## ✅ Success Criteria

Your WhatsApp automation is working correctly if:

- [x] WhatsApp Web loads within 180 seconds
- [x] Chat list appears
- [x] Search box is visible
- [x] Contacts can be found by exact name
- [x] Messages send successfully
- [x] Browser closes cleanly after sending

---

## 🚀 Next Steps

1. **Test with different contacts**:
   ```bash
   python scripts/list_whatsapp_contacts_v2.py  # Get contact names
   python scripts/test_whatsapp_flexible.py "Contact Name" "Test message"
   ```

2. **Integrate with your workflow**:
   - Use production WhatsAppSender class
   - Add to your automation scripts
   - Set up scheduled messages

3. **Monitor and maintain**:
   - Check session validity periodically
   - Re-authenticate if QR code appears
   - Reset session if loading gets stuck

---

*Last Updated: 2026-01-20*
*Status: ✅ Fully Working*
*Load Time: 30-180 seconds*
*Key Learning: Contact names must include emojis exactly as they appear in WhatsApp*
