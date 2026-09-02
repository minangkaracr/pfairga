"""
Security and Authorization Module
"""
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from app import config

logger = logging.getLogger(__name__)

def is_user_authorized(user_id: int | str) -> bool:
    """Check if the Telegram user ID matches the authorized whitelist."""
    allowed = config.TELEGRAM_ALLOWED_USER_ID
    if not allowed:
        # If no whitelist is set, allow (with warning)
        logger.warning("TELEGRAM_ALLOWED_USER_ID is not configured in .env! Security check bypassed.")
        return True
    
    # Support comma-separated IDs (e.g. 123456789,987654321)
    allowed_ids = [id_str.strip() for id_str in str(allowed).split(",") if id_str.strip()]
    return str(user_id).strip() in allowed_ids

def restricted(func):
    """Decorator to enforce Telegram User ID whitelist authorization."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if not is_user_authorized(user_id):
            logger.warning(f"Unauthorized access attempt from user_id: {user_id}")
            if update.message:
                await update.message.reply_text("⛔ Akses Ditolak. Sistem ini dikonfigurasi khusus untuk akun pribadi tertentu.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped
