from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter()


# ================================
# SUMMARY
# ================================

@router.get("/reconciliation/summary")
def reconciliation_summary(
    group_by: str = Query("merchant", enum=["merchant", "status"]),
    db: Session = Depends(get_db),
):

    if group_by == "merchant":
        query = text("""
            SELECT merchant_id AS group,
                   COUNT(*) AS total_transactions,
                   SUM(amount) AS total_amount
            FROM transactions
            GROUP BY merchant_id
        """)
    else:
        query = text("""
            SELECT status AS group,
                   COUNT(*) AS total_transactions,
                   SUM(amount) AS total_amount
            FROM transactions
            GROUP BY status
        """)

    result = db.execute(query).fetchall()

    return [dict(row._mapping) for row in result]


# ================================
# DISCREPANCIES
# ================================

@router.get("/reconciliation/discrepancies")
def reconciliation_discrepancies(db: Session = Depends(get_db)):

    query = text("""
        SELECT transaction_id, merchant_id, amount, status,
               'processed but not settled' AS discrepancy_type
        FROM v_processed_not_settled

        UNION ALL

        SELECT transaction_id, merchant_id, amount, status,
               'failed but settled' AS discrepancy_type
        FROM v_failed_but_settled

        UNION ALL

        SELECT transaction_id, merchant_id, amount, status,
               'stuck initiated' AS discrepancy_type
        FROM v_stuck_initiated
    """)

    result = db.execute(query).fetchall()

    rows = [dict(r._mapping) for r in result]

    return {
        "total_discrepancies": len(rows),
        "discrepancies": rows
    }