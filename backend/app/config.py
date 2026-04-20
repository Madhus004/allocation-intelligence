import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
    raise ValueError("OPENAI_API_KEY is missing or still set to placeholder in backend/.env")

print(f"Loaded OPENAI_API_KEY ending with: {OPENAI_API_KEY[-6:]}")