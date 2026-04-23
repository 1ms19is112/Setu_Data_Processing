from fastapi import FastAPI
from fastapi.responses import FileResponse  # Import FileResponse
from app.routers import events, transactions, reconciliation

app = FastAPI()

app.include_router(events.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)

@app.get("/")
async def read_index():
    # This serves the HTML file located in the same directory
    return FileResponse('Technical_Specification.html')

@app.get("/health")
def health():
    return {"status": "ok"}