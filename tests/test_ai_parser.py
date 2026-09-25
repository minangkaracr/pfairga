import pytest
from app.storage.local_storage import LocalStorage
from app.ai.parser import AIParserService
from app.accounting.models import TransactionType

@pytest.fixture
def temp_storage(tmp_path):
    return LocalStorage(data_dir=tmp_path)

def test_nlp_expense_parsing(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("Tadi makan 35 ribu pakai GoPay", target_date="2026-08-16")

    assert res.is_financial_transaction is True
    assert len(res.items) == 1
    item = res.items[0]
    assert item.transaction_type == TransactionType.EXPENSE
    assert item.amount == 35000.0
    assert item.account == "GoPay"
    assert item.category == "Food & Beverage"

def test_nlp_transfer_parsing(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("Top up GoPay 500 ribu dari BRI", target_date="2026-08-16")

    assert res.is_financial_transaction is True
    item = res.items[0]
    assert item.transaction_type == TransactionType.TRANSFER
    assert item.amount == 500000.0
    assert item.account == "BRI"
    assert item.destination_account == "GoPay"

def test_nlp_missing_account_trigger(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("Makan 50 ribu", target_date="2026-08-16")

    assert "account" in res.missing_critical_fields
    assert res.clarification_prompt is not None

def test_nlp_liability_payment_parsing(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("bayar cicilan CC 221040 bayar bri", target_date="2026-09-25")

    assert res.is_financial_transaction is True
    assert len(res.items) == 1
    item = res.items[0]
    assert item.transaction_type == TransactionType.LIABILITY_PAYMENT
    assert item.amount == 221040.0
    assert item.account == "BRI"
    assert "Credit Card" in item.destination_account or "Kartu Kredit" in item.destination_account

def test_nlp_portfolio_setup_parsing(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("aku punya akun di bibit portofolio saya bernilai 21 juta", target_date="2026-09-25")

    assert res.intent == "setup_account"
    assert len(res.items) == 1
    item = res.items[0]
    assert item.account == "Bibit"
    assert item.amount == 21_000_000.0
    assert item.account_type == "Investment"

def test_nlp_bank_setup_parsing(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("aku punya akun tabungan di jago senilai 15 juta", target_date="2026-09-25")

    assert res.intent == "setup_account"
    assert len(res.items) == 1
    item = res.items[0]
    assert item.account == "Jago"
    assert item.amount == 15_000_000.0
    assert item.account_type == "Bank"

def test_nlp_gold_missing_amount_prompt(temp_storage):
    service = AIParserService(temp_storage)
    res = service.parse_user_message("aku punya emas 10 gram", target_date="2026-09-25")

    assert res.intent == "setup_account"
    assert "amount" in res.missing_critical_fields
    assert res.clarification_prompt is not None


