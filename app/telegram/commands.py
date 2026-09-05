import os
import tempfile
from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes
from app.security.auth import restricted
from app.accounting.engine import AccountingEngine
from app.accounting.statements import FinancialStatementGenerator
from app.reporting.pdf_generator import PDFReportGenerator
from app.storage.base import BaseStorage
from app.accounting.models import Account, AccountType, Transaction, TransactionType, TransactionStatus

def get_helpers(context: ContextTypes.DEFAULT_TYPE):
    storage: BaseStorage = context.bot_data["storage"]
    engine: AccountingEngine = context.bot_data["engine"]
    statement_gen = FinancialStatementGenerator(storage)
    pdf_gen = PDFReportGenerator(storage)
    return storage, engine, statement_gen, pdf_gen

@restricted
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 <b>Selamat Datang di Personal Finance AI Assistant!</b>\n\n"
        "Saya adalah asisten keuangan pribadi Anda. Anda dapat mencatat transaksi keuangan hanya dengan berbicara secara natural.\n\n"
        "<b>Contoh Input Natural:</b>\n"
        "• <i>\"Tadi makan 35 ribu pakai GoPay\"</i>\n"
        "• <i>\"Top up GoPay 500 ribu dari BRI\"</i>\n"
        "• <i>\"Gaji bulan ini 10 juta masuk BRI\"</i>\n"
        "• <i>\"Beli laptop 15 juta dari BRI\"</i>\n"
        "• <i>\"Bayar kartu kredit 2 juta dari BRI\"</i>\n\n"
        "Gunakan /help untuk melihat daftar perintah dan /summary untuk ringkasan bulan ini."
    )
    await update.message.reply_html(msg)

@restricted
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, _, _ = get_helpers(context)
    accounts = storage.get_all_accounts()
    
    msg = (
        "⚙️ <b>Financial Initial Setup Wizard</b>\n\n"
        "Daftar Rekening / Account Anda saat ini:\n"
    )
    for acc in accounts:
        msg += f"• <b>{acc.account_name}</b> ({acc.account_type.value}): Rp{acc.current_balance:,.0f}\n"

    msg += (
        "\nUntuk menambah atau mengubah saldo awal account, ketik format:\n"
        "<code>Setup [Nama Account] [Saldo Awal]</code>\n"
        "Contoh: <code>Setup BRI 10000000</code>"
    )
    await update.message.reply_html(msg)

@restricted
async def catat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📝 <b>Panduan Pencatatan Transaksi</b>\n\n"
        "Anda tidak perlu menggunakan format kaku. Langsung saja kirim pesan seperti:\n"
        "1. <i>\"Makan siang 25 ribu dari Cash\"</i>\n"
        "2. <i>\"Transfer 200 ribu dari BCA ke GoPay\"</i>\n"
        "3. <i>\"Beli sepatu 500 ribu pakai BRI Credit Card\"</i>\n\n"
        "Atau jika ingin terstruktur:\n"
        "<code>Catat [Tipe] [Jumlah] [Account] [Kategori] [Deskripsi]</code>"
    )
    await update.message.reply_html(msg)

