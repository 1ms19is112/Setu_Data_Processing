from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Event, Transaction, Merchant
from app.schemas import EventIn

router = APIRouter()

# Priority system (handles out-of-order events)
PRIORITY = {
    "payment_initiated": 1,
    "payment_processed": 2,
    "payment_failed": 3,
    "settled": 4,
}


@router.post("/events")
def ingest_event(event: EventIn, db: Session = Depends(get_db)):

    # 1. Idempotency check
    existing_event = db.get(Event, event.event_id)
    if existing_event:
        return {"message": "duplicate ignored"}

    # 2. Ensure merchant exists
    merchant = db.get(Merchant, event.merchant_id)
    if not merchant:
        merchant = Merchant(
            merchant_id=event.merchant_id,
            merchant_name=event.merchant_name,
        )
        db.add(merchant)
        db.flush()  # IMPORTANT: ensure FK safety

    # 3. Ensure transaction exists
    transaction = db.get(Transaction, event.transaction_id)

    if not transaction:
        transaction = Transaction(
            transaction_id=event.transaction_id,
            merchant_id=event.merchant_id,
            amount=event.amount,
            currency=event.currency,
            status=event.event_type.value,
        )
        db.add(transaction)
        db.flush()  # IMPORTANT: ensure FK safety
    else:
        # 4. Update state (priority-based)
        current_priority = PRIORITY.get(transaction.status, 0)
        new_priority = PRIORITY.get(event.event_type.value, 0)

        if new_priority > current_priority:
            transaction.status = event.event_type.value

    # 5. Insert event
    new_event = Event(
        event_id=event.event_id,
        transaction_id=event.transaction_id,
        merchant_id=event.merchant_id,
        event_type=event.event_type.value,
        amount=event.amount,
        currency=event.currency,
        timestamp=event.timestamp,
    )

    db.add(new_event)

    # 6. Commit safely
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        return {"message": f"duplicate ignored (race condition)", "error": str(e)}

    return {"message": "event recorded"}