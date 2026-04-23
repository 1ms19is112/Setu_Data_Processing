import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. Load the variables from your .env file
load_dotenv()
db_url = os.getenv("DATABASE_URL")

# 2. Safety Check: Ensure the dialect is correct for SQLAlchemy
if db_url and "postgresql://" in db_url and "postgresql+psycopg2://" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")

try:
    # 3. Create the engine and attempt a connection
    engine = create_engine(db_url)

    with engine.connect() as connection:
        # This simple query just asks the database for the current time
        result = connection.execute(text("SELECT now();"))
        print("✅ Connection Successful!")
        print(f"Database Time: {result.fetchone()[0]}")

except Exception as e:
    print("❌ Connection Failed.")
    print(f"Error: {e}")