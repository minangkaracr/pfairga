import uuid
import logging
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes
from app.security.auth import restricted
from app.accounting.models import Transaction, TransactionType, TransactionStatus
from app.accounting.engine import AccountingEngine
from app.ai.parser import AIParserService
from app.storage.base import BaseStorage
from app.telegram.state import proxy_error_flag, failed_chats

logger = logging.getLogger(__name__)

# User context state for clarification dialogs
user_dialog_state = {}

@restricted
async def handle_natural_language_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If a previous network error prevented a reply and connection is now restored, notify the user with error details
    chat = getattr(update, "effective_chat", None)
    if chat:
        chat_id = chat.id
        if proxy_error_flag and chat_id in failed_chats:
            # Include the stored error message for transparency
            error_msg = tg_state.last_error_message or "(tidak ada detail)"
            await update.message.reply_text(
                f"🔔 Koneksi ke server sudah pulih. Sebelumnya ada gangguan jaringan: {error_msg}."
            )
            failed_chats.remove(chat_id)
            # Reset the shared flags
            tg_state.proxy_error_flag = False
            tg_state.last_error_message = ""

    user_text = update.message.text.strip()
    user_id = update.effective_user.id

    storage: BaseStorage = context.bot_data["storage"]
    engine: AccountingEngine = context.bot_data["engine"]
    ai_parser: AIParserService = context.bot_data["ai_parser"]

    # 1. Check for direct setup / balance adjustment commands (e.g. "Setup BRI 468104" or "set saldo GoPay 500000")
    normalized_text = user_text.lstrip('/').strip().lower()
    if normalized_text.startswith("setup") or normalized_text.startswith("set saldo") or normalized_text.startswith("saldo awal"):
        parts = user_text.split()
        if len(parts) >= 3:
            acc_name = " ".join(parts[1:-1]).strip()
            raw_amt = parts[-1].replace(".", "").replace(",", "").strip()
            try:
                amt = float(raw_amt)
                acc = engine.edit_account_balance(acc_name, amt, reason="Initial setup balance")
                msg = (
                    f"⚙️ <b>Setup Saldo Berhasil</b>\n\n"
                    f"🏦 <b>Account:</b> {acc.account_name}\n"
                    f"💵 <b>Saldo Terpasang:</b> Rp{acc.current_balance:,.0f}\n\n"
                    f"✅ <i>Saldo telah diperbarui di Google Sheets dan Neraca Keuangan.</i>"
                )
                await update.message.reply_html(msg)
                return
            except Exception as e:
                await update.message.reply_html(f"❌ Gagal melakukan setup saldo: {e}")
                return
        elif len(parts) == 2:
            await update.message.reply_html(
                "⚠️ <b>Format Setup Saldo:</b>\n"
                "<code>Setup NAMA_ACCOUNT NOMINAL</code>\n"
                "<i>Contoh:</i> <code>Setup BRI 468104</code>\n"
                "<i>Contoh:</i> <code>Setup GoPay 500000</code>"
            )
            return
        parts = user_text.split()
        if len(parts) >= 3:
            acc_name = " ".join(parts[1:-1]).strip()
            raw_amt = parts[-1].replace(".", "").replace(",", "").strip()
            try:
                amt = float(raw_amt)
                acc = engine.edit_account_balance(acc_name, amt, reason="Initial setup balance")
                msg = (
                    f"⚙️ <b>Setup Saldo Berhasil</b>\n\n"
                    f"🏦 <b>Account:</b> {acc.account_name}\n"
                    f"💵 <b>Saldo Terpasang:</b> Rp{acc.current_balance:,.0f}\n\n"
                    f"✅ <i>Saldo telah diperbarui di Google Sheets dan Neraca Keuangan.</i>"
                )
                await update.message.reply_html(msg)
                return
            except Exception as e:
                await update.message.reply_html(f"❌ Gagal melakukan setup saldo: {e}")
                return
        elif len(parts) == 2:
            await update.message.reply_html(
                "⚠️ <b>Format Setup Saldo:</b>\n"
                "<code>Setup NAMA_ACCOUNT NOMINAL</code>\n"
                "<i>Contoh:</i> <code>Setup BRI 468104</code>\n"
                "<i>Contoh:</i> <code>Setup GoPay 500000</code>"
            )
            return

    # 2. Check if user is in an ongoing clarification dialog
    if user_id in user_dialog_state:
        state = user_dialog_state.pop(user_id)
        pending_item = state["pending_item"]
        missing_field = state["missing_field"]

        if missing_field == "account":
            pending_item.account = user_text
        elif missing_field == "useful_life":
            try:
                pending_item.useful_life_years = float(user_text.replace("tahun", "").strip())
            except ValueError:
                pending_item.useful_life_years = 5.0

        # Now post the transaction
        tx = _post_parsed_item(engine, pending_item)
        await update.message.reply_html(_format_success_message(tx, engine, storage))
        return

    # 2. Parse natural language message via AI Service
    today_str = date.today().strftime("%Y-%m-%d")
    result = ai_parser.parse_user_message(user_text, target_date=today_str)

    if not result.is_financial_transaction or not result.items:
        await update.message.reply_text("💡 Saya tidak menemukan instruksi transaksi keuangan pada pesan ini. Ketik /help untuk panduan.")
        return

    # 3. Check for missing critical fields (Confirmation / Clarification dialog BRD §28, §80)
    if result.missing_critical_fields:
        missing_field = result.missing_critical_fields[0]
        pending_item = result.items[0]
        user_dialog_state[user_id] = {
            "pending_item": pending_item,
            "missing_field": missing_field
        }
        prompt = result.clarification_prompt or f"Informasi {missing_field} belum lengkap. Mohon berikan rinciannya:"
        await update.message.reply_text(prompt)
        return

    # 4. Post parsed transactions
    success_msgs = []
    for item in result.items:
        tx = _post_parsed_item(engine, item)
        success_msgs.append(_format_success_message(tx, engine, storage))

    await update.message.reply_html("\n\n".join(success_msgs))

