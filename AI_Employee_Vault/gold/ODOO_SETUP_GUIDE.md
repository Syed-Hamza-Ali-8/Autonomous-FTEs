# Odoo Community Edition Setup Guide

**Status**: Step-by-step guide for integrating Odoo Community with Gold Tier
**Estimated Time**: 30-45 minutes
**Date**: 2026-02-09

---

## Prerequisites ✅

- [x] Odoo Docker containers running (`odoo_app` and `odoo_db`)
- [x] Odoo accessible at http://localhost:8069
- [x] `.env` file created in `gold/` directory
- [x] Python 3.13 virtual environment in `gold/.venv`

---

## Step 1: Initialize Odoo Database (10 minutes)

### 1.1 Access Odoo Web Interface

```bash
# Open in your browser
http://localhost:8069
```

You should see the **Odoo Database Manager** page.

### 1.2 Create Database

Click **"Create Database"** and fill in:

| Field | Value | Notes |
|-------|-------|-------|
| **Master Password** | `admin` | Default for Docker image |
| **Database Name** | `ai_employee_accounting` | Must match `.env` file |
| **Email** | `admin@aiemployee.local` | Admin user email |
| **Password** | `Admin2026!Secure` | Choose a secure password |
| **Phone Number** | (optional) | Leave blank |
| **Language** | `English (US)` | Select your language |
| **Country** | `United States` | Select your country |
| **Demo Data** | ❌ **Unchecked** | We'll add our own data |

Click **"Create Database"** and wait 2-3 minutes for initialization.

### 1.3 Verify Database Creation

After creation, you should be logged in to Odoo and see the **Apps** screen.

**Checkpoint**: ✅ Database `ai_employee_accounting` created successfully

---

## Step 2: Install Accounting Module (5 minutes)

### 2.1 Navigate to Apps

- You should already be on the **Apps** page
- If not, click the grid icon (☰) → **Apps**

### 2.2 Install Accounting

1. Search for **"Accounting"** in the search bar
2. Find **"Accounting"** (by Odoo S.A.)
3. Click **"Install"**
4. Wait 1-2 minutes for installation

### 2.3 Configure Accounting

After installation, Odoo will prompt you to configure:

| Setting | Value |
|---------|-------|
| **Company Name** | `AI Employee Business` |
| **Currency** | `USD - US Dollar` |
| **Chart of Accounts** | `United States - Chart of Accounts` |
| **Fiscal Year** | `January - December` |
| **Bank Account** | (skip for now) |

Click **"Apply"** to save configuration.

**Checkpoint**: ✅ Accounting module installed and configured

---

## Step 3: Create API User (10 minutes)

### 3.1 Navigate to Users

1. Click **Settings** (gear icon in top menu)
2. Click **Users & Companies** → **Users**

### 3.2 Create New User

Click **"Create"** and fill in:

| Field | Value | Notes |
|-------|-------|-------|
| **Name** | `API User` | Display name |
| **Email Address** | `api@aiemployee.local` | Must match `.env` |
| **Password** | `ApiUser2026!Secure` | Must match `.env` |

### 3.3 Set Access Rights

In the **Access Rights** tab:

1. **Accounting**: Select **"Accountant"**
2. **Sales**: Select **"User: Own Documents Only"** (optional)
3. **Administration**: Leave as **"Access Rights"** (default)

Click **"Save"**.

### 3.4 Test API User Login

1. Log out (click your name → **Log out**)
2. Log in with:
   - Email: `api@aiemployee.local`
   - Password: `ApiUser2026!Secure`
3. Verify you can access **Accounting** module
4. Log out and log back in as admin

**Checkpoint**: ✅ API user created with Accounting access

---

## Step 4: Add Sample Accounting Data (15 minutes)

### 4.1 Create Customers

Navigate to **Accounting** → **Customers** → **Customers**

Create 3 customers:

**Customer 1: Client A**
- Name: `Client A`
- Email: `client-a@example.com`
- Phone: `(555) 123-4567`
- Tags: `VIP`, `Consulting`

