# Suspicious Word Detector Telegram Bot

A Telegram bot that checks messages against a local word blacklist, classifies message severity with Google Gemini, and records events for a local dashboard.

## Requirements

- Python 3.11 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup on Windows

1. Create and activate a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create your local configuration and add your newly generated credentials to `.env`:

   ```powershell
   Copy-Item .env.example .env
   ```

   ```dotenv
   GEMINI_API_KEY=your_gemini_api_key
   TELEGRAM_TOKEN=your_telegram_bot_token
   ```

4. Start the bot:

   ```powershell
   python main.py
   ```

5. In another terminal, start the dashboard server from the project directory:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python Dashboard_serv.py
   ```

   Open <http://localhost:8000/Dashboard.html>.

The dashboard server exposes message logs without authentication. Keep it local and do not expose port 8000 to the public internet.

## Project files

- `main.py`: Telegram bot and Gemini classification
- `Dashboard_serv.py` and `Dashboard.html`: local event dashboard
- `blacklist.txt`: terms checked locally by the bot
- `events_log.json`: runtime event data; intentionally excluded from Git
- `.env`: local credentials; intentionally excluded from Git