def _post_parsed_item(engine: AccountingEngine, item) -> Transaction:
    tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
    tx = Transaction(
        transaction_id=tx_id,
        transaction_date=item.transaction_date,
        recorded_at=date.today().strftime("%Y-%m-%d"),
        type=item.transaction_type,
        description=item.description,
        amount=item.amount,
        account=item.account or "GoPay",
        destination_account=item.destination_account,
        category=item.category,
        status=TransactionStatus.POSTED
    )
    return engine.post_transaction(tx, reason="Natural language entry")

def _format_success_message(tx: Transaction, engine: AccountingEngine, storage: BaseStorage) -> str:
    acc_obj = storage.get_account_by_name(tx.account)
    acc_bal = acc_obj.current_balance if acc_obj else 0.0

    if tx.type == TransactionType.TRANSFER:
        dest_obj = storage.get_account_by_name(tx.destination_account) if tx.destination_account else None
        dest_bal = dest_obj.current_balance if dest_obj else 0.0
        return (
            f"✅ <b>Transfer Berhasil Dicatat</b>\n\n"
            f"↔️ <b>{tx.account} → {tx.destination_account}</b>\n"
            f"💵 Rp{tx.amount:,.0f}\n"
            f"📅 Tanggal: {tx.transaction_date}\n\n"
            f"💳 Saldo {tx.account}: Rp{acc_bal:,.0f}\n"
            f"💳 Saldo {tx.destination_account}: Rp{dest_bal:,.0f}"
        )
    elif tx.type == TransactionType.INCOME:
        return (
            f"✅ <b>Pemasukan Berhasil Dicatat</b>\n\n"
            f"📥 <b>{tx.category}</b> — {tx.description}\n"
            f"💵 Rp{tx.amount:,.0f}\n"
            f"🏦 Account: {tx.account}\n"
            f"📅 Tanggal: {tx.transaction_date}\n\n"
            f"💳 Saldo {tx.account}: Rp{acc_bal:,.0f}"
        )
    elif tx.type == TransactionType.ASSET_ACQUISITION:
        return (
            f"✅ <b>Pembelian Aset Berhasil Dicatat</b>\n\n"
            f"📦 <b>{tx.description}</b> ({tx.category})\n"
            f"💵 Nilai Aset: Rp{tx.amount:,.0f}\n"
            f"🏦 Dibayar dari: {tx.account}\n"
            f"📅 Tanggal: {tx.transaction_date}\n\n"
            f"ℹ️ <i>Aset ini akan didepresiasi secara otomatis pada laporan neraca.</i>"
        )
    else:
        return (
            f"✅ <b>Pengeluaran Berhasil Dicatat</b>\n\n"
            f"🏷️ <b>{tx.category}</b> — {tx.description}\n"
            f"💵 Rp{tx.amount:,.0f}\n"
            f"🏦 Account: {tx.account}\n"
            f"📅 Tanggal: {tx.transaction_date}\n\n"
            f"💳 Saldo {tx.account}: Rp{acc_bal:,.0f}"
        )
