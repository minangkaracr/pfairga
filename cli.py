import sys
import io
import json
from datetime import date

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import config
from app.storage.local_storage import LocalStorage
from app.sheets.sheets_storage import SheetsStorage
from app.accounting.engine import AccountingEngine
from app.accounting.statements import FinancialStatementGenerator
from app.ai.parser import AIParserService
from app.reporting.pdf_generator import PDFReportGenerator
from app.accounting.models import Account, AccountType, Transaction, TransactionType

def get_storage():
    if config.STORAGE_DRIVER == "sheets":
        return SheetsStorage()
    return LocalStorage()

def cli_seed():
    storage = get_storage()
    print("🌱 Seeding opening balances...")
    accounts = [
        ("BRI", AccountType.BANK, 10_000_000.0),
        ("BCA", AccountType.BANK, 5_000_000.0),
        ("GoPay", AccountType.EWALLET, 500_000.0),
        ("Cash", AccountType.CASH, 1_000_000.0),
        ("BRIZZI", AccountType.PREPAID, 100_000.0)
    ]
    for idx, (name, acc_type, opening) in enumerate(accounts, 1):
        acc = Account(
            account_id=f"ACC-00{idx}",
            account_name=name,
            account_type=acc_type,
            opening_balance=opening,
            current_balance=opening
        )
        storage.save_account(acc)
        print(f"  [+] Account {name} ({acc_type.value}) set with Opening Balance: Rp{opening:,.0f}")
    print("✅ Seeding complete!")

def cli_parse(user_input: str):
    storage = get_storage()
    engine = AccountingEngine(storage)
    ai_parser = AIParserService(storage)

    print(f"\n💬 Processing Input: \"{user_input}\"")
    result = ai_parser.parse_user_message(user_input)
    print(f"🤖 AI Intent: {result.intent} | Confidence: {result.confidence_score}")

    if result.missing_critical_fields:
        print(f"⚠️ Missing Critical Fields: {result.missing_critical_fields}")
        print(f"❓ Clarification Prompt: {result.clarification_prompt}")
        return

    for item in result.items:
        import uuid
        tx = Transaction(
            transaction_id=f"TX-{uuid.uuid4().hex[:8].upper()}",
            transaction_date=item.transaction_date,
            recorded_at=date.today().strftime("%Y-%m-%d"),
            type=item.transaction_type,
            description=item.description,
            amount=item.amount,
            account=item.account or "GoPay",
            destination_account=item.destination_account,
            category=item.category
        )
        posted = engine.post_transaction(tx)
        print(f"  [+] Posted Transaction {posted.transaction_id}: {posted.type.value} | Rp{posted.amount:,.0f} | Account: {posted.account} | Cat: {posted.category}")

def cli_summary():
    storage = get_storage()
    stmt = FinancialStatementGenerator(storage)
    today = date.today()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    inc = stmt.generate_income_statement(start_date, end_date)
    bs = stmt.generate_balance_sheet()

    print("\n==========================================")
    print(f"📊 MONTHLY SUMMARY ({start_date} s/d {end_date})")
    print("==========================================")
    print(f"Total Income   : Rp{inc['total_income']:,.0f}")
    print(f"Total Expense  : Rp{inc['total_expense']:,.0f}")
    print(f"Net Income     : Rp{inc['net_income']:,.0f}")
    print("------------------------------------------")
    print(f"Total Assets   : Rp{bs['assets']['total_assets']:,.0f}")
    print(f"Total Liab.    : Rp{bs['liabilities']['total_liabilities']:,.0f}")
    print(f"Total Equity   : Rp{bs['equity']['total_equity']:,.0f}")
    print(f"NET WORTH      : Rp{bs['net_worth']:,.0f}")
    status_str = 'BALANCED' if bs['is_balanced'] else f"UNBALANCED (Diff: {bs['discrepancy']})"
    print(f"Integrity Check: {status_str}")
    print("==========================================\n")

def cli_report():
    storage = get_storage()
    pdf_gen = PDFReportGenerator(storage)
    today = date.today()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    output_filename = "Financial_Report_Demo.pdf"
    pdf_gen.generate_pdf_report(start_date, end_date, output_path=output_filename)
    print(f"✅ Generated PDF report saved to: {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cli.py [seed | parse <input> | summary | report]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "seed":
        cli_seed()
    elif cmd == "parse":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Tadi makan 35 ribu pakai GoPay"
        cli_parse(text)
    elif cmd == "summary":
        cli_summary()
    elif cmd == "report":
        cli_report()
    else:
        print(f"Unknown command: {cmd}")