@restricted
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, statement_gen, _ = get_helpers(context)
    
    # Calculate period: 25th of previous month to 24th of current month
    today = date.today()
    # End date is the 24th of the current month
    end_date_obj = date(today.year, today.month, 24)
    # Start date is the 25th of the previous month
    if end_date_obj.month == 1:
        start_year = end_date_obj.year - 1
        start_month = 12
    else:
        start_year = end_date_obj.year
        start_month = end_date_obj.month - 1
    start_date_obj = date(start_year, start_month, 25)
    start_date = start_date_obj.strftime("%Y-%m-%d")
    end_date = end_date_obj.strftime("%Y-%m-%d")

    inc_stmt = statement_gen.generate_income_statement(start_date, end_date)
    bs = statement_gen.generate_balance_sheet()

    month_name = end_date_obj.strftime("%B %Y")  # Use ending month for label
    integrity_icon = "✅" if bs["is_balanced"] else "⚠️"

    msg = (
        f"📊 <b>Ringkasan Keuangan — {month_name}</b>\n"
        f"   (Periode {start_date_obj.strftime('%d %b %Y')} - {end_date_obj.strftime('%d %b %Y')})\n\n"
        f"💰 <b>Total Pemasukan:</b> Rp{inc_stmt['total_income']:,.0f}\n"
        f"💸 <b>Total Pengeluaran:</b> Rp{inc_stmt['total_expense']:,.0f}\n"
        f"📈 <b>Net Income:</b> Rp{inc_stmt['net_income']:,.0f}\n\n"
        f"🏛️ <b>Total Aset:</b> Rp{bs['assets']['total_assets']:,.0f}\n"
        f"💳 <b>Total Liabilitas:</b> Rp{bs['liabilities']['total_liabilities']:,.0f}\n"
        f"💎 <b>Net Worth:</b> Rp{bs['net_worth']:,.0f}\n\n"
        f"{integrity_icon} <b>Integritas Neraca:</b> {'Balanced' if bs['is_balanced'] else 'Discrepancy Warning'}"
    )
    await update.message.reply_html(msg)

@restricted
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, statement_gen, _ = get_helpers(context)
    bs = statement_gen.generate_balance_sheet()
    ast = bs["assets"]
    lia = bs["liabilities"]
    eq = bs["equity"]

    # Build assets section
    assets_section = (
        "<b>ASSETS</b>\n"
        f"• Cash & Bank: Rp{ast['cash_bank']:,.0f}\n"
        f"• E-Wallet: Rp{ast['ewallet']:,.0f}\n"
        f"• Prepaid Balance: Rp{ast['prepaid']:,.0f}\n"
        f"• Investasi: Rp{ast['investment']:,.0f}\n"
    )
    if ast['fixed_assets_nbv'] > 0:
        assets_section += f"• Aset Tetap (NBV): Rp{ast['fixed_assets_nbv']:,.0f}\n"
    assets_section += f"<b>TOTAL ASSETS: Rp{ast['total_assets']:,.0f}</b>\n"

    # Build equity section
    equity_section = (
        "<b>EQUITY</b>\n"
        f"• Modal Awal: Rp{eq['opening_equity']:,.0f}\n"
        f"• Akumulasi Net Income: Rp{eq['accumulated_net_income']:,.0f}\n"
    )
    adj = eq.get('equity_adjustment', 0.0)
    if abs(adj) >= 1.0:
        equity_section += f"• Penyesuaian Saldo: Rp{adj:,.0f}\n"
    equity_section += f"<b>TOTAL EQUITY: Rp{eq['total_equity']:,.0f}</b>\n"

    integrity_note = ""
    if not bs['is_balanced']:
        integrity_note = f"\n⚠️ <i>Discrepancy: Rp{bs['discrepancy']:,.0f}</i>"

    msg = (
        "⚖️ <b>Laporan Neraca Keuangan (Balance Sheet)</b>\n\n"
        + assets_section
        + "\n<b>LIABILITIES</b>\n"
        f"• Kartu Kredit: Rp{lia['credit_card']:,.0f}\n"
        f"• Cicilan & Pinjaman: Rp{lia['installments'] + lia['loans']:,.0f}\n"
        f"<b>TOTAL LIABILITIES: Rp{lia['total_liabilities']:,.0f}</b>\n\n"
        + equity_section
        + f"\n💎 <b>NET WORTH: Rp{bs['net_worth']:,.0f}</b>"
        + integrity_note
    )
    await update.message.reply_html(msg)

