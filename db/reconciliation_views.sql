CREATE OR REPLACE VIEW v_processed_not_settled AS
SELECT
    t.transaction_id,
    t.merchant_id,
    t.amount,
    t.status
FROM transactions t
WHERE EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type = 'payment_processed'
)
AND NOT EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type = 'settled'
)
AND NOT EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type = 'payment_failed'
);

CREATE OR REPLACE VIEW v_failed_but_settled AS
SELECT t.transaction_id, t.merchant_id, t.amount, t.status
FROM transactions t
WHERE EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type = 'payment_failed'
)
AND EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type = 'settled'
);

CREATE OR REPLACE VIEW v_stuck_initiated AS
SELECT
    t.transaction_id,
    t.merchant_id,
    t.amount,
    t.status
FROM transactions t
WHERE EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type = 'payment_initiated'
)
AND NOT EXISTS (
    SELECT 1 FROM events e
    WHERE e.transaction_id = t.transaction_id
      AND e.event_type IN ('payment_processed', 'payment_failed', 'settled')
);