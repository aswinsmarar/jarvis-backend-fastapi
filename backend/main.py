# backend/main.py
import os
import requests
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from supabase import create_client

from backend.auth import verify_supabase_token
from backend.iot_tuya import (
    list_devices as tuya_list,
    turn_on,
    turn_off,
    set_brightness,
    router as tuya_router,
)
from backend.models import ChatRequest
from backend.ai import generate_reply

# -------------------- Load Env & Supabase --------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

TUYA_CLIENT_ID = os.getenv("TUYA_CLIENT_ID")
TUYA_CLIENT_SECRET = os.getenv("TUYA_CLIENT_SECRET")
TUYA_ENDPOINT = os.getenv("TUYA_ENDPOINT") or "https://openapi.tuyaeu.com"
OAUTH_REDIRECT_URL = os.getenv("OAUTH_REDIRECT_URL")

# -------------------- Create FastAPI App --------------------
app = FastAPI(title="Jarvis Backend (Gemini + Tuya)")

# CORS (for Flutter app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ for dev (restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Tuya router (optional modular logic)
app.include_router(tuya_router)

# -------------------- Auth Helpers --------------------
def get_current_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return verify_supabase_token(authorization)

def _extract_user_id(current):
    if isinstance(current, dict):
        if "id" in current:
            return current["id"]
        if "user" in current and isinstance(current["user"], dict) and "id" in current["user"]:
            return current["user"]["id"]
    raise HTTPException(status_code=400, detail="Could not determine user id")

# -------------------- Root & Chat --------------------
@app.get("/")
def root():
    return {"ok": True, "msg": "✅ Jarvis backend running successfully"}

@app.post("/chat")
def chat(req: ChatRequest, current=Depends(get_current_user)):
    print(f"💬 Incoming message: {req.message}")
    reply = generate_reply(req.message)
    print(f"💬 Sending reply to Flutter: {reply}")
    return {"reply": reply}

# -------------------- Tuya OAuth --------------------
@app.get("/iot/tuya/login")
def tuya_login(current=Depends(get_current_user)):
    """Redirect user to Tuya Smart Life login page."""
    oauth_url = (
        f"{TUYA_ENDPOINT}/login?"
        f"client_id={TUYA_CLIENT_ID}"
        f"&redirect_uri={OAUTH_REDIRECT_URL}"
        f"&response_type=code"
    )
    return RedirectResponse(url=oauth_url)

@app.get("/iot/tuya/callback")
def tuya_callback(code: str, current=Depends(get_current_user)):
    """Exchange Tuya code for access_token and save in Supabase."""
    token_url = f"{TUYA_ENDPOINT}/v1.0/token?grant_type=authorization_code&code={code}"
    res = requests.post(token_url, auth=(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET))
    data = res.json()
    if "result" not in data:
        return HTMLResponse(
            f"<h3>Authorization failed</h3><pre>{data}</pre>", status_code=400
        )

    result = data["result"]
    uid = result.get("uid")
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")

    user_id = _extract_user_id(current)

    # Store or update in your Supabase table
    sb.table("user_iot_accounts").upsert(
        {
            "user_id": user_id,
            "provider": "tuya",
            "tuya_uid": uid,
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        on_conflict="user_id,provider",
    ).execute()

    return HTMLResponse("<h2>✅ Linked successfully. You can close this window.</h2>")

# -------------------- Devices & Control --------------------
@app.get("/iot/devices")
def get_iot_devices(current=Depends(get_current_user)):
    """List user's connected Tuya devices."""
    user_id = _extract_user_id(current)
    rec = (
        sb.table("user_iot_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", "tuya")
        .single()
        .execute()
    )

    if not rec.data or not rec.data.get("tuya_uid"):
        raise HTTPException(status_code=400, detail="No Tuya account linked")

    devices = tuya_list(rec.data["tuya_uid"])
    return {"devices": devices}

@app.post("/iot/{device_id}/on")
def iot_on(device_id: str, current=Depends(get_current_user)):
    res = turn_on(device_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed"))
    return {"ok": True, "used_code": res.get("code")}

@app.post("/iot/{device_id}/off")
def iot_off(device_id: str, current=Depends(get_current_user)):
    res = turn_off(device_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed"))
    return {"ok": True, "used_code": res.get("code")}

@app.post("/iot/{device_id}/brightness")
def iot_brightness(
    device_id: str, value: int = Query(50, ge=1, le=100), current=Depends(get_current_user)
):
    res = set_brightness(device_id, value)
    return {"raw": res}