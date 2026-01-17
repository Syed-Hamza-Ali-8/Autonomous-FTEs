# Xero MCP Server API Contract

**Version**: 1.0
**Last Updated**: 2026-01-17
**Status**: Active

## Overview

This document defines the API contract for the Xero MCP (Model Context Protocol) server, which provides integration with Xero accounting platform for the Gold Tier autonomous employee.

## Base Configuration

```json
{
  "mcpServers": {
    "xero": {
      "command": "node",
      "args": ["gold/mcp/xero/server.js"],
      "env": {
        "XERO_CLIENT_ID": "${XERO_CLIENT_ID}",
        "XERO_CLIENT_SECRET": "${XERO_CLIENT_SECRET}",
        "XERO_REDIRECT_URI": "${XERO_REDIRECT_URI}",
        "XERO_TENANT_ID": "${XERO_TENANT_ID}"
      }
    }
  }
}
```

## Authentication

### OAuth 2.0 Flow

**Authorization URL**: `https://login.xero.com/identity/connect/authorize`

**Token URL**: `https://identity.xero.com/connect/token`

**Scopes Required**:
- `accounting.transactions.read`
- `accounting.contacts.read`
- `accounting.reports.read`
- `accounting.settings.read`
- `offline_access`

### Token Storage

Tokens stored in: `gold/.credentials/xero_tokens.json`

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_at": "ISO-8601 datetime",
  "tenant_id": "string"
}
```

## API Methods

### 1. getTransactions

Retrieve transactions from Xero.

**Input**:
```json
{
  "method": "getTransactions",
  "params": {
    "startDate": "2026-01-01",
    "endDate": "2026-01-31",
    "type": "income|expense|all",
    "limit": 100,
    "offset": 0
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "transaction_id": "xero_tx_12345",
        "date": "2026-01-15",
        "amount": -15.00,
        "currency": "USD",
        "category": "expense",
        "subcategory": "software_subscription",
        "description": "Monthly Notion subscription",
        "vendor": "Notion Labs Inc",
        "business_related": true,
        "tax_deductible": true
      }
    ],
    "total": 45,
    "limit": 100,
    "offset": 0
  }
}
```

**Error Codes**:
- `XERO_AUTH_FAILED`: Authentication failed
- `XERO_RATE_LIMIT`: Rate limit exceeded
- `XERO_INVALID_DATE`: Invalid date format
- `XERO_API_ERROR`: Xero API error

---

### 2. getInvoices

Retrieve invoices from Xero.

**Input**:
```json
{
  "method": "getInvoices",
  "params": {
    "status": "DRAFT|SUBMITTED|AUTHORISED|PAID|VOIDED",
    "startDate": "2026-01-01",
    "endDate": "2026-01-31",
    "contactId": "optional-contact-id"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "invoices": [
      {
        "invoice_id": "INV-2026-001",
        "invoice_number": "INV-2026-001",
        "contact": "Client A",
        "date": "2026-01-15",
        "due_date": "2026-01-30",
        "status": "AUTHORISED",
        "total": 1500.00,
        "amount_due": 1500.00,
        "amount_paid": 0.00,
        "currency": "USD",
        "line_items": [
          {
            "description": "Consulting services",
            "quantity": 10,
            "unit_amount": 150.00,
            "line_amount": 1500.00
          }
        ]
      }
    ]
  }
}
```

---

### 3. createInvoice

Create a new invoice in Xero.

**Input**:
```json
{
  "method": "createInvoice",
  "params": {
    "contact": "Client A",
    "date": "2026-01-15",
    "due_date": "2026-01-30",
    "line_items": [
      {
        "description": "Consulting services",
        "quantity": 10,
        "unit_amount": 150.00
      }
    ],
    "reference": "Project Alpha - Phase 2",
    "status": "DRAFT"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "invoice_id": "INV-2026-001",
    "invoice_number": "INV-2026-001",
    "status": "DRAFT",
    "total": 1500.00,
    "url": "https://go.xero.com/AccountsReceivable/View.aspx?InvoiceID=..."
  }
}
```

**Approval Required**: Yes (if total > $500)

---

### 4. updateInvoice

Update an existing invoice.

**Input**:
```json
{
  "method": "updateInvoice",
  "params": {
    "invoice_id": "INV-2026-001",
    "status": "AUTHORISED|PAID|VOIDED",
    "payment_date": "2026-01-20",
    "payment_amount": 1500.00
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "invoice_id": "INV-2026-001",
    "status": "PAID",
    "amount_paid": 1500.00,
    "updated_at": "2026-01-20T10:00:00Z"
  }
}
```

---

### 5. getContacts

Retrieve contacts (clients/vendors) from Xero.

**Input**:
```json
{
  "method": "getContacts",
  "params": {
    "type": "CUSTOMER|SUPPLIER|ALL",
    "search": "optional search term"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "contacts": [
      {
        "contact_id": "xero_contact_123",
        "name": "Client A",
        "email": "client-a@example.com",
        "type": "CUSTOMER",
        "balance": 1500.00
      }
    ]
  }
}
```

---

### 6. getReports

Generate financial reports.

**Input**:
```json
{
  "method": "getReports",
  "params": {
    "report_type": "ProfitAndLoss|BalanceSheet|CashFlow",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "periods": 1
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "report_type": "ProfitAndLoss",
    "period": "2026-01-01 to 2026-01-31",
    "revenue": 4500.00,
    "expenses": 2000.00,
    "net_profit": 2500.00,
    "sections": [
      {
        "title": "Revenue",
        "total": 4500.00,
        "rows": [
          {
            "account": "Sales",
            "amount": 4500.00
          }
        ]
      },
      {
        "title": "Expenses",
        "total": 2000.00,
        "rows": [
          {
            "account": "Software Subscriptions",
            "amount": 500.00
          },
          {
            "account": "Office Supplies",
            "amount": 200.00
          }
        ]
      }
    ]
  }
}
```

---

### 7. categorizeTransaction

Automatically categorize a transaction using AI.

**Input**:
```json
{
  "method": "categorizeTransaction",
  "params": {
    "description": "Monthly Notion subscription",
    "vendor": "Notion Labs Inc",
    "amount": -15.00
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "category": "expense",
    "subcategory": "software_subscription",
    "business_related": true,
    "tax_deductible": true,
    "confidence": 0.95,
    "reasoning": "Recurring software subscription for business productivity tool"
  }
}
```

---

### 8. syncTransactions

Sync transactions from Xero to vault.

**Input**:
```json
{
  "method": "syncTransactions",
  "params": {
    "since": "2026-01-01T00:00:00Z",
    "auto_categorize": true
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "synced": 45,
    "categorized": 45,
    "errors": 0,
    "files_created": [
      "/Vault/Accounting/Transactions/xero_tx_12345.md",
      "/Vault/Accounting/Transactions/xero_tx_12346.md"
    ]
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "type": "transient|auth|logic|data|system",
    "recoverable": true,
    "retry_after": 60
  }
}
```

### Error Codes

| Code | Type | Recoverable | Description |
|------|------|-------------|-------------|
| `XERO_AUTH_FAILED` | auth | Yes | OAuth authentication failed |
| `XERO_TOKEN_EXPIRED` | auth | Yes | Access token expired |
| `XERO_RATE_LIMIT` | transient | Yes | Rate limit exceeded |
| `XERO_API_ERROR` | transient | Yes | Xero API error |
| `XERO_INVALID_PARAMS` | logic | No | Invalid parameters |
| `XERO_NOT_FOUND` | data | No | Resource not found |
| `XERO_NETWORK_ERROR` | transient | Yes | Network error |

---

## Rate Limiting

**Xero API Limits**:
- 60 requests per minute per tenant
- 5,000 requests per day per tenant

**MCP Server Handling**:
- Automatic retry with exponential backoff
- Queue requests when rate limit approached
- Return `XERO_RATE_LIMIT` error if queue full

---

## Testing

### Test Credentials

Use Xero Demo Company for testing:
- Create demo company at https://developer.xero.com/
- Use demo company tenant ID for testing

### Test Cases

1. **Authentication Flow**
   - Test OAuth authorization
   - Test token refresh
   - Test expired token handling

2. **Transaction Sync**
   - Sync transactions from demo company
   - Verify categorization
   - Verify file creation in vault

3. **Invoice Management**
   - Create draft invoice
   - Update invoice status
   - Mark invoice as paid

4. **Financial Reports**
   - Generate P&L report
   - Generate balance sheet
   - Verify calculations

5. **Error Handling**
   - Test rate limit handling
   - Test network error recovery
   - Test invalid parameter handling

---

## Security

### Credentials Storage

- OAuth tokens encrypted at rest
- Client secret never logged
- Tokens refreshed automatically before expiry

### Data Handling

- All financial data classified as "confidential"
- Audit logging for all Xero operations
- No caching of sensitive data

### Compliance

- GDPR compliant data handling
- SOC 2 Type II controls
- PCI DSS not applicable (no card data)

---

## Integration Points

### Watchers
- `XeroWatcher`: Polls for new transactions every 15 minutes

### Actions
- `InvoiceManager`: Creates and updates invoices
- `FinancialReporter`: Generates reports
- `TransactionCategorizer`: Categorizes transactions

### Intelligence
- `CEOBriefingGenerator`: Uses Xero data for revenue analysis
- `CrossDomainReasoner`: Links payments to business actions
- `SubscriptionAuditor`: Analyzes recurring expenses

---

**API Version**: 1.0
**Xero API Version**: 2.0
**Last Updated**: 2026-01-17
