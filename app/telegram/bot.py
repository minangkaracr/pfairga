import logging
import asyncio
import os
from telegram.ext import ContextTypes
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import NetworkError
from app import config
from app.storage.base import BaseStorage
import app.telegram.state as tg_state
from app.sheets.sheets_storage import SheetsStorage
from app.accounting.engine import AccountingEngine
from app.ai.parser import AIParserService
from app.telegram.commands import (
    start_command, setup_command, catat_command, summary_command,
    balance_command, expense_command, income_command, accounts_command,
    debt_command, report_command, help_command, history_command,
    void_command, delete_account_command, edit_balance_command,
    rename_account_command
)
from app.telegram.conversation import handle_natural_language_message

logger = logging.getLogger(__name__)

# Import shared state for tracking proxy failures (already imported at line 10)
# Duplicate import removed

# (flag moved to shared state module)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for PTB.
    Logs the exception and (optionally) notifies the user.
    """
    logger.exception("Unhandled exception in handler")
    # If the exception is a network error, avoid replying (proxy likely down)
    if isinstance(context.error, NetworkError):
        logger.warning("NetworkError encountered – skipping user reply")
        # Record that we had a network/proxy failure so we can notify later
        tg_state.proxy_error_flag = True
        tg_state.last_error_message = str(context.error)
        # Store the chat id that failed so we can notify when back online
        if update and getattr(update, "effective_chat", None):
            tg_state.failed_chats.add(update.effective_chat.id)
        return
    # Otherwise try to notify the user; any failure is logged but ignored
    try:
        if update and getattr(update, "effective_message", None):
            await update.effective_message.reply_text(
                "Maaf, terjadi gangguan jaringan atau internal. Silakan coba lagi nanti."
            )
        # After a successful reply, clear the proxy error flag
        tg_state.proxy_error_flag = False
    except Exception as exc:
        logger.exception("Failed to send error reply to user: %s", exc)

def build_application() -> Application:
    """Builds and configures the Telegram Bot application instance.
    This function returns a PTB Application without starting polling.
    """
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is missing! Bot will not start until configured in .env.")

    # Always use Google Sheets as the single source of truth
    logger.info("Using Google service account file: %s", config.GOOGLE_SERVICE_ACCOUNT_FILE)
    storage = SheetsStorage()

    engine = AccountingEngine(storage)
    ai_parser = AIParserService(storage)

    # Ensure proxy environment variables are set for free PythonAnywhere accounts
    # PythonAnywhere provides an HTTP proxy at http://proxy.server:3128 (or proxy.pythonanywhere.com)
    os.environ.setdefault(
        "HTTP_PROXY", os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or "http://proxy.pythonanywhere.com:3128"
    )
    os.environ.setdefault(
        "HTTPS_PROXY", os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or "http://proxy.pythonanywhere.com:3128"
    )

    # Use the proxy URL from the environment (ApplicationBuilder will use it via .proxy())
    proxy_url = os.getenv("HTTPS_PROXY")
    logger.info("Proxy URL yang dipakai: %s", proxy_url)

    # Build the Telegram Application with optional proxy support (PTB v22 uses .proxy())
    builder = Application.builder().token(token or "DUMMY_TOKEN_FOR_BUILD")
    if proxy_url:
        builder = builder.proxy(proxy_url)
    app = builder.build()
    # Initialization will be performed once in the webhook entry point

    # Add error handler
    app.add_error_handler(error_handler)

    # Share dependencies via bot_data
    app.bot_data["storage"] = storage
    app.bot_data["engine"] = engine
    app.bot_data["ai_parser"] = ai_parser

    # Register Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setup", setup_command))
    app.add_handler(CommandHandler("catat", catat_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("expense", expense_command))
    app.add_handler(CommandHandler("income", income_command))
    app.add_handler(CommandHandler("accounts", accounts_command))
    app.add_handler(CommandHandler("debt", debt_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("void", void_command))
    app.add_handler(CommandHandler("deleteaccount", delete_account_command))
    app.add_handler(CommandHandler("deactivateaccount", delete_account_command))
    app.add_handler(CommandHandler("nonaktif", delete_account_command))
    app.add_handler(CommandHandler("editbalance", edit_balance_command))
    app.add_handler(CommandHandler("renameaccount", rename_account_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("help", help_command))

    # Register Natural Language Handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_language_message))

    return app


def set_webhook():
    """Utility to register the Telegram webhook.
    Call this once after the web app is deployed (or via a scheduled task).
    """
    from urllib.parse import urljoin
    token = config.TELEGRAM_BOT_TOKEN
    # Build base URL – PythonAnywhere provides HTTPS automatically
    username = os.getenv('PYTHONANYWHERE_USERNAME') or os.getenv('USER')
    base_url = f"https://{username}.pythonanywhere.com"
    webhook_url = urljoin(base_url + '/', 'webhook')
    logger.info("Setting Telegram webhook to %s", webhook_url)
    # Use a temporary Application just to get the Bot instance
    bot_app = (
        Application.builder()
        .token(token)
        .build()
    )
    import asyncio
    async def _register():
        await bot_app.bot.set_webhook(url=webhook_url)
    asyncio.run(_register())
