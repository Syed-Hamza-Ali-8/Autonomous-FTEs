# Keyword Filtering - Smart Message Prioritization

**Status**: ✅ Implemented
**Last Updated**: 2026-02-14

---

## 🎯 What Is Keyword Filtering?

Keyword filtering prevents message overload by only processing messages that contain priority keywords like "urgent", "fast", "important", etc.

**Problem it solves:**
- You have 133 unread WhatsApp messages
- Without filtering: 133 files in Needs_Action + 133 in Pending_Approval = folder chaos
- With filtering: Only messages with keywords like "urgent" or "help" are processed

**Result:** Your folders stay clean, and you only respond to priority messages.

---

## 🔧 How It Works

### WhatsApp Messages

When the daemon checks WhatsApp:
1. Finds all unread messages
2. Reads message text
3. Checks if text contains any priority keywords
4. **If keywords found:** Creates file in Needs_Action → AI generates reply
5. **If no keywords:** Skips message (stays unread in WhatsApp, no file created)

### Gmail Messages

When the daemon checks Gmail:
1. Finds all unread emails
2. Reads subject + body
3. Checks if either contains priority keywords
4. **If keywords found:** Creates file in Needs_Action → AI generates reply
5. **If no keywords:** Skips email (stays unread in Gmail, no file created)

---

## ⚙️ Configuration

### Location
`silver/config/watcher_config.yaml`

### WhatsApp Configuration

```yaml
whatsapp:
  keyword_filter:
    enabled: true  # Set to false to process ALL messages
    keywords:
      - "urgent"
      - "fast"
      - "important"
      - "asap"
      - "help"
      - "priority"
      - "emergency"
      - "critical"
      - "immediate"
      - "quick"
      - "now"
      - "please"
    case_sensitive: false  # Match keywords regardless of case
```

### Gmail Configuration

```yaml
gmail:
  keyword_filter:
    enabled: true  # Set to false to process ALL emails
    keywords:
      - "urgent"
      - "fast"
      - "important"
      - "asap"
      - "help"
      - "priority"
      - "emergency"
      - "critical"
      - "immediate"
      - "quick"
      - "now"
      - "please"
    case_sensitive: false  # Match keywords regardless of case
```

---

## 📝 Customizing Keywords

### Add Your Own Keywords

Edit `silver/config/watcher_config.yaml`:

```yaml
whatsapp:
  keyword_filter:
    enabled: true
    keywords:
      - "urgent"
      - "fast"
      - "client"      # Add custom keyword
      - "meeting"     # Add custom keyword
      - "deadline"    # Add custom keyword
      - "payment"     # Add custom keyword
```

### Case Sensitivity

**Case insensitive (default):**
```yaml
case_sensitive: false
```
- Matches: "URGENT", "urgent", "Urgent", "uRgEnT"

**Case sensitive:**
```yaml
case_sensitive: true
```
- Only matches exact case: "urgent" ≠ "URGENT"

---

## 🎮 Usage Examples

### Example 1: Client Sends Urgent Message

**WhatsApp message:**
```
Hey, I need help with the urgent project ASAP!
```

**Result:**
- ✅ Contains keywords: "help", "urgent", "ASAP"
- ✅ File created: `Needs_Action/msg_whatsapp_abc123.md`
- ✅ AI generates reply → `Pending_Approval/approval_20260214_123456_reply_whatsapp.md`
- ✅ You review and approve → Message sent

### Example 2: Friend Sends Casual Message

**WhatsApp message:**
```
Hey bro, what's up? Want to hang out this weekend?
```

**Result:**
- ❌ No keywords found
- ❌ No file created
- ❌ Message stays unread in WhatsApp
- ❌ No AI reply generated

### Example 3: Client Sends Email

**Email subject:** "Quick question about invoice"
**Email body:** "Can you please send me the invoice?"

**Result:**
- ✅ Contains keywords: "Quick", "please"
- ✅ File created: `Needs_Action/msg_gmail_def456.md`
- ✅ AI generates reply → `Pending_Approval/approval_20260214_123457_reply_email.md`
- ✅ You review and approve → Email sent

---

## 🔄 Enabling/Disabling Filtering

### Disable Filtering (Process ALL Messages)

Edit `silver/config/watcher_config.yaml`:

```yaml
whatsapp:
  keyword_filter:
    enabled: false  # Process all messages
```

**Result:** All 133 messages will be processed (not recommended!)

### Enable Filtering (Process Only Priority Messages)

