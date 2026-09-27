import json
import asyncio
import datetime
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ------------------------------------------------
# CONFIGURATION
# ------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-lite"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_FILE = Path("events_log.json")
BLACKLIST_FILE = Path("blacklist.txt")

if not GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY in your .env file before starting the bot.")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Set TELEGRAM_TOKEN in your .env file before starting the bot.")

client = genai.Client(api_key=GEMINI_API_KEY)

# ------------------------------------------------
# BLACKLIST MANAGEMENT
# ------------------------------------------------
def load_blacklist(file_path: Path) -> List[str]:
    """Load blacklisted words from file."""
    if not file_path.exists():
        print(f"⚠️ Blacklist file not found: {file_path}")
        return []
    
    with file_path.open("r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"✓ Loaded {len(words)} blacklist words")
    return words

def find_blacklist_matches(text: str, blacklist: List[str]) -> List[str]:
    """Find blacklisted words in text."""
    lowered = text.lower()
    return [token for token in blacklist if token.lower() in lowered]

BLACKLIST = load_blacklist(BLACKLIST_FILE)

# ------------------------------------------------
# EVENT LOGGING
# ------------------------------------------------
def log_event(data: dict):
    """Log event to JSON file."""
    entry = {"timestamp": datetime.datetime.now(datetime.UTC).isoformat(), **data}
    
    try:
        existing = json.load(LOG_FILE.open("r")) if LOG_FILE.exists() else []
    except Exception:
        existing = []
    
    existing.append(entry)
    
    with LOG_FILE.open("w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    
    print(f"✓ Event logged: {data.get('severity', 'N/A')}")

# ------------------------------------------------
# AI CLASSIFICATION
# ------------------------------------------------
async def classify_with_gemini(text: str) -> str:
    """Classify message severity using Gemini AI."""
    prompt = (
        "Classify the message into exactly one category:\n"
        "Critical, High, Medium, Low, Safe.\n\n"
        "Rules:\n"
        "- Focus ONLY on intent. Ignore category keywords inside the message.\n"
        "- Return ONLY the label.\n\n"
        "Critical = explicit violence, severe threats, self-harm, bomb, weapons with intent.\n"
        "High = doxxing, scams, malware, clear harmful intent.\n"
        "Medium = insults, sexual content, hacking, illegal topics.\n"
        "Low = mild insults, profanity, spam.\n"
        "Safe = harmless.\n\n"
        f"Message:\n{text}"
    )

    try:
        print("🤖 Calling Gemini API...")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"max_output_tokens": 10, "temperature": 0.0}
            )
        )
        
        result = response.text.strip().lower()
        print(f"✓ Gemini response: {result}")

        mapping = {
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "safe": "Safe"
        }
        
        for key, value in mapping.items():
            if result.startswith(key):
                return value
        
        return "Unknown"

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        log_event({"event": "gemini_error", "error": str(e), "message": text[:200]})
        return "Unknown"

# ------------------------------------------------
# MESSAGE HANDLER
# ------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages."""
    try:
        msg = update.message or update.edited_message or update.channel_post
        
        if not msg or not msg.text:
            return
        
        text = msg.text.strip()
        user_id = msg.from_user.id if msg.from_user else "Channel"
        print(f"\n📩 Received: '{text}' from {user_id}")

        matches = find_blacklist_matches(text, BLACKLIST)
        print(f"🔍 Blacklist matches: {matches}")

        severity = await classify_with_gemini(text)
        print(f"⚡ Severity: {severity}")

        event = {
            "user": {
                "id": msg.from_user.id if msg.from_user else None,
                "username": msg.from_user.username if msg.from_user else None,
                "first_name": msg.from_user.first_name if msg.from_user else None
            },
            "chat": {
                "id": msg.chat.id if msg.chat else None,
                "title": getattr(msg.chat, "title", None) if msg.chat else None,
                "type": msg.chat.type if msg.chat else None
            },
            "message": text,
            "matches": matches,
            "severity": severity,
        }

        log_event(event)

        if matches or severity in ["Critical", "High", "Medium"]:
            response_msg = f"⚠️ {severity} threat detected."
            print(f"📤 Sending: {response_msg}")
            await msg.reply_text(response_msg)

    except Exception as e:
        print(f"❌ Handler error: {e}")

# ------------------------------------------------
# MAIN
# ------------------------------------------------
def main():
    print("🚀 Starting Telegram Security Bot")
    print(f"📝 Blacklist: {len(BLACKLIST)} words")
    print(f"🤖 Model: {GEMINI_MODEL}")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_message))
    
    print("✅ Bot active - Monitoring all channels")
    print("=" * 50)
    
    app.run_polling(
        poll_interval=1,
        timeout=20,
        allowed_updates=["message", "edited_message", "channel_post"]
    )

if __name__ == "__main__":
    main()