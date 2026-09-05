import os
import sys

# Add project directory to PYTHONPATH for WSGI
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from webhook.flask_app import app as application  # noqa: F401
