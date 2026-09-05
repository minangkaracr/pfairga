import os
import logging
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application
from app.telegram.bot import build_application

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Initialise PTB Application once
ptb_app: Application = build_application()

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        ptb_app.process_update(update)
        return "OK", 200
    abort(403)

if __name__ == "__main__":
    # For local debugging only – not used on PythonAnywhere
    app.run(host="0.0.0.0", port=8443, debug=True)
