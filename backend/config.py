"""Environment configuration for Second Brain."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model Configuration
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

# Paths
BASE_DIR = Path(__file__).parent.parent
VAULT_PATH = Path(os.getenv("VAULT_PATH", BASE_DIR / "vault"))
PROMPTS_PATH = BASE_DIR / "backend" / "prompts"

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))

# Classification
CONFIDENCE_THRESHOLD = 0.6

# Vault Categories
VAULT_CATEGORIES = ["People", "Projects", "Ideas", "Admin", "InboxLog", "_digests"]
