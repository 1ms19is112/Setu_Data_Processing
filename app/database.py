import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

# Engine config (optimized for Supabase + Railway)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,          # safer for free tier
    max_overflow=2,       # avoids hitting limits
    pool_timeout=30,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()