@restricted
async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, statement_gen, _ = get_helpers(context)
    today = date.today()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    inc_stmt = statement_gen.generate_income_statement(start_date, end_date)
    expenses = inc_stmt["expense_by_category"]

    msg = f"📉 <b>Rincian Pengeluaran — {today.strftime('%B %Y')}</b>\n\n"
    if not expenses:
        msg += "Belum ada pengeluaran yang dicatat bulan ini."
    else:
        for cat, amt in expenses.items():
            msg += f"• <b>{cat}:</b> Rp{amt:,.0f}\n"
        msg += f"\n<b>Total Pengeluaran: Rp{inc_stmt['total_expense']:,.0f}</b>"

    await update.message.reply_html(msg)

@restricted
async def income_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, statement_gen, _ = get_helpers(context)
    today = date.today()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    inc_stmt = statement_gen.generate_income_statement(start_date, end_date)
    incomes = inc_stmt["income_by_category"]

    msg = f"📈 <b>Rincian Pemasukan — {today.strftime('%B %Y')}</b>\n\n"
    if not incomes:
        msg += "Belum ada pemasukan yang dicatat bulan ini."
    else:
        for cat, amt in incomes.items():
            msg += f"• <b>{cat}:</b> Rp{amt:,.0f}\n"
        msg += f"\n<b>Total Pemasukan: Rp{inc_stmt['total_income']:,.0f}</b>"

    await update.message.reply_html(msg)

@restricted
async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, _, _, _ = get_helpers(context)
    accounts = storage.get_all_accounts()

    # Filter only Active accounts
    active_accounts = [acc for acc in accounts if acc.status == "Active"]

    # Group by account type
    from collections import defaultdict
    grouped = defaultdict(list)
    for acc in active_accounts:
        grouped[acc.account_type].append(acc)

    msg = "💳 <b>Saldo Rekening & Account</b>\n\n"
    total_acc = 0.0

    # Sort account types alphabetically based on their value
    sorted_types = sorted(grouped.keys(), key=lambda t: t.value.lower() if hasattr(t, 'value') else str(t).lower())

    for acc_type in sorted_types:
        type_label = acc_type.value if hasattr(acc_type, 'value') else str(acc_type)
        msg += f"<b>{type_label.upper()}</b>\n"
        
        # Sort accounts alphabetically by name
        sorted_accounts = sorted(grouped[acc_type], key=lambda a: a.account_name.lower())
        for acc in sorted_accounts:
            msg += f"• <b>{acc.account_name}</b>: Rp{acc.current_balance:,.0f}\n"
            total_acc += acc.current_balance
        msg += "\n"

    # Strip trailing whitespace/newlines
    msg = msg.strip()
    msg += f"\n\n<b>Total Saldo Account: Rp{total_acc:,.0f}</b>"
    await update.message.reply_html(msg)

@restricted
async def debt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, _, _, _ = get_helpers(context)
    liabilities = storage.get_all_liabilities()

    msg = "💳 <b>Daftar Kewajiban & Hutang (Liabilities)</b>\n\n"
    total_debt = 0.0
    active_liabilities = [l for l in liabilities if l.status == "Active" and l.outstanding_balance > 0]

    if not active_liabilities:
        msg += "🎉 Selamat! Anda tidak memiliki hutang/kewajiban aktif saat ini."
    else:
        for l in active_liabilities:
            msg += f"• <b>{l.liability_name}</b> ({l.liability_type}): Rp{l.outstanding_balance:,.0f}\n"
            total_debt += l.outstanding_balance
        msg += f"\n<b>Total Kewajiban: Rp{total_debt:,.0f}</b>"

    await update.message.reply_html(msg)

@restricted
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, statement_gen, pdf_gen = get_helpers(context)
    await update.message.reply_text("⏳ Sedang menyiapkan Laporan Keuangan PDF...")

    today = date.today()
    # End date is 24th of current month
    end_date_obj = date(today.year, today.month, 24)
    # Start date is 25th of previous month
    if end_date_obj.month == 1:
        start_year = end_date_obj.year - 1
        start_month = 12
    else:
        start_year = end_date_obj.year
        start_month = end_date_obj.month - 1
    start_date_obj = date(start_year, start_month, 25)
    start_date = start_date_obj.strftime("%Y-%m-%d")
    end_date = end_date_obj.strftime("%Y-%m-%d")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name

    try:
        pdf_gen.generate_pdf_report(start_date, end_date, output_path=pdf_path)
        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Financial_Report_{end_date_obj.strftime('%Y_%m')}.pdf",
                caption=f"📄 <b>Laporan Keuangan Periode {end_date_obj.strftime('%B %Y')}</b>\n"
                        f"(Periode {start_date_obj.strftime('%d %b %Y')} - {end_date_obj.strftime('%d %b %Y')})",
                parse_mode="HTML"
            )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

