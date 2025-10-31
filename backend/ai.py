# backend/ai.py
import os
import requests
from dotenv import load_dotenv
from backend.ai import generate_reply

load_dotenv()

# 🔑 Your Hugging Face API Key (set in .env)
HF_API_TOKEN = os.getenv("HF_API_KEY")

# 🧠 Model — You can change this later to a larger one
MODEL = "google/flan-t5-base"

# 🎙️ System prompt (Jarvis personality)
JARVIS_PROMPT = """
You are Jarvis — a calm, intelligent, and loyal AI assistant inspired by Iron Man.
Your tone should be confident, concise, and slightly witty.
If the user asks something unclear, ask for clarification politely.
"""

def generate_reply(text: str) -> str:
    """Generate a Jarvis-style reply using Hugging Face Inference API."""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": f"{JARVIS_PROMPT}\n\nUser: {text}\nJarvis:",
        "parameters": {
            "max_new_tokens": 120,
            "temperature": 0.7,
            "do_sample": True
        },
    }

    try:
        res = requests.post(
            f"https://api-inference.huggingface.co/models/{MODEL}",
            headers=headers,
            json=payload,
            timeout=30,
        )
        res.raise_for_status()
        data = res.json()

        # Hugging Face API returns a list of outputs
        if isinstance(data, list) and len(data) and "generated_text" in data[0]:
            reply = data[0]["generated_text"].split("Jarvis:")[-1].strip()
            print(f"🤖 Jarvis reply: {reply}")
            return reply

        print("⚠️ Unexpected HF response:", data)
        return "I'm processing that, sir."

    except Exception as e:
        print(f"❌ Hugging Face API error: {e}")
        return "Apologies, sir — I ran into an issue while thinking."