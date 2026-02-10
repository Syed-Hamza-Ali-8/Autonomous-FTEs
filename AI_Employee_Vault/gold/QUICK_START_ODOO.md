# 🚀 Quick Start: Odoo Community Integration

**Status**: Ready to integrate
**Time Required**: 30-45 minutes
**Date**: 2026-02-09

---

## ✅ What's Already Done

I've prepared everything you need:

1. ✅ **Configuration Files Created**
   - `gold/.env` - Odoo credentials and settings
   - `gold/.env.example` - Template for future reference

2. ✅ **Documentation Created**
   - `gold/ODOO_SETUP_GUIDE.md` - Detailed step-by-step guide
   - `gold/scripts/test_odoo_connection.sh` - Test script

3. ✅ **Odoo Containers Running**
   - `odoo_app` - Odoo 19.0 Community Edition
   - `odoo_db` - PostgreSQL 15 database
   - Accessible at: http://localhost:8069

---

## 🎯 What You Need to Do Now

### Step 1: Open Odoo Web Interface (2 minutes)

```bash
# Open in your browser
http://localhost:8069
```

You'll see the **Odoo Database Manager** page.

### Step 2: Create Database (5 minutes)

Click **"Create Database"** and use these values:

| Field | Value |
|-------|-------|
| Master Password | `admin` |
| Database Name | `ai_employee_accounting` |
| Email | `admin@aiemployee.local` |
| Password | `Admin2026!Secure` |
| Language | English (US) |
| Country | United States |
| Demo Data | ❌ **UNCHECK THIS** |

Click **"Create Database"** and wait 2-3 minutes.

### Step 3: Install Accounting Module (3 minutes)

After database creation:

1. You'll be on the **Apps** page
2. Search for **"Accounting"**
3. Click **"Install"** on the Accounting app
4. Wait 1-2 minutes
5. Configure:
   - Company Name: `AI Employee Business`
   - Currency: `USD`
   - Chart of Accounts: `United States`
6. Click **"Apply"**

### Step 4: Create API User (5 minutes)

1. Click **Settings** (gear icon)
2. Go to **Users & Companies** → **Users**
3. Click **"Create"**
4. Fill in:
   - Name: `API User`
   - Email: `api@aiemployee.local`
   - Password: `ApiUser2026!Secure`
5. In **Access Rights** tab:
   - Accounting: Select **"Accountant"**
6. Click **"Save"**

### Step 5: Add Sample Data (15 minutes)

#### Create 3 Customers

Go to **Accounting** → **Customers** → **Customers**

1. **Client A**: `client-a@example.com`
2. **Client B**: `client-b@example.com`
3. **Client C**: `client-c@example.com`

#### Create 3 Invoices

Go to **Accounting** → **Customers** → **Invoices**

**Invoice 1 (Paid):**
- Customer: Client A
- Date: 2026-01-15
- Product: Consulting Services
- Amount: $1,500
- Click **"Confirm"** → **"Register Payment"**

**Invoice 2 (Unpaid):**
- Customer: Client B
- Date: 2026-01-10
- Product: Project Alpha
- Amount: $2,000
- Click **"Confirm"** only

**Invoice 3 (Unpaid):**
- Customer: Client C
- Date: 2026-01-08
- Product: Monthly Retainer
- Amount: $1,500
- Click **"Confirm"** only

#### Create 3 Expenses

Go to **Accounting** → **Vendors** → **Bills**

1. **Notion**: $15 (paid)
2. **Slack**: $16 (paid)
3. **Office Supplies**: $50 (paid)

### Step 6: Enable Real Odoo Integration (2 minutes)

Edit `gold/.env` and change:

```bash
# Change this line:
USE_MOCK_ODOO=true

# To:
USE_MOCK_ODOO=false
```

### Step 7: Test Connection (3 minutes)

```bash
# Run the test script
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/gold
./scripts/test_odoo_connection.sh
```

You should see:
```
✅ Connection successful
✅ Financial summary retrieved
✅ Found 2 outstanding invoices
✅ All tests passed!
```

### Step 8: Generate CEO Briefing with Real Data (2 minutes)

```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/gold
source .venv/bin/activate
python src/intelligence/ceo_briefing.py
```

Check the output:
```bash
cat ../Reports/CEO_Briefings/ceo_briefing_*.md | tail -50
```

You should see:
- Revenue: $1,500.00 (from Client A)
- Expenses: $81.00 (Notion + Slack + Supplies)
- Outstanding: $3,500.00 (Client B + Client C)

---

## 🎉 Success Criteria

You've successfully integrated Odoo when:

- ✅ Odoo database `ai_employee_accounting` exists
- ✅ API user can log in
- ✅ Sample data is visible in Odoo
- ✅ Test script passes all checks
- ✅ CEO Briefing shows real Odoo data (not mock data)

---

## 📚 Need More Details?

See the full guide: `gold/ODOO_SETUP_GUIDE.md`

---

## 🆘 Troubleshooting

### "Authentication failed"
- Verify password in `.env` matches API user password
- Check username is exactly `api@aiemployee.local`

### "Database not found"
- Verify database name is exactly `ai_employee_accounting`
- Check database was created successfully in Step 2

### "No data in briefing"
- Verify invoice dates are within last 30 days
- Check invoices are in "Posted" state (not Draft)

---

## ⏱️ Time Breakdown

- Database setup: 5 min
- Accounting install: 3 min
- API user creation: 5 min
- Sample data: 15 min
- Testing: 5 min
- **Total: ~30 minutes**

---

**Ready to start? Open http://localhost:8069 and follow the steps above!** 🚀