@restricted
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, _, _, _ = get_helpers(context)
    all_tx = storage.get_all_transactions()
    posted_tx = [
        t for t in all_tx
        if (t.status.value if hasattr(t.status, 'value') else str(t.status)).lower().strip() == "posted"
    ]
    recent_tx = list(reversed(posted_tx))[:10]

    if not recent_tx:
        await update.message.reply_html("📋 Belum ada transaksi aktif yang tercatat.")
        return

    msg = "📋 <b>10 Transaksi Terakhir:</b>\n\n"
    for tx in recent_tx:
        type_str = tx.type.value if hasattr(tx.type, 'value') else str(tx.type)
        msg += (
            f"🔹 <b>ID:</b> <code>{tx.transaction_id}</code>\n"
            f"   📅 {tx.transaction_date} | {type_str} | Rp{tx.amount:,.0f}\n"
            f"   🏷️ {tx.category} ({tx.account}) — {tx.description}\n\n"
        )
    msg += "💡 <i>Untuk membatalkan/menghapus transaksi, gunakan:</i>\n<code>/void ID_TRANSAKSI</code>"
    await update.message.reply_html(msg)

@restricted
async def void_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, _, _ = get_helpers(context)
    args = context.args

    if not args:
        await update.message.reply_html(
            "⚠️ <b>Format Pembatalan Transaksi:</b>\n"
            "<code>/void ID_TRANSAKSI</code>\n\n"
            "<i>Contoh:</i> <code>/void TX-5CFFE0CA</code>\n"
            "💡 Gunakan perintah /history untuk melihat daftar ID Transaksi."
        )
        return

    tx_id = args[0].strip().upper()
    try:
        voided_tx = engine.void_transaction(tx_id, reason="User Void via Telegram")
        msg = (
            f"❌ <b>Transaksi Berhasil Dibatalkan (Void)</b>\n\n"
            f"🔹 <b>ID:</b> <code>{voided_tx.transaction_id}</code>\n"
            f"📝 <b>Deskripsi:</b> {voided_tx.description}\n"
            f"💵 <b>Jumlah:</b> Rp{voided_tx.amount:,.0f}\n"
            f"🏦 <b>Account:</b> {voided_tx.account}\n\n"
            "✅ <i>Saldo akun telah dikembalikan dan histori audit tersimpan.</i>"
        )
        await update.message.reply_html(msg)
    except Exception as e:
        await update.message.reply_html(f"❌ Gagal membatalkan transaksi: {e}")

@restricted
async def delete_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, _, _ = get_helpers(context)
    args = context.args

    if not args:
        await update.message.reply_html(
            "⚠️ <b>Format Nonaktifkan Account:</b>\n"
            "<code>/deactivateaccount NAMA_ACCOUNT</code>\n"
            "<i>Contoh:</i> <code>/deactivateaccount GoPay</code>\n\n"
            "ℹ️ <i>Account tidak dihapus secara permanen agar histori akuntansi tetap aman. Status account akan diubah menjadi Nonaktif (Inactive).</i>"
        )
        return

    acc_name = " ".join(args).strip()
    try:
        acc = engine.deactivate_account(acc_name)
        await update.message.reply_html(f"✅ Account <b>{acc.account_name}</b> berhasil dinonaktifkan (Status: Inactive). Histori transaksi tetap tersimpan aman.")
    except Exception as e:
        await update.message.reply_html(f"❌ Gagal menonaktifkan account: {e}")

