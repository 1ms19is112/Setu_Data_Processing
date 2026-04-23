# Payment Reconciliation Service

A backend service that ingests payment lifecycle events, tracks transaction state, and surfaces settlement discrepancies. Built with FastAPI, PostgreSQL, and designed for reliability and maintainability.

**Live Deployment:** https://setuassignmentdb.up.railway.app/

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Local Development Setup](#local-development-setup)
3. [API Documentation](#api-documentation)
4. [Deployment Details](#deployment-details)
5. [Assumptions & Tradeoffs](#assumptions--tradeoffs)

---

## Architecture Overview

### System Design

The service is built around a simple but powerful principle: **events are immutable facts, transactions are mutable state**. All payment lifecycle events flow through the system and get stored permanently in the `events` table. The `transactions` table stays synchronized with the latest event state for each transaction, enabling fast queries and discrepancy detection.

### Core Layers

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   /events    │  │  /transactions│  │/reconciliation│  │
│  │   (Ingestion)│  │   (Query API) │  │  (Analytics) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                  ↓                  ↓         │
├─────────────────────────────────────────────────────────┤
│                  Pydantic Validation Layer              │
├─────────────────────────────────────────────────────────┤
│                  SQLAlchemy ORM Layer                   │
├─────────────────────────────────────────────────────────┤
│                  Connection Pooling                     │
├─────────────────────────────────────────────────────────┤
│            PostgreSQL (Supabase) Database               │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  merchants  │  │ transactions │  │   events    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  reconciliation_views (SQL views for analytics) │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Data Model

**3 Core Tables:**

1. **merchants** — Store merchant details
   - `merchant_id` (PK): Unique identifier
   - `merchant_name`: Human-readable name
   - `created_at`, `updated_at`: Timestamps

2. **transactions** — Current state of each payment
   - `transaction_id` (PK): Unique transaction identifier
   - `merchant_id` (FK): Links to merchants
   - `amount`: Exact decimal (NUMERIC(12,2))
   - `currency`: ISO 4217 code (default: INR)
   - `status`: ENUM (payment_initiated, payment_processed, payment_failed, settled)
   - `created_at`, `updated_at`: Timestamps

3. **events** — Immutable audit trail
   - `event_id` (PK): Uniqueness ensures idempotency
   - `transaction_id` (FK): Links to transactions
   - `event_type`: ENUM (payment_initiated, payment_processed, payment_failed, settled)
   - `amount`: From the event payload
   - `timestamp`: When event occurred in source system
   - `created_at`: When we received it

**Key Design Decisions:**
- Events are append-only. No updates or deletes.
- Transaction status updated atomically when valid events arrive.
- Duplicate event IDs are silently rejected at the database level (PRIMARY KEY constraint).
- All money amounts stored as NUMERIC(12,2) — never float.
- Timestamps always stored in UTC (TIMESTAMPTZ).

### State Machine

```
payment_initiated
    ↓
    ├→ payment_processed → settled (success path)
    │
    └→ payment_failed (terminal)
```

Invalid transitions are rejected. Once a transaction reaches "settled" or "payment_failed", no further state changes are allowed.

### Project Structure

```
claudeFin/
├── main.py                      # FastAPI app entry point, router registration
├── requirements.txt             # Python dependencies
├── Procfile                     # Deployment config for Railway
├── runtime.txt                  # Python version specification
├── dbcheck.py                   # Utility to verify DATABASE_URL connectivity
├── Technical_Specification.html # Detailed design document
├── readme.md                    # This file
│
├── app/
│   ├── database.py              # SQLAlchemy engine, session factory, connection pooling
│   ├── models.py                # ORM models (Merchant, Transaction, Event) + ENUM definitions
│   ├── schemas.py               # Pydantic models for request/response validation
│   │
│   └── routers/
│       ├── events.py            # POST /events (event ingestion with idempotency)
│       ├── transactions.py      # GET /transactions, GET /transactions/{id}
│       └── reconciliation.py    # GET /reconciliation/summary, /discrepancies
│
├── db/
│   ├── schema.sql               # Database schema: tables, ENUMs, indexes, triggers
│   └── reconciliation_views.sql # SQL views for discrepancy detection
│
└── data/
    ├── sample_events.json       # 10,000 sample payment events
    └── seed.py                  # Bulk event loader with retry logic
```

---

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ (or Supabase free tier account)
- Git

### Step 1: Clone & Install Dependencies

```bash
# Clone the repository
git clone <repo-url>
cd transactions_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Database

#### Option A: Using Supabase (Recommended)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (PostgreSQL database is provided)
3. Copy the connection string from Project Settings → Database
4. Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://[user]:[password]@[host].supabase.co:5432/postgres
```

5. Run the schema:

```bash
# Using psql directly
psql $DATABASE_URL -f db/schema.sql

# Or paste the contents of db/schema.sql in Supabase SQL Editor
```

#### Option B: Local PostgreSQL

```bash
# Create database
createdb payment_service

# Set environment variable
export DATABASE_URL=postgresql://localhost/payment_service

# Run schema
psql payment_service -f db/schema.sql
```

### Step 3: Verify Database Connection

```bash
python dbcheck.py
```

This script will verify that DATABASE_URL is valid and the connection works.

### Step 4: Run the Development Server

```bash
uvicorn main:app --reload
```

The API will start at `http://localhost:8000`

### Step 5: Load Sample Data (Optional)

```bash
python data/seed.py
```

This loads 10,000 sample events into your local database.

### Step 6: Access the API

- **Swagger UI:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **ReDoc:** http://localhost:8000/redoc

---

## API Documentation

All API endpoints are documented in the interactive Swagger UI at `/docs` on the live server or your local instance.

### Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/events` | Ingest a payment event |
| GET | `/transactions` | List all transactions (filtered, paginated) |
| GET | `/transactions/{id}` | Get transaction details with event history |
| GET | `/reconciliation/summary` | Aggregated statistics (grouped by merchant or status) |
| GET | `/reconciliation/discrepancies` | Find payment anomalies |

---

### 1. POST /events — Ingest Payment Event

**Request Body:**

```json
{
  "event_id": "evt_12345",
  "transaction_id": "txn_abc123",
  "merchant_id": "merchant_1",
  "merchant_name": "Acme Corp",
  "event_type": "payment_initiated",
  "amount": 15248.29,
  "currency": "INR",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

**Response (200 OK):**

```json
{
  "message": "event recorded",
  "transaction_id": "txn_abc123",
  "status": "payment_initiated"
}
```

**Valid Event Types:** `payment_initiated`, `payment_processed`, `payment_failed`, `settled`

**Idempotency:** The same event_id will not create duplicate records. Duplicate submissions return 200 with "duplicate ignored" message.

**Validation Rules:**
- `event_id`: Non-empty string, unique
- `transaction_id`: Non-empty string
- `merchant_id`: Non-empty string
- `amount`: Must be positive (> 0)
- `event_type`: Must be one of the 4 valid types
- `timestamp`: Valid ISO 8601 datetime

---

### 2. GET /transactions — List Transactions

**Query Parameters:**

| Parameter | Type | Example | Notes |
|-----------|------|---------|-------|
| `merchant_id` | string | `?merchant_id=merchant_1` | Optional. Filter by merchant. |
| `status` | string | `?status=settled` | Optional. Filter by transaction status. |
| `start_date` | date | `?start_date=2026-01-01` | Optional. Filter by created_at >= date. |
| `end_date` | date | `?end_date=2026-01-31` | Optional. Filter by created_at <= date. |
| `page` | integer | `?page=2` | Default: 1. Pagination page number. |
| `limit` | integer | `?limit=50` | Default: 20. Max: 100. Results per page. |
| `sort_by` | string | `?sort_by=amount` | Default: created_at. Options: created_at, amount, status. |
| `order` | string | `?order=asc` | Default: desc. Order: asc or desc. |

**Response (200 OK):**

```json
[
  {
    "transaction_id": "txn_abc123",
    "merchant_id": "merchant_1",
    "amount": 15248.29,
    "currency": "INR",
    "status": "settled",
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:45:00Z"
  }
]
```

**Examples:**

```
# Get all settled transactions for merchant_1
GET /transactions?merchant_id=merchant_1&status=settled

# Get transactions from January, sorted by amount (descending), page 2
GET /transactions?start_date=2026-01-01&end_date=2026-01-31&sort_by=amount&order=desc&page=2&limit=10
```

---

### 3. GET /transactions/{id} — Transaction Detail with Event History

**Response (200 OK):**

```json
{
  "transaction_id": "txn_abc123",
  "merchant_id": "merchant_1",
  "amount": 15248.29,
  "currency": "INR",
  "status": "settled",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:45:00Z",
  "events": [
    {
      "event_id": "evt_12345",
      "event_type": "payment_initiated",
      "timestamp": "2026-01-15T10:30:00Z",
      "amount": 15248.29,
      "created_at": "2026-01-15T10:30:05Z"
    },
    {
      "event_id": "evt_12346",
      "event_type": "payment_processed",
      "timestamp": "2026-01-15T10:35:00Z",
      "amount": 15248.29,
      "created_at": "2026-01-15T10:35:02Z"
    },
    {
      "event_id": "evt_12347",
      "event_type": "settled",
      "timestamp": "2026-01-15T10:45:00Z",
      "amount": 15248.29,
      "created_at": "2026-01-15T10:45:01Z"
    }
  ]
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Transaction not found"
}
```

---

### 4. GET /reconciliation/summary — Aggregated Statistics

**Query Parameters:**

| Parameter | Type | Example | Notes |
|-----------|------|---------|-------|
| `group_by` | string | `?group_by=merchant` | Options: merchant (default) or status. |

**Response (200 OK) — Grouped by Merchant:**

```json
[
  {
    "group": "merchant_1",
    "total_transactions": 412,
    "total_amount": 2840192.50
  },
  {
    "group": "merchant_2",
    "total_transactions": 389,
    "total_amount": 1920441.00
  }
]
```

**Response (200 OK) — Grouped by Status:**

```json
[
  {
    "group": "settled",
    "total_transactions": 586,
    "total_amount": 4120819.50
  },
  {
    "group": "payment_processed",
    "total_transactions": 142,
    "total_amount": 893422.75
  },
  {
    "group": "payment_failed",
    "total_transactions": 73,
    "total_amount": 421391.25
  }
]
```

---

### 5. GET /reconciliation/discrepancies — Find Anomalies

Identifies three types of payment anomalies:

1. **Processed but not settled** — Payment approved but merchant never received funds
2. **Failed but settled** — Payment rejected but settlement exists (rare, but critical)
3. **Stuck at initiated** — Payment never progressed past initiation

**Response (200 OK):**

```json
{
  "total_discrepancies": 47,
  "discrepancies": [
    {
      "transaction_id": "txn_stuck_001",
      "merchant_id": "merchant_5",
      "amount": 5000.00,
      "status": "payment_initiated",
      "discrepancy_type": "stuck at initiated"
    },
    {
      "transaction_id": "txn_processed_001",
      "merchant_id": "merchant_2",
      "amount": 8750.50,
      "status": "payment_processed",
      "discrepancy_type": "processed but never settled"
    },
    {
      "transaction_id": "txn_failed_001",
      "merchant_id": "merchant_8",
      "amount": 3200.00,
      "status": "payment_failed",
      "discrepancy_type": "failed but settled"
    }
  ]
}
```

---

## Deployment Details

### Live Environment

**URL:** https://setuassignmentdb.up.railway.app/

The application is deployed on Railway with Supabase PostgreSQL as the database.

### Deployment Architecture

```
GitHub Repository
        ↓
    (push)
        ↓
   Railway CI/CD
        ↓
   Build & Deploy
        ↓
   Live Service ←→ Supabase PostgreSQL
```

### Deploy Your Own (Railway + Supabase)

#### Step 1: Set Up Supabase

1. Create a Supabase account at [supabase.com](https://supabase.com)
2. Create a new project
3. In the project dashboard, go to Settings → Database
4. Copy the connection string (URI)
5. Run `db/schema.sql` in the SQL Editor

#### Step 2: Deploy to Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) and sign in
3. Create a new project, select "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables:
   - `DATABASE_URL`: Your Supabase connection string
   - `PYTHON_VERSION`: `3.11`

6. Railway automatically detects `requirements.txt` and `Procfile`
7. The app will build and deploy

#### Step 3: Verify Deployment

```bash
# Test health endpoint
curl https://<your-railway-app>.up.railway.app/health

# Should return:
# {"status": "ok"}
```

### Environment Variables

**Required:**
- `DATABASE_URL`: PostgreSQL connection string

**Optional (with defaults):**
- `PYTHONUNBUFFERED`: Set to 1 (helps with logging)
- `PORT`: Defaults to 8000

### Database Migrations

The schema is applied once during initial setup via `db/schema.sql`. For production changes:

1. Create a new migration in `db/migrations/`
2. Test locally
3. Apply to production database manually or via deployment pipeline

*Note: No automated migrations in this MVP. Schema is stable.*

---

## Assumptions & Tradeoffs

### Assumptions Made

**Data Assumptions:**
- Events arrive out-of-order. The system uses a priority-based state machine to handle this.
- Event IDs are globally unique across all events (no collisions).
- Merchants must exist before transactions (auto-created on first event).
- All amounts are positive. Refunds not supported in MVP.
- Timestamps in events are UTC or timezone-aware.

**Architectural Assumptions:**
- Single database. No sharding or multi-region support.
- State transitions are immutable. Once "settled" or "failed", no further changes.
- Events are immutable. No updates or deletes allowed.
- Duplicate detection is critical and happens at the database level (PRIMARY KEY on event_id).
- Consistency over availability. If DB is down, the API returns 5xx.

**Operational Assumptions:**
- Database schema is initialized before the app starts.
- All configuration via environment variables (DATABASE_URL).
- No manual rate limiting. Assumes trusted sources.
- Logging to stdout (captured by deployment platform).

### Tradeoffs & Simplifications

| Tradeoff | Current MVP | Production Alternative |
|----------|-------------|------------------------|
| **Batch Event Ingestion** | Single event per POST | Support POST /events/batch for bulk loads |
| **Caching** | None. Every query hits DB. | Redis cache for /transactions results |
| **Materialized Views** | SQL views recalculated per query | Materialized views, refreshed on schedule |
| **Authentication** | Open. No API keys. | JWT bearer token or API key auth |
| **Rate Limiting** | None | Per-IP or per-merchant rate limits |
| **Error Handling** | Basic validation errors | Comprehensive error recovery & retry logic |
| **Monitoring** | Logging to stdout | Structured JSON logging + metrics (Prometheus) |
| **Database Backups** | Supabase automatic backups | Custom backup schedule + restore testing |
| **Multi-Environment** | Single production config | Separate .env.local, .env.staging, .env.prod |
| **API Documentation** | Auto-generated Swagger UI | Postman collection + custom documentation |
| **Test Suite** | Manual testing | Automated pytest + integration tests |

### Why These Tradeoffs Were Made

1. **No Authentication:** The MVP assumes internal use or trusted sources. Adding JWT would add complexity without clear business need yet.

2. **No Caching:** 10,000 events is a small dataset. Database is fast enough. Added complexity for minimal gain.

3. **No Batch Ingestion:** Single event per POST keeps the ingestion logic simple. Bulk loading via seed.py is acceptable for test data.

4. **Simple Error Handling:** Pydantic handles validation. Invalid state transitions return 200 (not error), which aligns with the "idempotency" principle.

5. **No Sharding:** Single database is sufficient for MVP scale. Can be partitioned later if needed.

### What Would Be Done First With More Time

1. **Automated Test Suite** — pytest with 85%+ coverage
2. **Structured Logging** — JSON logs with request_id tracing
3. **Basic Monitoring** — Prometheus metrics, Grafana dashboards
4. **Materialized Views** — Replace SQL views for faster reconciliation queries
5. **API Authentication** — Protect endpoints with API keys or JWT
6. **Integration Tests** — End-to-end flows with test database isolation

---

## Running Tests

The API includes manual test cases for each phase. Interactive testing is recommended:

```bash
# Start the server
uvicorn main:app --reload

# In another terminal, use curl or Postman
curl http://localhost:8000/health

# Or use the Swagger UI
open http://localhost:8000/docs
```

**Example Test Sequence:**

1. Post a single event:
   ```bash
   curl -X POST http://localhost:8000/events \
     -H "Content-Type: application/json" \
     -d '{
       "event_id": "evt_test_1",
       "transaction_id": "txn_test_1",
       "merchant_id": "merchant_1",
       "merchant_name": "Test Merchant",
       "event_type": "payment_initiated",
       "amount": 100.00,
       "currency": "INR",
       "timestamp": "2026-01-15T10:00:00Z"
     }'
   ```

2. Query transactions:
   ```bash
   curl http://localhost:8000/transactions
   ```

3. Get transaction detail:
   ```bash
   curl http://localhost:8000/transactions/txn_test_1
   ```

4. Check reconciliation:
   ```bash
   curl http://localhost:8000/reconciliation/summary?group_by=merchant
   ```

---

## Troubleshooting

### Database Connection Error

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Verify DATABASE_URL is correct: `python dbcheck.py`
2. Check that the database is running and accessible
3. For Supabase: Verify the IP is whitelisted (if using regional network)

### Port Already in Use

**Problem:** `Address already in use`

**Solution:**
```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

### Schema Not Found

**Problem:** `relation "transactions" does not exist`

**Solution:**
```bash
# Re-run the schema
psql $DATABASE_URL -f db/schema.sql
```

### Invalid State Transition

**Problem:** Event rejected with "invalid state transition"

**Solution:**
This is expected behavior. The system enforces the state machine. Valid transitions are:
- `payment_initiated` → `payment_processed` → `settled`
- `payment_initiated` → `payment_failed`

Any other sequence is rejected.

---

## Support & Questions

For detailed design documentation, see [Technical_Specification.html](Technical_Specification.html) for the complete architecture document with test cases and design rationale.

---

## License

This project is provided as-is for educational and assignment purposes.
