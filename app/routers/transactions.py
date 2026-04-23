from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter()


# ================================
# GET /transactions
# ================================

@router.get("/transactions")
def list_transactions(
    merchant_id: str = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    sort_by: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit

    # whitelist sorting (important)
    allowed_sort_fields = {"created_at", "amount", "status"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid order")

    query = text(f"""
        SELECT transaction_id, merchant_id, amount, currency, status, created_at
        FROM transactions
        WHERE (:merchant_id IS NULL OR merchant_id = :merchant_id)
          AND (:status IS NULL OR status = :status)
          AND (:start_date IS NULL OR created_at >= :start_date)
          AND (:end_date IS NULL OR created_at <= :end_date)
        ORDER BY {sort_by} {order}
        LIMIT :limit OFFSET :offset
    """)

    result = db.execute(
        query,
        {
            "merchant_id": merchant_id,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
        },
    )

    rows = result.fetchall()

    return [dict(row._mapping) for row in rows]


# ================================
# GET /transactions/{id}
# ================================

@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):

    # 1. Get transaction
    txn_query = text("""
        SELECT transaction_id, merchant_id, amount, currency, status, created_at
        FROM transactions
        WHERE transaction_id = :transaction_id
    """)

    txn = db.execute(txn_query, {"transaction_id": transaction_id}).fetchone()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # 2. Get events (ordered)
    events_query = text("""
        SELECT event_id, event_type, timestamp
        FROM events
        WHERE transaction_id = :transaction_id
        ORDER BY timestamp
    """)

    events = db.execute(events_query, {"transaction_id": transaction_id}).fetchall()

    return {
        **dict(txn._mapping),
        "events": [dict(e._mapping) for e in events],
    }