**Customer 2: Client B**
- Name: `Client B`
- Email: `client-b@example.com`
- Phone: `(555) 234-5678`
- Tags: `Project-Based`

**Customer 3: Client C**
- Name: `Client C`
- Email: `client-c@example.com`
- Phone: `(555) 345-6789`
- Tags: `Retainer`

### 4.2 Create Invoices

Navigate to **Accounting** → **Customers** → **Invoices**

**Invoice 1: Client A - Paid**
- Customer: `Client A`
- Invoice Date: `2026-01-15`
- Due Date: `2026-01-30`
- Invoice Lines:
  - Product: `Consulting Services - January 2026`
  - Quantity: `10 hours`
  - Unit Price: `$150.00`
  - Total: `$1,500.00`
- Click **"Confirm"** → **"Register Payment"**
  - Payment Date: `2026-01-15`
  - Amount: `$1,500.00`
  - Click **"Create Payment"**

**Invoice 2: Client B - Unpaid**
- Customer: `Client B`
- Invoice Date: `2026-01-10`
- Due Date: `2026-01-25`
- Invoice Lines:
  - Product: `Project Alpha - Phase 2`
  - Quantity: `1`
  - Unit Price: `$2,000.00`
- Click **"Confirm"** (do NOT register payment)

**Invoice 3: Client C - Unpaid**
- Customer: `Client C`
- Invoice Date: `2026-01-08`
- Due Date: `2026-02-08`
- Invoice Lines:
  - Product: `Monthly Retainer - January 2026`
  - Quantity: `1`
  - Unit Price: `$1,500.00`
- Click **"Confirm"** (do NOT register payment)

### 4.3 Create Expenses

Navigate to **Accounting** → **Vendors** → **Bills**

**Expense 1: Notion Subscription**
- Vendor: `Notion Labs Inc` (create new vendor)
- Bill Date: `2026-01-10`
- Due Date: `2026-01-10`
- Bill Lines:
  - Product: `Notion Subscription - Monthly`
  - Quantity: `1`
  - Unit Price: `$15.00`
- Click **"Confirm"** → **"Register Payment"**

**Expense 2: Slack Subscription**
- Vendor: `Slack Technologies` (create new vendor)
- Bill Date: `2026-01-14`
- Due Date: `2026-01-14`
- Bill Lines:
  - Product: `Slack Premium - Monthly`
  - Quantity: `1`
  - Unit Price: `$16.00`
- Click **"Confirm"** → **"Register Payment"**

**Expense 3: Office Supplies**
- Vendor: `Amazon` (create new vendor)
- Bill Date: `2026-01-12`
- Due Date: `2026-01-12`
- Bill Lines:
  - Product: `Office Supplies`
  - Quantity: `1`
  - Unit Price: `$50.00`
- Click **"Confirm"** → **"Register Payment"**

**Checkpoint**: ✅ Sample data added (3 customers, 3 invoices, 3 expenses)

---

## Step 5: Test Odoo MCP Connection (5 minutes)

### 5.1 Update .env File

Edit `gold/.env` and change:

```bash
# Change from:
USE_MOCK_ODOO=true

# To:
USE_MOCK_ODOO=false
```

### 5.2 Run Test Client

```bash
# Navigate to Odoo MCP directory
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/gold/mcp/odoo-mcp-python

# Activate virtual environment
source ../../.venv/bin/activate

# Run test client
python test_client.py
```

### 5.3 Expected Output

