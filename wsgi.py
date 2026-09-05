import os
import sys
from pathlib import Path

# -------------------------------------------------
# 1️⃣ Add the project root to Python's import path
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2] / "pfairga" / "pfairga"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# -------------------------------------------------
# 2️⃣ Load .env (the .env lives in the project root)
# -------------------------------------------------
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")          # reads TELEGRAM_BOT_TOKEN, HTTPS_PROXY, etc.

# -------------------------------------------------
# 3️⃣ Expose the Flask “application” object for the web server
# -------------------------------------------------
from wsgi import application   # <-- our wsgi.py file that imports the Flask app
