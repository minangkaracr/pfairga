import logging
import os
import sys
import tempfile
from app import config
from app.telegram.bot import create_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

LOCK_FILE = os.path.join(tempfile.gettempdir(), "personal_finance_bot.lock")

def acquire_lock():
    """Pastikan hanya 1 instance bot yang berjalan di waktu bersamaan."""
    import msvcrt
    try:
        lock_fd = open(LOCK_FILE, "w")
        msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        return lock_fd  # Kembalikan file handle agar lock tetap aktif
    except (IOError, OSError):
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
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env! Please configure your bot token.")
        print("\n⚠️ ERROR: TELEGRAM_BOT_TOKEN missing in .env")
        print("Please copy .env.example to .env and add your Telegram Bot Token and User ID.\n")
        lock_fd.close()
        return

    try:
        app = create_app()
        logger.info("Bot started successfully! Waiting for messages...")
        app.run_polling()
    finally:
        # Hapus lock file saat bot berhenti
        try:
            lock_fd.close()
            os.remove(LOCK_FILE)
        except Exception:
            pass

if __name__ == "__main__":
    main()
