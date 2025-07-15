from fastapi import FastAPI
from routes_chat import router as chat_router
from routes_contract import router as contract_router
from routes_audit import router as audit_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MetaDAG backend is running!"}

app.include_router(chat_router)
app.include_router(contract_router)
app.include_router(audit_router) 