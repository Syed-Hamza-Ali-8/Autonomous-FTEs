# Odoo Integration Checklist

**Date**: 2026-02-09
**Status**: Ready for User Completion
**Estimated Time**: 30-45 minutes

---

## ✅ Pre-Integration (Already Complete)

- [x] Odoo Docker containers running (odoo_app, odoo_db)
- [x] Odoo 19.0 Community Edition accessible at http://localhost:8069
- [x] Configuration files created (`.env`, `.env.example`)
- [x] Documentation written (3 guides)
- [x] Test script created (`scripts/test_odoo_connection.sh`)
- [x] MCP server code ready (`mcp/odoo-mcp-python/`)
- [x] CEO Briefing generator supports Odoo integration
- [x] Mock Odoo API available for development

---

## ⏳ User Setup Tasks (Your Work)

### Phase 1: Database Setup (10 minutes)

- [ ] Open http://localhost:8069 in browser
- [ ] Click "Create Database"
- [ ] Fill in database details:
  - [ ] Master Password: `admin`
  - [ ] Database Name: `ai_employee_accounting`
  - [ ] Email: `admin@aiemployee.local`
  - [ ] Password: `Admin2026!Secure`
  - [ ] Language: English (US)
  - [ ] Country: United States
  - [ ] Demo Data: **UNCHECKED**
- [ ] Click "Create Database" and wait 2-3 minutes
- [ ] Verify you're logged in and see the Apps screen

### Phase 2: Accounting Module (5 minutes)

- [ ] Navigate to Apps (should already be there)
- [ ] Search for "Accounting"
- [ ] Click "Install" on Accounting module
- [ ] Wait 1-2 minutes for installation
- [ ] Configure accounting:
  - [ ] Company Name: `AI Employee Business`
  - [ ] Currency: `USD - US Dollar`
  - [ ] Chart of Accounts: `United States`
  - [ ] Fiscal Year: `January - December`
- [ ] Click "Apply"

### Phase 3: API User (5 minutes)

- [ ] Click Settings (gear icon)
- [ ] Go to Users & Companies → Users
- [ ] Click "Create"
- [ ] Fill in user details:
  - [ ] Name: `API User`
  - [ ] Email: `api@aiemployee.local`
  - [ ] Password: `ApiUser2026!Secure`
- [ ] Set Access Rights:
  - [ ] Accounting: Select "Accountant"
- [ ] Click "Save"
- [ ] Test login with API user credentials
- [ ] Log back in as admin

### Phase 4: Sample Customers (3 minutes)

- [ ] Navigate to Accounting → Customers → Customers
- [ ] Create Customer 1:
  - [ ] Name: `Client A`
  - [ ] Email: `client-a@example.com`
  - [ ] Phone: `(555) 123-4567`
  - [ ] Tags: `VIP`, `Consulting`
- [ ] Create Customer 2:
  - [ ] Name: `Client B`
  - [ ] Email: `client-b@example.com`
  - [ ] Phone: `(555) 234-5678`
  - [ ] Tags: `Project-Based`
- [ ] Create Customer 3:
  - [ ] Name: `Client C`
  - [ ] Email: `client-c@example.com`
  - [ ] Phone: `(555) 345-6789`
  - [ ] Tags: `Retainer`

### Phase 5: Sample Invoices (7 minutes)

- [ ] Navigate to Accounting → Customers → Invoices
- [ ] Create Invoice 1 (Paid):
  - [ ] Customer: `Client A`
  - [ ] Invoice Date: `2026-01-15`
  - [ ] Due Date: `2026-01-30`
  - [ ] Product: `Consulting Services - January 2026`
  - [ ] Quantity: `10 hours`
  - [ ] Unit Price: `$150.00`
  - [ ] Click "Confirm"
  - [ ] Click "Register Payment"
  - [ ] Payment Date: `2026-01-15`
  - [ ] Amount: `$1,500.00`
  - [ ] Click "Create Payment"
- [ ] Create Invoice 2 (Unpaid):
  - [ ] Customer: `Client B`
  - [ ] Invoice Date: `2026-01-10`
  - [ ] Due Date: `2026-01-25`
  - [ ] Product: `Project Alpha - Phase 2`
  - [ ] Quantity: `1`
  - [ ] Unit Price: `$2,000.00`
  - [ ] Click "Confirm" (do NOT register payment)
- [ ] Create Invoice 3 (Unpaid):
  - [ ] Customer: `Client C`
  - [ ] Invoice Date: `2026-01-08`
  - [ ] Due Date: `2026-02-08`
  - [ ] Product: `Monthly Retainer - January 2026`
  - [ ] Quantity: `1`
  - [ ] Unit Price: `$1,500.00`
  - [ ] Click "Confirm" (do NOT register payment)

### Phase 6: Sample Expenses (5 minutes)

- [ ] Navigate to Accounting → Vendors → Bills
- [ ] Create Expense 1:
  - [ ] Vendor: `Notion Labs Inc` (create new)
  - [ ] Bill Date: `2026-01-10`
  - [ ] Product: `Notion Subscription - Monthly`
  - [ ] Unit Price: `$15.00`
  - [ ] Click "Confirm" → "Register Payment"
- [ ] Create Expense 2:
  - [ ] Vendor: `Slack Technologies` (create new)
  - [ ] Bill Date: `2026-01-14`
  - [ ] Product: `Slack Premium - Monthly`
  - [ ] Unit Price: `$16.00`
  - [ ] Click "Confirm" → "Register Payment"
- [ ] Create Expense 3:
  - [ ] Vendor: `Amazon` (create new)
  - [ ] Bill Date: `2026-01-12`
  - [ ] Product: `Office Supplies`
  - [ ] Unit Price: `$50.00`
  - [ ] Click "Confirm" → "Register Payment"

