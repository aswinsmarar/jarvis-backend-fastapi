import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 🧠 System prompt – controls the assistant’s personality
JARVIS_PROMPT = """
You are Jarvis — a calm, intelligent AI assistant inspired by Iron Man’s AI.
Your tone should be confident, respectful, and witty but never arrogant.
Keep responses concise, clear, and human-like.
If the user asks something you don’t know, admit it politely and suggest what you *can* do.
Always address the user directly.
"""

def generate_reply(text: str) -> str:
    """
    Generate a Jarvis-style reply using Gemini 2.5 Flash.
    Fallback to rule-based replies if API fails.
    """
    print(f"💬 Incoming message: {text}")

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = f"{JARVIS_PROMPT}\n\nUser: {text}\nJarvis:"

        print(f"🧠 Using model: {model.model_name}")
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            print(f"🤖 Gemini reply: {response.text}")
            return response.text.strip()

        print("⚠️ Empty response from Gemini.")
        return "I'm processing that, sir."

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        t = text.lower()
        if "turn on" in t and "light" in t:
            return "✅ Simulated: turning on the light, sir."
        if "turn off" in t and "light" in t:
            return "✅ Simulated: turning off the light, sir."
        if "hello" in t or "hi" in t:
            return "Hello, sir. How can I assist you today?"
        return "Apologies, sir — I couldn’t connect to Gemini right now."