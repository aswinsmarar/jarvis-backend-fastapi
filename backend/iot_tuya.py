# backend/iot_tuya.py
import os
import requests
from fastapi import APIRouter
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/iot/tuya", tags=["IoT - Tuya"])

TUYA_ENDPOINT = os.getenv("TUYA_ENDPOINT")
TUYA_CLIENT_ID = os.getenv("TUYA_CLIENT_ID")
TUYA_CLIENT_SECRET = os.getenv("TUYA_CLIENT_SECRET")

# In-memory placeholder for access token
ACCESS_TOKEN = None


def _get_access_token():
    """Retrieve a valid Tuya cloud token."""
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    url = f"{TUYA_ENDPOINT}/v1.0/token?grant_type=1"
    res = requests.get(url, auth=(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET))
    data = res.json()

    if "result" in data:
        ACCESS_TOKEN = data["result"]["access_token"]
        return ACCESS_TOKEN
    raise Exception(f"Failed to get token: {data}")


def list_devices(uid: str):
    """Get all devices linked to this user UID."""
    token = _get_access_token()
    url = f"{TUYA_ENDPOINT}/v1.0/users/{uid}/devices"
    res = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    data = res.json()
    return data.get("result", [])


def turn_on(device_id: str):
    """Turn a Tuya device ON."""
    token = _get_access_token()
    url = f"{TUYA_ENDPOINT}/v1.0/devices/{device_id}/commands"
    payload = {"commands": [{"code": "switch_led", "value": True}]}
    res = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
    return {"success": res.status_code == 200, "code": "switch_led"}


def turn_off(device_id: str):
    """Turn a Tuya device OFF."""
    token = _get_access_token()
    url = f"{TUYA_ENDPOINT}/v1.0/devices/{device_id}/commands"
    payload = {"commands": [{"code": "switch_led", "value": False}]}
    res = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
    return {"success": res.status_code == 200, "code": "switch_led"}


def set_brightness(device_id: str, value: int):
    """Adjust brightness (1–100)."""
    token = _get_access_token()
    url = f"{TUYA_ENDPOINT}/v1.0/devices/{device_id}/commands"
    payload = {"commands": [{"code": "bright_value_v2", "value": value}]}
    res = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
    return res.json()

def _get_access_token():
    """Retrieve and cache Tuya Cloud token."""
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    url = f"{TUYA_ENDPOINT}/v1.0/token?grant_type=1"
    res = requests.get(url, auth=(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET))
    data = res.json()

    print("🔑 Tuya token response:", data)

    if "result" in data:
        ACCESS_TOKEN = data["result"]["access_token"]
        return ACCESS_TOKEN

    raise Exception(f"Failed to get token: {data}")