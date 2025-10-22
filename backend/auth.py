import os
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi import HTTPException, Header

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def verify_supabase_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]

    try:
        user = sb.auth.get_user(token)
        if not user or (hasattr(user, "user") and not user.user):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user.user if hasattr(user, "user") else user
    except Exception as e:
        print("verify token error:", e)
        raise HTTPException(status_code=401, detail="Token verification failed")