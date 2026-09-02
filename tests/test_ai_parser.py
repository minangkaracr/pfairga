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
