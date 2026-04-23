from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Literal
from app.database import get_db

router = APIRouter()


# ================================
# SUMMARY
# ================================

@router.get("/reconciliation/summary")
def reconciliation_summary(
    group_by: Literal["merchant", "status"] = "merchant",
    db: Session = Depends(get_db),
):

    if group_by == "merchant":
        query = text("""
            SELECT merchant_id AS group_key,
                   COUNT(*) AS total_transactions,
                   SUM(amount) AS total_amount
            FROM transactions
            GROUP BY merchant_id
        """)
    else:
        query = text("""
            SELECT status AS group_key,
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
        SELECT
            discrepancy_type,
            COUNT(*) AS total,
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'transaction_id', transaction_id,
                    'merchant_id', merchant_id,
                    'amount', amount,
                    'status', status
                )
            ) AS records
        FROM (
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
        ) t
        GROUP BY discrepancy_type
    """)

    result = db.execute(query).fetchall()

    rows = [dict(r._mapping) for r in result]

    return {
        "total_discrepancies": len(rows),
        "discrepancies": rows
    }