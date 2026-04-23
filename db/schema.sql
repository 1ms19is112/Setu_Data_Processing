-- ENUMS (strict allowed values)

CREATE TYPE event_type_enum AS ENUM (
    'payment_initiated',
    'payment_processed',
    'payment_failed',
    'settled'
);

CREATE TYPE transaction_status_enum AS ENUM (
    'payment_initiated',
    'payment_processed',
    'payment_failed',
    'settled'
);

-----------------------------------------------------

-- MERCHANTS

CREATE TABLE merchants (
    merchant_id VARCHAR(50) PRIMARY KEY,
    merchant_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-----------------------------------------------------

-- TRANSACTIONS

CREATE TABLE transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    merchant_id VARCHAR(50) REFERENCES merchants(merchant_id),
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    status transaction_status_enum NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-----------------------------------------------------

-- EVENTS (IDEMPOTENCY LIVES HERE)

CREATE TABLE events (
    event_id VARCHAR(100) PRIMARY KEY,
    transaction_id VARCHAR(100) REFERENCES transactions(transaction_id),
    merchant_id VARCHAR(50) REFERENCES merchants(merchant_id),
    event_type event_type_enum NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-----------------------------------------------------

-- INDEXES (critical for performance)

CREATE INDEX idx_transactions_merchant ON transactions(merchant_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

CREATE INDEX idx_events_transaction ON events(transaction_id);
CREATE INDEX idx_events_type_transaction ON events(event_type, transaction_id);

-----------------------------------------------------

-- UPDATED_AT TRIGGER (auto update timestamps)

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_transactions_updated_at
BEFORE UPDATE ON transactions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_merchants_updated_at
BEFORE UPDATE ON merchants
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();