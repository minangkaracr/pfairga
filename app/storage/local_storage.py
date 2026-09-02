import json
import logging
from pathlib import Path
from typing import List, Optional
from app import config
from app.storage.base import BaseStorage
from app.accounting.models import (
    Transaction, Account, Category, CategoryAlias, Asset, Liability, AuditLog,
    AccountType, CategoryType
)

logger = logging.getLogger(__name__)

class LocalStorage(BaseStorage):
    """
    Local JSON file implementation of BaseStorage.
    Provides immediate zero-config testing and offline local execution.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or config.DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.tx_file = self.data_dir / "transactions.json"
        self.acc_file = self.data_dir / "accounts.json"
        self.cat_file = self.data_dir / "categories.json"
        self.alias_file = self.data_dir / "category_aliases.json"
        self.asset_file = self.data_dir / "assets.json"
        self.lia_file = self.data_dir / "liabilities.json"
        self.audit_file = self.data_dir / "audit_log.json"

        self._seed_defaults_if_needed()

    def _read_json(self, file_path: Path) -> List[dict]:
        if not file_path.exists():
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON from {file_path}: {e}")
            return []

    def _write_json(self, file_path: Path, data: List[dict]) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _seed_defaults_if_needed(self):
        # Default Categories per BRD §78
        if not self.cat_file.exists():
            default_categories = [
                Category(category_id="CAT-001", category_name="Salary", category_type=CategoryType.INCOME),
                Category(category_id="CAT-002", category_name="Other Income", category_type=CategoryType.INCOME),
                Category(category_id="CAT-003", category_name="Food & Beverage", category_type=CategoryType.EXPENSE),
                Category(category_id="CAT-004", category_name="Housing", category_type=CategoryType.EXPENSE),
                Category(category_id="CAT-005", category_name="Utilities", category_type=CategoryType.EXPENSE),
                Category(category_id="CAT-006", category_name="Transportation", category_type=CategoryType.EXPENSE),
                Category(category_id="CAT-007", category_name="Shopping", category_type=CategoryType.EXPENSE),
                Category(category_id="CAT-008", category_name="Entertainment", category_type=CategoryType.EXPENSE),
                Category(category_id="CAT-009", category_name="Electronics", category_type=CategoryType.ASSET),
                Category(category_id="CAT-010", category_name="Credit Card Payment", category_type=CategoryType.LIABILITY),
                Category(category_id="CAT-011", category_name="Transfer", category_type=CategoryType.TRANSFER)
            ]
            self._write_json(self.cat_file, [c.model_dump() for c in default_categories])

        # Default Aliases per BRD §24, §53
        if not self.alias_file.exists():
            default_aliases = [
                CategoryAlias(alias_id="ALI-001", alias="kopi", category_id="CAT-003", category_name="Food & Beverage"),
                CategoryAlias(alias_id="ALI-002", alias="coffee", category_id="CAT-003", category_name="Food & Beverage"),
                CategoryAlias(alias_id="ALI-003", alias="ngopi", category_id="CAT-003", category_name="Food & Beverage"),
                CategoryAlias(alias_id="ALI-004", alias="cafe", category_id="CAT-003", category_name="Food & Beverage"),
                CategoryAlias(alias_id="ALI-005", alias="makan", category_id="CAT-003", category_name="Food & Beverage"),
                CategoryAlias(alias_id="ALI-006", alias="gaji", category_id="CAT-001", category_name="Salary"),
                CategoryAlias(alias_id="ALI-007", alias="topup", category_id="CAT-011", category_name="Transfer"),
                CategoryAlias(alias_id="ALI-008", alias="bensin", category_id="CAT-006", category_name="Transportation")
            ]
            self._write_json(self.alias_file, [a.model_dump() for a in default_aliases])

        # Default Accounts per BRD §36
        if not self.acc_file.exists():
            default_accounts = [
                Account(account_id="ACC-001", account_name="Cash", account_type=AccountType.CASH, opening_balance=0.0, current_balance=0.0),
                Account(account_id="ACC-002", account_name="BRI", account_type=AccountType.BANK, opening_balance=0.0, current_balance=0.0),
                Account(account_id="ACC-003", account_name="BCA", account_type=AccountType.BANK, opening_balance=0.0, current_balance=0.0),
                Account(account_id="ACC-004", account_name="GoPay", account_type=AccountType.EWALLET, opening_balance=0.0, current_balance=0.0),
                Account(account_id="ACC-005", account_name="OVO", account_type=AccountType.EWALLET, opening_balance=0.0, current_balance=0.0),
                Account(account_id="ACC-006", account_name="BRIZZI", account_type=AccountType.PREPAID, opening_balance=0.0, current_balance=0.0)
            ]
            self._write_json(self.acc_file, [a.model_dump() for a in default_accounts])

    # Transactions
    def save_transaction(self, transaction: Transaction) -> None:
        data = self._read_json(self.tx_file)
        filtered = [d for d in data if d.get("transaction_id") != transaction.transaction_id]
        filtered.append(transaction.model_dump())
        self._write_json(self.tx_file, filtered)

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        data = self._read_json(self.tx_file)
        for d in data:
            if d.get("transaction_id") == transaction_id:
                return Transaction(**d)
        return None

    def get_all_transactions(self) -> List[Transaction]:
        data = self._read_json(self.tx_file)
        return [Transaction(**d) for d in data]

    def get_transactions_by_period(self, start_date: str, end_date: str) -> List[Transaction]:
        all_tx = self.get_all_transactions()
        return [tx for tx in all_tx if start_date <= tx.transaction_date <= end_date]

    # Accounts
    def save_account(self, account: Account) -> None:
        data = self._read_json(self.acc_file)
        filtered = [d for d in data if d.get("account_id") != account.account_id and d.get("account_name").lower() != account.account_name.lower()]
        filtered.append(account.model_dump())
        self._write_json(self.acc_file, filtered)

    def get_account_by_name(self, account_name: str) -> Optional[Account]:
        data = self._read_json(self.acc_file)
        target = account_name.lower().strip()
        for d in data:
            if d.get("account_name", "").lower().strip() == target:
                return Account(**d)
        return None

    def get_all_accounts(self) -> List[Account]:
        data = self._read_json(self.acc_file)
        return [Account(**d) for d in data]

    # Categories
    def save_category(self, category: Category) -> None:
        data = self._read_json(self.cat_file)
        filtered = [d for d in data if d.get("category_id") != category.category_id]
        filtered.append(category.model_dump())
        self._write_json(self.cat_file, filtered)

    def get_all_categories(self) -> List[Category]:
        data = self._read_json(self.cat_file)
        return [Category(**d) for d in data]

    # Category Aliases
    def save_category_alias(self, alias: CategoryAlias) -> None:
        data = self._read_json(self.alias_file)
        filtered = [d for d in data if d.get("alias_id") != alias.alias_id]
        filtered.append(alias.model_dump())
        self._write_json(self.alias_file, filtered)

    def get_all_category_aliases(self) -> List[CategoryAlias]:
        data = self._read_json(self.alias_file)
        return [CategoryAlias(**d) for d in data]

    # Assets
    def save_asset(self, asset: Asset) -> None:
        data = self._read_json(self.asset_file)
        filtered = [d for d in data if d.get("asset_id") != asset.asset_id]
        filtered.append(asset.model_dump())
        self._write_json(self.asset_file, filtered)

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        data = self._read_json(self.asset_file)
        for d in data:
            if d.get("asset_id") == asset_id:
                return Asset(**d)
        return None

    def get_all_assets(self) -> List[Asset]:
        data = self._read_json(self.asset_file)
        return [Asset(**d) for d in data]

    # Liabilities
    def save_liability(self, liability: Liability) -> None:
        data = self._read_json(self.lia_file)
        filtered = [d for d in data if d.get("liability_id") != liability.liability_id]
        filtered.append(liability.model_dump())
        self._write_json(self.lia_file, filtered)

    def get_liability(self, liability_id: str) -> Optional[Liability]:
        data = self._read_json(self.lia_file)
        for d in data:
            if d.get("liability_id") == liability_id:
                return Liability(**d)
        return None

    def get_all_liabilities(self) -> List[Liability]:
        data = self._read_json(self.lia_file)
        return [Liability(**d) for d in data]

    # Audit Log
    def save_audit_log(self, audit: AuditLog) -> None:
        data = self._read_json(self.audit_file)
        data.append(audit.model_dump())
        self._write_json(self.audit_file, data)

    def get_all_audit_logs(self) -> List[AuditLog]:
        data = self._read_json(self.audit_file)
        return [AuditLog(**d) for d in data]
