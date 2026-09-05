import os
import logging
from flask import Flask, request, abort
from telegram import Update
import asyncio
from app.telegram.bot import build_application

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Initialise PTB Application once
ptb_app = build_application()
# Initialise the PTB Application (load handlers, start bot, etc.)
asyncio.run(ptb_app.initialize())

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("Webhook request received")
    try:
        # Parse incoming Telegram update
        update_json = request.get_json(force=True)
        logger.debug("Received webhook update: %s", update_json)
        update = Update.de_json(update_json, ptb_app.bot)
        # Process the update (PTB process_update is async)
        asyncio.run(ptb_app.process_update(update))
    except Exception as e:
        logger.exception("Error processing webhook update: %s", e)
        abort(500)
    return "OK", 200

if __name__ == "__main__":
    # Local debugging only
    app.run(host="0.0.0.0", port=8443, debug=True)
