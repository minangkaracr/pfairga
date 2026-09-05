import logging
import os
import sys
import tempfile
import fcntl

from app import config
from app.telegram.bot import build_application, set_webhook


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

LOCK_FILE = os.path.join(
    tempfile.gettempdir(),
    "personal_finance_bot.lock"
)


def acquire_lock():
    """Pastikan hanya 1 instance bot yang berjalan di waktu bersamaan."""

    try:
        lock_fd = open(LOCK_FILE, "w")

        # Linux / Unix
        fcntl.flock(
            lock_fd.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

        lock_fd.write(str(os.getpid()))
        lock_fd.flush()

        return lock_fd

    except (IOError, OSError, BlockingIOError):
        logger.error(
            "Bot sudah berjalan di proses lain! "
            "Hanya satu instance yang diperbolehkan. Keluar..."
        )

        print("\n⚠️ ERROR: Bot sudah berjalan di proses lain.")
        print("Hentikan proses lama terlebih dahulu sebelum menjalankan yang baru.\n")

        sys.exit(1)


def main():
    logger.info("Starting Personal Finance AI Assistant Bot...")

    # Pastikan hanya 1 instance berjalan
    lock_fd = acquire_lock()

    if not config.TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set in .env! "
            "Please configure your bot token."
        )

        print("\n⚠️ ERROR: TELEGRAM_BOT_TOKEN missing in .env")
        print(
            "Please copy .env.example to .env and add "
            "your Telegram Bot Token and User ID.\n"
        )

        lock_fd.close()
        return

    try:
        # Build the PTB Application (no polling needed for webhook mode)
        build_application()
        # Register the Telegram webhook (once per deployment)
        set_webhook()
        logger.info("Webhook registered. Bot is now ready to receive updates via Flask endpoint.")

    finally:
        # Lepaskan lock saat bot berhenti
        try:
            fcntl.flock(
                lock_fd.fileno(),
                fcntl.LOCK_UN
            )
            lock_fd.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()