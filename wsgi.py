import os
import sys
from pathlib import Path

# Add project root (the directory containing this wsgi.py) to PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Load environment variables from .env in project root
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

# Expose the Flask application for PythonAnywhere
from webhook.flask_app import app as application
