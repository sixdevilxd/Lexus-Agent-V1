import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CONDUIT_API_KEY = os.getenv("CONDUIT_API_KEY")

# OpenAI-compatible base URL (must include /api/v1)
CONDUIT_BASE_URL = os.getenv("CONDUIT_BASE_URL", "https://conduit.ozdoev.net/api/v1")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-6")

MAX_HISTORY = int(os.getenv("MAX_HISTORY", "10"))
STREAM_ENABLED = os.getenv("STREAM_ENABLED", "true").lower() == "true"

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing! Please set it in your .env file.")
if not CONDUIT_API_KEY:
    raise ValueError("CONDUIT_API_KEY is missing! Please set it in your .env file.")
