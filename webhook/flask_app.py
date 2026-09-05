import os
import app.telegram.state as tg_state
import logging
from flask import Flask, request, abort
from telegram import Update
import asyncio
# Create a single event loop that will live for the lifetime of the Flask process.
# PTB's internal async client will keep references to this loop, so we must not close it
_event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_event_loop)
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
        # Ensure the application is initialized (only once per process)
        if not getattr(ptb_app, "initialized", False):
            async def _init_and_process(update_json):
                await ptb_app.initialize()
                update = Update.de_json(update_json, ptb_app.bot)
                await ptb_app.process_update(update)
                return True
            update_json = request.get_json(force=True)
            logger.debug("Received webhook update: %s", update_json)
            _event_loop.run_until_complete(_init_and_process(update_json))
        else:
            update_json = request.get_json(force=True)
            logger.debug("Received webhook update: %s", update_json)
            update = Update.de_json(update_json, ptb_app.bot)
            _event_loop.run_until_complete(ptb_app.process_update(update))
    except Exception as e:
        logger.exception("Error processing webhook update: %s", e)
        # Capture network/proxy failures for later user notification
        if isinstance(e, Exception) and ('ProxyError' in str(e) or 'NetworkError' in str(e)):
            tg_state.proxy_error_flag = True
            tg_state.last_error_message = str(e)
            # Attempt to extract chat ID from the incoming update for later notification
            try:
                update_json = request.get_json(force=True)
                chat_id = update_json.get('message', {}).get('chat', {}).get('id')
                if chat_id:
                    tg_state.failed_chats.add(chat_id)
            except Exception:
                pass
        abort(500)

    return "OK", 200

# ── Local debugging ───────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443, debug=True)
