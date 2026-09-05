import os
import logging
from flask import Flask, request, abort
from telegram import Update
import asyncio
from app.telegram.bot import build_application

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Global placeholder – no global statement at module level
ptb_app = None

# ── Health check (never touches PTB) ───────────────────────
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# ── Webhook entry point ───────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    logger.info("Webhook request received")
    global ptb_app
    try:
        # Initialise the PTB Application if it hasn't been created yet
        if ptb_app is None:
            ptb_app = build_application()
    except Exception as e:
        logger.exception("Failed to initialise Telegram app: %s", e)
        abort(500)

    try:
        update_json = request.get_json(force=True)
        logger.debug("Received webhook update: %s", update_json)
        update = Update.de_json(update_json, ptb_app.bot)
        asyncio.run(ptb_app.process_update(update))
    except Exception as e:
        logger.exception("Error processing webhook update: %s", e)
        abort(500)

    return "OK", 200

# ── Local debugging ───────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443, debug=True)