```
============================================================
Odoo JSON-RPC Client Test
============================================================

1. Initializing Odoo client...
   ✅ Client initialized

2. Testing connection (health check)...
   ✅ Connection successful
      Database: ai_employee_accounting
      User ID: 2
      URL: http://localhost:8069

3. Testing financial summary...
   Date range: 2026-01-10 to 2026-02-09
   ✅ Financial summary retrieved
      Revenue: $1,500.00
      Expenses: $81.00
      Profit: $1,419.00
      Profit Margin: 94.6%
      Outstanding Invoices: 2
      Outstanding Amount: $3,500.00

4. Testing outstanding invoices...
   ✅ Found 2 outstanding invoices
   First 3 invoices:
      - INV/2026/0002: $2,000.00 (Client B)
      - INV/2026/0003: $1,500.00 (Client C)

5. Testing customer list...
   ✅ Found 3 customers (showing max 5)
      - Client A (client-a@example.com)
      - Client B (client-b@example.com)
      - Client C (client-c@example.com)

6. Testing revenue calculation...
   ✅ Revenue: $1,500.00

7. Testing expenses calculation...
   ✅ Expenses: $81.00

8. Testing invoice filters...
   ✅ Found 3 posted invoices (max 5)

============================================================
✅ All tests passed!
============================================================
```

**Checkpoint**: ✅ Odoo MCP client connected successfully

---

## Step 6: Test CEO Briefing with Real Data (5 minutes)

### 6.1 Generate CEO Briefing

```bash
# Navigate to gold directory
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/gold

# Activate virtual environment
source .venv/bin/activate

# Generate CEO briefing with real Odoo data
python src/intelligence/ceo_briefing.py
```

### 6.2 Verify Real Data

Check the generated briefing:

```bash
# View latest briefing
cat /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/Reports/CEO_Briefings/ceo_briefing_*.md | tail -100
```

Look for:
- ✅ Revenue: $1,500.00 (from Client A payment)
- ✅ Expenses: $81.00 (Notion + Slack + Office Supplies)
- ✅ Outstanding Invoices: 2 (Client B and Client C)
- ✅ Outstanding Amount: $3,500.00

**Checkpoint**: ✅ CEO Briefing using real Odoo data

---

## Step 7: Verification Checklist

Run through this checklist to confirm everything is working:

- [ ] Odoo database `ai_employee_accounting` created
- [ ] Accounting module installed
- [ ] API user `api@aiemployee.local` created with Accountant access
- [ ] 3 customers added (Client A, B, C)
- [ ] 3 invoices created (1 paid, 2 unpaid)
- [ ] 3 expenses added (Notion, Slack, Office Supplies)
- [ ] `.env` file updated with `USE_MOCK_ODOO=false`
- [ ] Odoo MCP test client passes all tests
- [ ] CEO Briefing shows real Odoo data

---

## Troubleshooting

### Issue: "Authentication failed"

**Solution**: Verify credentials in `.env` match API user:
```bash
# Check .env file
cat gold/.env | grep ODOO

# Verify in Odoo: Settings → Users → API User
```

### Issue: "Database not found"

**Solution**: Verify database name:
```bash
# Check database exists
docker exec odoo_db psql -U odoo -d postgres -c "\l" | grep ai_employee
```

### Issue: "No data in CEO Briefing"

**Solution**: Verify date range includes your sample data:
```python
# Check invoice dates in Odoo
# Ensure they're within the last 30 days
```

### Issue: "Connection refused"

**Solution**: Verify Odoo containers are running:
```bash
docker ps | grep odoo
# Should show odoo_app and odoo_db as "Up"
```

---

## Next Steps

After completing this setup:

1. **Update Gold Tier README**: Document that Odoo is now integrated
2. **Test MCP Server**: Verify MCP server can be called from Claude Code
3. **Schedule CEO Briefing**: Configure PM2 for Sunday 7:00 AM execution
4. **Add More Data**: Add more invoices, expenses, and customers as needed
5. **Backup Database**: Export Odoo database for backup

---

## Success Criteria ✅

You've successfully integrated Odoo Community when:

- ✅ Odoo MCP test client passes all 8 tests
- ✅ CEO Briefing shows real financial data from Odoo
- ✅ Revenue, expenses, and profit calculations are accurate
- ✅ Outstanding invoices are correctly identified
- ✅ Customer list is retrieved successfully

---

**Congratulations! Odoo Community Edition is now fully integrated with your Gold Tier AI Employee.** 🎉

---

*Last Updated: 2026-02-09*
*Odoo Version: 19.0 Community Edition*
*Integration Status: Complete*