```yaml
whatsapp:
  keyword_filter:
    enabled: true  # Only process messages with keywords
```

**Result:** Only messages with keywords are processed (recommended!)

---

## 📊 What Happens to Filtered Messages?

### Messages WITHOUT Keywords

**WhatsApp:**
- Stay unread in WhatsApp Web
- No file created in Needs_Action
- No AI reply generated
- You can manually check WhatsApp later

**Gmail:**
- Stay unread in Gmail inbox
- No file created in Needs_Action
- No AI reply generated
- You can manually check Gmail later

### Messages WITH Keywords

**WhatsApp:**
- File created in Needs_Action
- AI generates reply in Pending_Approval
- You review and approve
- System sends reply automatically

**Gmail:**
- File created in Needs_Action
- AI generates reply in Pending_Approval
- You review and approve
- System sends reply automatically

---

## 🎯 Recommended Keywords

### Business/Client Communication
```yaml
keywords:
  - "urgent"
  - "important"
  - "asap"
  - "priority"
  - "deadline"
  - "client"
  - "meeting"
  - "payment"
  - "invoice"
  - "contract"
```

### Support/Help Requests
```yaml
keywords:
  - "help"
  - "issue"
  - "problem"
  - "error"
  - "bug"
  - "broken"
  - "not working"
  - "emergency"
```

### Time-Sensitive
```yaml
keywords:
  - "urgent"
  - "fast"
  - "quick"
  - "asap"
  - "now"
  - "immediate"
  - "today"
  - "tonight"
```

---

## 🧪 Testing Keyword Filtering

### Test 1: Send Message WITH Keywords

1. Send yourself a WhatsApp message: "Hey, I need urgent help!"
2. Wait 30 seconds for daemon to check
3. Check `Needs_Action/` - file should appear
4. Check logs: "Message contains keyword: 'urgent'"

### Test 2: Send Message WITHOUT Keywords

1. Send yourself a WhatsApp message: "Hey, how are you?"
2. Wait 30 seconds for daemon to check
3. Check `Needs_Action/` - no file created
4. Check logs: "Skipping message from [name] - no priority keywords found"

### Test 3: Verify Filtering is Active

Check daemon logs:
```
✅ WhatsApp watcher initialized
   Keyword filtering enabled with 12 keywords
```

---

## 🔍 Troubleshooting

### All Messages Being Processed (Filtering Not Working)

**Check:**
1. Is filtering enabled in config?
   ```yaml
   keyword_filter:
     enabled: true  # Must be true
   ```

2. Restart daemon after config changes:
   ```bash
   # Stop daemon (Ctrl+C)
   # Start again
   python silver/scripts/run_daemon.py
   ```

3. Check logs for "Keyword filtering enabled"

### No Messages Being Processed

**Check:**
1. Are your keywords too restrictive?
2. Try adding more common keywords like "please", "thanks", "question"
3. Or temporarily disable filtering:
   ```yaml
   keyword_filter:
     enabled: false
   ```

### Case Sensitivity Issues

**Problem:** Keyword "urgent" not matching "URGENT"

**Solution:**
```yaml
case_sensitive: false  # Match any case
```

---

## 📈 Performance Impact

**Before Filtering (133 messages):**
- 133 files in Needs_Action
- 133 AI replies in Pending_Approval
- Folder chaos
- Overwhelming to review

**After Filtering (assume 10 urgent messages):**
- 10 files in Needs_Action
- 10 AI replies in Pending_Approval
- Clean folders
- Easy to review

**Processing time:**
- Filtering adds ~0.1 seconds per message
- Negligible impact on performance

---

## 🎉 Benefits

✅ **Clean Folders:** Only priority messages create files
✅ **Focus:** Review only important messages
✅ **Scalability:** Handle 100+ unread messages without chaos
✅ **Flexibility:** Customize keywords for your needs
✅ **Control:** Enable/disable anytime
✅ **Smart:** Checks both subject and body for emails

---

## 📚 Related Documentation

- **Main Guide:** `silver/24_7_AUTONOMOUS_SYSTEM.md`
- **Configuration:** `silver/config/watcher_config.yaml`
- **Implementation:** `silver/src/watchers/whatsapp_watcher.py`
- **Implementation:** `silver/src/watchers/gmail_watcher.py`

---

**Feature Status:** ✅ Production Ready
**Recommended:** Enable for high-volume message scenarios
**Default:** Enabled with 12 common priority keywords