### Phase 7: Enable Real Odoo (2 minutes)

- [ ] Open `gold/.env` in text editor
- [ ] Find line: `USE_MOCK_ODOO=true`
- [ ] Change to: `USE_MOCK_ODOO=false`
- [ ] Save file

### Phase 8: Test Connection (3 minutes)

- [ ] Open terminal
- [ ] Navigate to gold directory:
  ```bash
  cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/gold
  ```
- [ ] Run test script:
  ```bash
  ./scripts/test_odoo_connection.sh
  ```
- [ ] Verify output shows:
  - [ ] ✅ Connection successful
  - [ ] ✅ Financial summary retrieved
  - [ ] ✅ Found 2 outstanding invoices
  - [ ] ✅ All tests passed!

### Phase 9: Test CEO Briefing (2 minutes)

- [ ] In same terminal, activate virtual environment:
  ```bash
  source .venv/bin/activate
  ```
- [ ] Generate CEO Briefing:
  ```bash
  python src/intelligence/ceo_briefing.py
  ```
- [ ] View generated briefing:
  ```bash
  cat ../Reports/CEO_Briefings/ceo_briefing_*.md | tail -50
  ```
- [ ] Verify briefing shows:
  - [ ] Revenue: $1,500.00 (from Client A payment)
  - [ ] Expenses: $81.00 (Notion + Slack + Office Supplies)
  - [ ] Outstanding: $3,500.00 (Client B + Client C)
  - [ ] 3 customers listed
  - [ ] Real data (not mock data)

---

## 🎉 Success Criteria

Integration is complete when ALL of these are true:

- [ ] Odoo database `ai_employee_accounting` exists and is accessible
- [ ] API user can log in with `api@aiemployee.local`
- [ ] 3 customers visible in Odoo
- [ ] 3 invoices visible in Odoo (1 paid, 2 unpaid)
- [ ] 3 expenses visible in Odoo (all paid)
- [ ] Test script passes all 8 tests
- [ ] CEO Briefing shows real Odoo data (not mock data)
- [ ] Financial calculations are accurate

---

## 📊 Expected Results

### Test Script Output
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
   ✅ Financial summary retrieved
      Revenue: $1,500.00
      Expenses: $81.00
      Profit: $1,419.00
      Profit Margin: 94.6%
      Outstanding Invoices: 2
      Outstanding Amount: $3,500.00

4. Testing outstanding invoices...
   ✅ Found 2 outstanding invoices

5. Testing customer list...
   ✅ Found 3 customers

6. Testing revenue calculation...
   ✅ Revenue: $1,500.00

7. Testing expenses calculation...
   ✅ Expenses: $81.00

8. Testing invoice filters...
   ✅ Found 3 posted invoices

============================================================
✅ All tests passed!
============================================================
```

### CEO Briefing Output
```markdown
## Financial Performance

- **Revenue**: $1,500.00
- **Expenses**: $81.00
- **Net Profit**: $1,419.00
- **Profit Margin**: 94.6%

### Invoices
- **Total**: 3 invoices ($5,000.00)
- **Paid**: 1 invoices ($1,500.00)
- **Outstanding**: 2 invoices ($3,500.00)
```

---

## 🆘 Troubleshooting

### Issue: Can't access http://localhost:8069

**Check**: Are containers running?
```bash
docker ps | grep odoo
```

**Fix**: Start containers
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/gold
docker-compose -f docker-compose.odoo.yml up -d
```

### Issue: "Authentication failed" in test script

**Check**: Credentials in `.env`
```bash
cat gold/.env | grep ODOO_
```

**Fix**: Verify they match what you set in Odoo
- Username must be exactly: `api@aiemployee.local`
- Password must match what you set for API user

### Issue: "Database not found"

**Check**: Database name
```bash
docker exec odoo_db psql -U odoo -d postgres -c "\l" | grep ai_employee
```

**Fix**: Verify database name is exactly `ai_employee_accounting`

### Issue: CEO Briefing still shows mock data

**Check**: `.env` file
```bash
cat gold/.env | grep USE_MOCK_ODOO
```

**Fix**: Must be set to `false`
```bash
USE_MOCK_ODOO=false
```

### Issue: No data in CEO Briefing

**Check**: Invoice dates
- Invoices must be within last 30 days
- Use dates from January 2026 (current month)

**Fix**: Update invoice dates in Odoo to recent dates

---

## 📈 Progress Tracking

**Total Tasks**: 9 phases
**Estimated Time**: 30-45 minutes

- [ ] Phase 1: Database Setup (10 min)
- [ ] Phase 2: Accounting Module (5 min)
- [ ] Phase 3: API User (5 min)
- [ ] Phase 4: Sample Customers (3 min)
- [ ] Phase 5: Sample Invoices (7 min)
- [ ] Phase 6: Sample Expenses (5 min)
- [ ] Phase 7: Enable Real Odoo (2 min)
- [ ] Phase 8: Test Connection (3 min)
- [ ] Phase 9: Test CEO Briefing (2 min)

---

## 🎯 Gold Tier Impact

### Before Odoo Integration
- Odoo Integration: 50% (installed but not connected)
- CEO Briefing: 60% (using mock data)
- **Overall Gold Tier: 75-80%**

### After Odoo Integration
- Odoo Integration: 100% ✅
- CEO Briefing: 95% ✅
- **Overall Gold Tier: 90-95%** 🎉

---

**Ready to start? Open http://localhost:8069 and begin Phase 1!** 🚀

---

*Checklist created: 2026-02-09*
*Estimated completion time: 30-45 minutes*
*Difficulty: Intermediate*
