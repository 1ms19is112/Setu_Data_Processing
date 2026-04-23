from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    payment_initiated = "payment_initiated"
    payment_processed = "payment_processed"
    payment_failed = "payment_failed"
    settled = "settled"


class EventIn(BaseModel):
    event_id: str
    event_type: EventType
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float = Field(gt=0)
    currency: str
    timestamp: datetime