from fastapi import FastAPI
from app.routers import wallets

app = FastAPI(debug=True)
app.include_router(wallets.router)