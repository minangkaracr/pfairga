from abc import ABC, abstractmethod
from typing import List, Optional
from app.accounting.models import Transaction, Account, Category, CategoryAlias, Asset, Liability, AuditLog

class BaseStorage(ABC):
    """Abstract storage interface for data persistence."""

    # Transactions
    @abstractmethod
    def save_transaction(self, transaction: Transaction) -> None:
        pass

    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        pass

    @abstractmethod
    def get_all_transactions(self) -> List[Transaction]:
        pass

    @abstractmethod
    def get_transactions_by_period(self, start_date: str, end_date: str) -> List[Transaction]:
        pass

    # Accounts
    @abstractmethod
    def save_account(self, account: Account) -> None:
        pass

    @abstractmethod
    def get_account_by_name(self, account_name: str) -> Optional[Account]:
        pass

    @abstractmethod
    def get_all_accounts(self) -> List[Account]:
        pass

    # Categories
    @abstractmethod
    def save_category(self, category: Category) -> None:
        pass

    @abstractmethod
    def get_all_categories(self) -> List[Category]:
        pass

    # Category Aliases
    @abstractmethod
    def save_category_alias(self, alias: CategoryAlias) -> None:
        pass

    @abstractmethod
    def get_all_category_aliases(self) -> List[CategoryAlias]:
        pass

    # Assets
    @abstractmethod
    def save_asset(self, asset: Asset) -> None:
        pass

    @abstractmethod
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        pass

    @abstractmethod
    def get_all_assets(self) -> List[Asset]:
        pass

    # Liabilities
    @abstractmethod
    def save_liability(self, liability: Liability) -> None:
        pass

    @abstractmethod
    def get_liability(self, liability_id: str) -> Optional[Liability]:
        pass

    @abstractmethod
    def get_all_liabilities(self) -> List[Liability]:
        pass

    # Audit Log
    @abstractmethod
    def save_audit_log(self, audit: AuditLog) -> None:
        pass

    @abstractmethod
    def get_all_audit_logs(self) -> List[AuditLog]:
        pass
