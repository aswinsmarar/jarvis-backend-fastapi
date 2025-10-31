import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

from backend.auth import verify_supabase_token
from backend.models import ChatRequest
from backend.ai import generate_reply

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

app = FastAPI(title="Jarvis Backend (AI Assistant)")

# Allow requests from Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict later in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- AUTH VERIFICATION ----------------
def get_current_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return verify_supabase_token(authorization)


# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"ok": True, "msg": "✅ Jarvis backend running successfully"}


# ---------------- CHAT ----------------
@app.post("/chat")
def chat(req: ChatRequest, current=Depends(get_current_user)):
    print(f"💬 Incoming message: {req.message}")
    reply = generate_reply(req.message)
    print(f"🤖 Jarvis reply: {reply}")
    return {"reply": reply}