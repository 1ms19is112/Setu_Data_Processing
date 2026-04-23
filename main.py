from fastapi import FastAPI
from app.routers import events, transactions, reconciliation

app = FastAPI()

app.include_router(events.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)

@app.get("/health")
def health():
    return {"status": "ok"}