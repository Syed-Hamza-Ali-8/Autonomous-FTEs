# Gmail Test Account Change Guide

**Purpose**: Change the Gmail account used for Silver Tier testing

**Time Required**: 10-15 minutes

---

## 📋 Prerequisites

- Access to Google Cloud Console
- New Gmail account ready for testing
- Current project OAuth credentials (Client ID and Secret)

---

## 🔄 Complete Process

### Step 1: Add New Test User in Google Cloud Console

1. **Open Google Cloud Console**:
   ```
   https://console.cloud.google.com/
   ```

2. **Navigate to OAuth Consent Screen**:
   - Click hamburger menu (☰) → **APIs & Services** → **OAuth consent screen**
   - Or direct link: https://console.cloud.google.com/apis/credentials/consent

3. **Add Test User**:
   - Scroll down to **Test users** section
   - Click **+ ADD USERS** button
   - Enter the new Gmail address (e.g., `newtestuser@gmail.com`)
   - Click **SAVE**

4. **Verify**:
   - New email should appear in the test users list
   - Status should show as "Active"

**Screenshot locations to verify**:
- Test users section shows your new email
- No error messages displayed

---

### Step 2: Clear Old Authentication Token

Run the reset script to clear the old refresh token:

```bash
# Navigate to vault root
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault

# Run reset script
python3 silver/scripts/reset_gmail_auth.py
```

**Expected Output**:
```
============================================================
Reset Gmail Authentication
============================================================

📋 Current status:
   .env file: /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver/config/.env

✅ Cleared GMAIL_REFRESH_TOKEN

✅ Gmail authentication reset complete!

Next steps:
   1. Add new test user in Google Cloud Console
   2. Run: python silver/scripts/setup_gmail.py
   3. Authenticate with the new Gmail account
```

---

### Step 3: Re-authenticate with New Account

Run the Gmail setup script:

```bash
# Make sure you're in the vault root
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault

# Activate venv (if using)
source silver/.venv/bin/activate

# Run setup script
python3 silver/scripts/setup_gmail.py
```

**Interactive Prompts**:

1. **Enter Client ID**:
   ```
   Client ID: 68776177581-dabflv882pkq7adj67gm30it5esp2g1g.apps.googleusercontent.com
   ```
   *(Use your existing Client ID from Google Cloud Console)*

2. **Enter Client Secret**:
   ```
   Client Secret: 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
   ```
   *(Use your existing Client Secret)*

3. **Browser Opens Automatically**:
   - OAuth consent screen will open in your default browser
   - **IMPORTANT**: Sign in with the NEW Gmail account (the one you added as test user)
   - Click "Continue" when prompted about unverified app
   - Grant permissions for Gmail API (read-only)
   - You'll see "The authentication flow has completed"

4. **Script Completes**:
   ```
   ✅ Authentication successful!

   📝 Updating .env file...

   ✅ Gmail API setup complete!
   ```

---

### Step 4: Verify New Account

Test the connection with the new account:

```bash
# Test Gmail API connection
python3 silver/scripts/test_gmail_connection.py
```

**Expected Output**:
```
============================================================
Gmail API Connection Test
============================================================

1️⃣  Loading credentials...
   ✅ Credentials loaded

2️⃣  Connecting to Gmail API...
   ✅ Connected successfully!

3️⃣  Fetching account info...
   ✅ Email: newtestuser@gmail.com  ← Should show NEW account
   ✅ Total messages: X
   ✅ Unread messages: Y

============================================================
✅ Gmail API connection test PASSED!
============================================================
```

**Verify**:
- Email address shown is the NEW test account
- No authentication errors
- Message counts are from the new account

---

## 🔍 Verification Checklist

After completing all steps, verify:

- [ ] New Gmail account added as test user in Google Cloud Console
- [ ] Old refresh token cleared from `.env` file
- [ ] Re-authentication completed successfully
- [ ] Test script shows new account email
- [ ] No authentication errors in logs

---

## 🐛 Troubleshooting

### Issue: "Access blocked: This app's request is invalid"

**Cause**: New account not added as test user in Google Cloud Console

**Solution**:
1. Go back to Google Cloud Console
2. Navigate to OAuth consent screen
3. Add the new email to test users
4. Wait 1-2 minutes for changes to propagate
5. Try authentication again

---

### Issue: "Invalid grant" error

**Cause**: Old refresh token still in use

**Solution**:
```bash
# Clear the token manually
nano silver/config/.env

# Find this line:
GMAIL_REFRESH_TOKEN=old_token_here

# Change to:
GMAIL_REFRESH_TOKEN=

# Save and exit (Ctrl+X, Y, Enter)

# Run setup again
python3 silver/scripts/setup_gmail.py
```

---

### Issue: Browser doesn't open automatically

**Cause**: Running in WSL or headless environment

**Solution**:
1. Script will print a URL in the terminal
2. Copy the URL manually
3. Paste into browser on Windows
4. Complete authentication
5. Copy the authorization code from browser
6. Paste back into terminal

---

### Issue: "Redirect URI mismatch"

**Cause**: OAuth credentials not configured for localhost

**Solution**:
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   - `http://localhost`
   - `http://localhost:8080`
4. Click **SAVE**
5. Wait 5 minutes for changes to propagate
6. Try authentication again

---

## 📝 What Gets Updated

When you change accounts, these files are updated:

| File | What Changes |
|------|--------------|
| `silver/config/.env` | `GMAIL_REFRESH_TOKEN` updated with new token |
| Gmail API | Now uses new account for all operations |
| Logs | Future logs will reference new account |

**What Stays the Same**:
- Client ID and Client Secret (same project)
- OAuth consent screen configuration
- Gmail API permissions
- Watcher scripts (no code changes needed)

---

## 🔐 Security Notes

1. **Never commit `.env` file**:
   - Already in `.gitignore`
   - Contains sensitive refresh token

2. **Refresh tokens are account-specific**:
   - Each Gmail account needs its own token
   - Tokens don't expire unless revoked

3. **Test users limit**:
   - Up to 100 test users per project
   - No need to remove old test users

4. **Revoking access**:
   - Old account: Go to https://myaccount.google.com/permissions
   - Find your app and click "Remove access"

---

## 🎯 Quick Reference Commands

```bash
# 1. Reset authentication
python3 silver/scripts/reset_gmail_auth.py

# 2. Re-authenticate with new account
python3 silver/scripts/setup_gmail.py

# 3. Test new connection
python3 silver/scripts/test_gmail_connection.py

# 4. Start watcher with new account
python3 -m silver.src.watchers.gmail_watcher
```

---

## ✅ Success Criteria

You've successfully changed accounts when:

1. ✅ New account appears in Google Cloud Console test users
2. ✅ `test_gmail_connection.py` shows new email address
3. ✅ No authentication errors in output
4. ✅ Gmail watcher can read emails from new account
5. ✅ `.env` file contains new refresh token

---

## 📞 Need Help?

If you encounter issues:

1. Check the troubleshooting section above
2. Review Google Cloud Console settings
3. Verify test user was added correctly
4. Check logs in `silver/Logs/` for detailed errors
5. Try the reset script again

---

**Last Updated**: 2026-01-23
**Tested On**: Python 3.14.0, Google OAuth2 API v2