@restricted
async def edit_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, _, _ = get_helpers(context)
    args = context.args

    if len(args) < 2:
        await update.message.reply_html(
            "⚠️ <b>Format Edit Saldo Account:</b>\n"
            "<code>/editbalance NAMA_ACCOUNT SALDO_BARU</code>\n\n"
            "<i>Contoh:</i> <code>/editbalance GoPay 750000</code>\n"
            "<i>Contoh:</i> <code>/editbalance BRI 15000000</code>"
        )
        return

    acc_name = " ".join(args[:-1]).strip()
    raw_amount = args[-1].replace(".", "").replace(",", "").strip()

    try:
        new_balance = float(raw_amount)
        acc = engine.edit_account_balance(acc_name, new_balance, reason="Manual user adjustment via Telegram")
        await update.message.reply_html(
            f"✅ <b>Saldo Account Berhasil Diperbarui</b>\n\n"
            f"🏦 <b>Account:</b> {acc.account_name}\n"
            f"💵 <b>Saldo Baru:</b> Rp{acc.current_balance:,.0f}\n\n"
            "✅ <i>Penyesuaian saldo telah dicatat di Audit Log & Google Sheets.</i>"
        )
    except Exception as e:
        await update.message.reply_html(f"❌ Gagal memperbarui saldo: {e}")

@restricted
async def rename_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage, engine, _, _ = get_helpers(context)
    args = context.args

    if len(args) < 2:
        await update.message.reply_html(
            "⚠️ <b>Format Ubah Nama Account:</b>\n"
            "<code>/renameaccount NAMA_LAMA NAMA_BARU</code>\n\n"
            "<i>Contoh:</i> <code>/renameaccount GoPay GoPay Utama</code>"
        )
        return

    old_name = args[0].strip()
    new_name = " ".join(args[1:]).strip()

    try:
        acc = engine.rename_account(old_name, new_name)
        await update.message.reply_html(
            f"✅ <b>Nama Account Berhasil Diubah</b>\n\n"
            f"📝 <b>Nama Lama:</b> {old_name}\n"
            f"✨ <b>Nama Baru:</b> {acc.account_name}\n"
            f"💳 <b>Saldo:</b> Rp{acc.current_balance:,.0f}"
        )
    except Exception as e:
        await update.message.reply_html(f"❌ Gagal mengubah nama account: {e}")

@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 <b>Daftar Perintah & Cara Penggunaan</b>\n\n"
        "<b>Manajemen Transaksi:</b>\n"
        "• /summary - Ringkasan keuangan bulan ini\n"
        "• /balance - Laporan Neraca (Balance Sheet & Net Worth)\n"
        "• /expense - Rincian pengeluaran per kategori\n"
        "• /income - Rincian pemasukan per kategori\n"
        "• /history - Lihat 10 ID transaksi terakhir\n"
        "• /void ID - Membatalkan/menghapus transaksi berdasarkan ID\n"
        "• /report - Download Laporan Keuangan format PDF\n\n"
        "<b>Manajemen Account / Rekening:</b>\n"
        "• /accounts - Saldo seluruh rekening/account\n"
        "• /editbalance NAMA SALDO - Edit saldo rekening (misal: /editbalance GoPay 750000)\n"
        "• /renameaccount LAMA BARU - Ubah nama rekening (misal: /renameaccount GoPay GoPayUtama)\n"
        "• /deactivateaccount NAMA - Nonaktifkan rekening (misal: /deactivateaccount GoPay)\n"
        "• /setup - Wizard pengisian rekening awal\n"
        "• /help - Bantuan ini\n\n"
        "<b>Contoh Input Bahasa Natural:</b>\n"
        "• <i>\"Tadi makan 35 ribu pakai GoPay\"</i>\n"
        "• <i>\"Top up GoPay 500 ribu dari BRI\"</i>\n"
        "• <i>\"Gaji masuk BRI 10 juta\"</i>"
    )
    await update.message.reply_html(msg)
