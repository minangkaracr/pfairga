import pytest
import shutil
from pathlib import Path
from app.storage.local_storage import LocalStorage
from app.accounting.engine import AccountingEngine
from app.accounting.statements import FinancialStatementGenerator
from app.accounting.models import (
    Transaction, Account, AccountType, TransactionType, TransactionStatus
)

@pytest.fixture
def temp_storage(tmp_path):
    storage = LocalStorage(data_dir=tmp_path)
    # Clear out seeded defaults for explicit control
    storage.save_account(Account(account_id="ACC-01", account_name="BRI", account_type=AccountType.BANK, opening_balance=10_000_000.0, current_balance=10_000_000.0))
    storage.save_account(Account(account_id="ACC-02", account_name="GoPay", account_type=AccountType.EWALLET, opening_balance=500_000.0, current_balance=500_000.0))
    storage.save_account(Account(account_id="ACC-03", account_name="BRI Credit Card", account_type=AccountType.CREDIT_CARD, opening_balance=0.0, current_balance=0.0))
    return storage

def test_transfer_rules(temp_storage):
    """BR-001/002: Transfer is NOT income or expense. Decreases source balance, increases dest balance."""
    engine = AccountingEngine(temp_storage)
    stmt_gen = FinancialStatementGenerator(temp_storage)

    tx = Transaction(
        transaction_id="TX-101",
        transaction_date="2026-08-16",
        recorded_at="2026-08-16",
        type=TransactionType.TRANSFER,
        description="Top Up GoPay dari BRI",
        amount=500_000.0,
        account="BRI",
        destination_account="GoPay",
        category="Transfer"
    )
    engine.post_transaction(tx)

    bri = temp_storage.get_account_by_name("BRI")
    gopay = temp_storage.get_account_by_name("GoPay")

    assert bri.current_balance == 9_500_000.0
    assert gopay.current_balance == 1_000_000.0

    # Verify no impact on income statement
    inc_stmt = stmt_gen.generate_income_statement("2026-08-01", "2026-08-31")
    assert inc_stmt["total_income"] == 0.0
    assert inc_stmt["total_expense"] == 0.0

def test_expense_rules(temp_storage):
    """BR-003: Expense reduces account balance and increases total expense."""
    engine = AccountingEngine(temp_storage)
    stmt_gen = FinancialStatementGenerator(temp_storage)

    tx = Transaction(
        transaction_id="TX-102",
        transaction_date="2026-08-16",
        recorded_at="2026-08-16",
        type=TransactionType.EXPENSE,
        description="Makan 35 ribu",
        amount=35_000.0,
        account="GoPay",
        category="Food & Beverage"
    )
    engine.post_transaction(tx)

    gopay = temp_storage.get_account_by_name("GoPay")
    assert gopay.current_balance == 465_000.0

    inc_stmt = stmt_gen.generate_income_statement("2026-08-01", "2026-08-31")
    assert inc_stmt["total_expense"] == 35_000.0
    assert inc_stmt["net_income"] == -35_000.0

def test_asset_acquisition_and_depreciation(temp_storage):
    """BR-005 & BR-006: Asset acquisition enters Balance Sheet and is depreciated straight-line."""
    engine = AccountingEngine(temp_storage)
    stmt_gen = FinancialStatementGenerator(temp_storage)

    tx = Transaction(
        transaction_id="TX-103",
        transaction_date="2026-01-01",
        recorded_at="2026-01-01",
        type=TransactionType.ASSET_ACQUISITION,
        description="Beli Laptop",
        amount=15_000_000.0,
        account="BRI",
        category="Electronics"
    )
    engine.post_transaction(tx)

    bri = temp_storage.get_account_by_name("BRI")
    assert bri.current_balance == -5_000_000.0  # 10M opening - 15M purchase

    assets = temp_storage.get_all_assets()
    assert len(assets) == 1
    assert assets[0].acquisition_cost == 15_000_000.0

    # Run depreciation for 1 year (12 months)
    updated_assets = engine.run_depreciation("2027-01-01")
    assert len(updated_assets) == 1
    # Annual depreciation = 15M / 5 years = 3M
    assert updated_assets[0].accumulated_depreciation == 3_000_000.0
    assert updated_assets[0].net_book_value == 12_000_000.0

def test_balance_sheet_integrity(temp_storage):
    """BR-016: Hard check Assets == Liabilities + Equity."""
    engine = AccountingEngine(temp_storage)
    stmt_gen = FinancialStatementGenerator(temp_storage)

    bs = stmt_gen.generate_balance_sheet()
    assert bs["is_balanced"] is True
    assert bs["discrepancy"] == 0.0

def test_void_transaction(temp_storage):
    """BR-014: Soft void reverses transaction effect and maintains audit history."""
    engine = AccountingEngine(temp_storage)

    tx = Transaction(
        transaction_id="TX-104",
        transaction_date="2026-08-16",
        recorded_at="2026-08-16",
        type=TransactionType.EXPENSE,
        description="Makan 50 ribu",
        amount=50_000.0,
        account="GoPay",
        category="Food & Beverage"
    )
    engine.post_transaction(tx)
    assert temp_storage.get_account_by_name("GoPay").current_balance == 450_000.0

    # Void transaction
    engine.void_transaction("TX-104", reason="Salah catat")
    assert temp_storage.get_account_by_name("GoPay").current_balance == 500_000.0

    audits = temp_storage.get_all_audit_logs()
    assert any(a.action.value == "VOID" for a in audits)

def test_rename_account(temp_storage):
    """Verify renaming an account updates account_name without creating duplicates."""
    engine = AccountingEngine(temp_storage)
    bca_before = temp_storage.get_account_by_name("BCA")
    assert bca_before is not None

    renamed = engine.rename_account("BCA", "Mandiri")
    assert renamed.account_name == "Mandiri"
    assert renamed.account_id == bca_before.account_id

    assert temp_storage.get_account_by_name("BCA") is None
    assert temp_storage.get_account_by_name("Mandiri") is not None
    assert len(temp_storage.get_all_accounts()) == 7  # Total account count remains unchanged after rename

