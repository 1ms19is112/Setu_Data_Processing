from sqlalchemy import Column, String, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime

Base = declarative_base()

# ================================
# ENUM DEFINITIONS (match DB exactly)
# ================================

event_type_enum = ENUM(
    "payment_initiated",
    "payment_processed",
    "payment_failed",
    "settled",
    name="event_type_enum",
    create_type=False  # IMPORTANT: use existing DB enum
)

transaction_status_enum = ENUM(
    "payment_initiated",
    "payment_processed",
    "payment_failed",
    "settled",
    name="transaction_status_enum",
    create_type=False
)

# ================================
# TABLES
# ================================

class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(String, primary_key=True)
    merchant_name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    merchant_id = Column(String, ForeignKey("merchants.merchant_id"))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="INR")
    status = Column(transaction_status_enum, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    merchant_id = Column(String, ForeignKey("merchants.merchant_id"))
    event_type = Column(event_type_enum, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="INR")
    timestamp = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)