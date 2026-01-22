# Odoo MCP Server (Python)

Python implementation of the Odoo MCP server using the Model Context Protocol SDK.

## Features

- **7 Tools** for Odoo accounting data access
- **JSON-RPC** client for Odoo 19+ External API
- **Native Python** implementation (no Node.js required)
- **Async/await** support for efficient I/O
- **Error handling** with automatic session retry

## Architecture

```
odoo-mcp-python/
├── server.py           # MCP server implementation
├── odoo_client.py      # Odoo JSON-RPC client
├── requirements.txt    # Python dependencies
├── .env.example        # Configuration template
└── README.md           # This file
```

## Installation

### 1. Install Dependencies

```bash
cd gold/mcp/odoo-mcp-python
uv pip install -r requirements.txt
```

**Note**: Using `uv` for faster package installation. If you don't have `uv`, install it with:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your Odoo credentials
```

Required environment variables:
- `ODOO_URL` - Odoo server URL (default: http://localhost:8069)
- `ODOO_DB` - Database name (default: ai_employee_accounting)
- `ODOO_USERNAME` - API user username (default: api@aiemployee.local)
- `ODOO_PASSWORD` - API user password (required)

### 3. Test Connection

```bash
python odoo_client.py
```

Expected output:
```
✅ Health: healthy
   Database: ai_employee_accounting
   UID: 2
✅ Revenue: $12,450.00
   Expenses: $7,200.00
   Profit: $5,250.00
```

## Usage

### Running the MCP Server

```bash
python server.py
```

The server runs on stdio and communicates via JSON-RPC 2.0.

### Available Tools

#### 1. get_financial_summary
Get comprehensive financial summary for a date range.

**Input:**
```json
{
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

**Output:**
```json
{
  "revenue": 12450.00,
  "expenses": 7200.00,
  "profit": 5250.00,
  "profit_margin": 42.17,
  "outstanding_invoices": 3,
  "outstanding_amount": 4500.00,
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

#### 2. get_outstanding_invoices
Get all outstanding invoices (posted but not fully paid).

**Input:** None

**Output:**
```json
[
  {
    "name": "INV/2026/0001",
    "partner_id": [1, "Customer A"],
    "invoice_date": "2026-01-15",
    "invoice_date_due": "2026-02-15",
    "amount_total": 1500.00,
    "amount_residual": 1500.00,
    "payment_state": "not_paid"
  }
]
```

#### 3. get_invoices
Get invoices with optional filters.

**Input:**
```json
{
  "state": "posted",
  "payment_state": "paid",
  "date_from": "2026-01-01",
  "date_to": "2026-01-19",
  "limit": 10
}
```

**Output:** List of invoice records

#### 4. get_revenue
Get total revenue for a date range.

**Input:**
```json
{
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

**Output:**
```json
{
  "revenue": 12450.00,
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

#### 5. get_expenses
Get total expenses for a date range.

**Input:**
```json
{
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

**Output:**
```json
{
  "expenses": 7200.00,
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

#### 6. get_customers
Get list of customers.

**Input:**
```json
{
  "limit": 10
}
```

**Output:** List of customer records

#### 7. health_check
Check Odoo connection and authentication status.

**Input:** None

**Output:**
```json
{
  "status": "healthy",
  "uid": 2,
  "database": "ai_employee_accounting",
  "url": "http://localhost:8069"
}
```

## Integration with CEO Briefing

The Python MCP server can be used directly by the CEO Briefing generator:

```python
from gold.mcp.odoo_mcp_python.odoo_client import OdooClient

# Initialize client
odoo = OdooClient(
    url="http://localhost:8069",
    db="ai_employee_accounting",
    username="api@aiemployee.local",
    password="your_password"
)

# Get financial summary
summary = odoo.get_financial_summary("2026-01-01", "2026-01-19")
print(f"Revenue: ${summary['revenue']:,.2f}")
print(f"Profit: ${summary['profit']:,.2f}")
```

## Odoo JSON-RPC API

The client uses Odoo's External API via JSON-RPC:

### Authentication
```
POST /web/session/authenticate
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "db": "ai_employee_accounting",
    "login": "api@aiemployee.local",
    "password": "password"
  }
}
```

### Model Method Calls
```
POST /web/dataset/call_kw
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "account.move",
    "method": "search_read",
    "args": [[["state", "=", "posted"]]],
    "kwargs": {"fields": ["name", "amount_total"]}
  }
}
```

## Error Handling

The client includes automatic error recovery:

1. **Session Expiry**: Automatically re-authenticates if session expires
2. **Connection Errors**: Raises clear exceptions with error messages
3. **API Errors**: Parses and reports Odoo API errors

## Testing

### Unit Tests (Manual)

```bash
# Test Odoo client
python odoo_client.py

# Test MCP server (requires MCP client)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health_check","arguments":{}}}' | python server.py
```

### Integration Test

```bash
# Test with CEO Briefing
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
python gold/src/intelligence/ceo_briefing.py
```

## Troubleshooting

### Connection Refused
```
Error: Odoo authentication error: Connection refused
```

**Solution**: Ensure Odoo is running:
```bash
docker ps | grep odoo
```

### Authentication Failed
```
Error: Authentication failed: Access Denied
```

**Solution**: Check credentials in `.env`:
- Verify username and password
- Ensure user has API access rights

### Module Not Found
```
ModuleNotFoundError: No module named 'mcp'
```

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Session Expired
The client automatically handles session expiry by re-authenticating.

## Performance

- **Authentication**: ~100-200ms (cached after first call)
- **Financial Summary**: ~500-1000ms (3 parallel queries)
- **Single Query**: ~50-150ms

## Security

- **Credentials**: Stored in `.env` (never commit to git)
- **Session Management**: Automatic session handling with cookies
- **API Access**: Uses Odoo's built-in access control
- **HTTPS**: Supports HTTPS URLs for production

## Comparison: Python vs JavaScript

| Feature | Python | JavaScript |
|---------|--------|------------|
| Dependencies | `mcp`, `requests` | `@modelcontextprotocol/sdk`, `axios` |
| Async | `asyncio` | Native promises |
| Type Safety | Type hints | TypeScript (optional) |
| Performance | Similar | Similar |
| Integration | Direct import | Subprocess call |

**Advantages of Python:**
- Direct integration with Python codebase
- No Node.js dependency
- Simpler deployment
- Better type hints with Python 3.10+

## License

MIT License - Part of AI Employee Vault Gold Tier

## Version

1.0.0 - Initial Python implementation (2026-01-19)
