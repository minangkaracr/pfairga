import uuid
import logging
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
from app.accounting.models import (
    Transaction, Account, Category, Asset, Liability, AuditLog,
    TransactionType, AccountType, TransactionStatus, AuditAction
)
from app.storage.base import BaseStorage

logger = logging.getLogger(__name__)

class AccountingEngine:
    """
    Core Accounting Engine.
    Ensures accounting integrity, atomic transaction execution,
    balance updates, depreciation calculations, and audit logging.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def post_transaction(self, tx: Transaction, reason: str = "New Transaction") -> Transaction:
        """
        Validates and posts a transaction atomically to storage, updating running balances,
        asset/liability records, and audit logs.
        """

        # 1. Validation checks
        if tx.amount <= 0:
            raise ValueError("Transaction amount must be strictly greater than 0.")

        # Ensure source account exists or auto-register
        account_obj = self.storage.get_account_by_name(tx.account)
        if not account_obj:
            account_obj = self._auto_create_account(tx.account)

        dest_account_obj = None
        if tx.destination_account:
            dest_account_obj = self.storage.get_account_by_name(tx.destination_account)
            if not dest_account_obj:
                dest_account_obj = self._auto_create_account(tx.destination_account)

        # 2. Process financial rules based on transaction type
        if tx.type == TransactionType.INCOME:
            # BR-004: Income increases account balance
            account_obj.current_balance += tx.amount
            self.storage.save_account(account_obj)

        elif tx.type == TransactionType.EXPENSE:
            # BR-003: Expense decreases account balance (or increases liability if CC account)
            if account_obj.account_type == AccountType.CREDIT_CARD:
                # BR-007: CC Purchase increases credit card liability balance
                liability = self._get_or_create_cc_liability(account_obj)
                liability.outstanding_balance += tx.amount
                self.storage.save_liability(liability)
                tx.liability_id = liability.liability_id
                # CC balance in accounts represents total debt (positive outstanding)
                account_obj.current_balance += tx.amount
            else:
                account_obj.current_balance -= tx.amount

            self.storage.save_account(account_obj)

        elif tx.type == TransactionType.TRANSFER:
            # BR-001/002: Transfer is NOT income or expense.
            if not dest_account_obj:
                raise ValueError("Destination account is required for Transfer transactions.")
            account_obj.current_balance -= tx.amount
            dest_account_obj.current_balance += tx.amount
            self.storage.save_account(account_obj)
            self.storage.save_account(dest_account_obj)

        elif tx.type == TransactionType.ASSET_ACQUISITION:
            # BR-005: Asset acquisition enters Balance Sheet
            account_obj.current_balance -= tx.amount
            self.storage.save_account(account_obj)

            # Create or update Asset record
            asset = Asset(
                asset_id=f"AST-{uuid.uuid4().hex[:8].upper()}",
                asset_name=tx.description or "New Asset",
                asset_category=tx.category or "Electronics",
                acquisition_date=tx.transaction_date,
                acquisition_cost=tx.amount,
                useful_life_years=5.0,  # Default, can be updated via prompt/setup
                net_book_value=tx.amount
            )
            self.storage.save_asset(asset)
            tx.asset_id = asset.asset_id

        elif tx.type == TransactionType.LIABILITY_PAYMENT:
            # BR-008/009: Liability payment decreases bank balance and liability outstanding
            account_obj.current_balance -= tx.amount
            self.storage.save_account(account_obj)

            if dest_account_obj and dest_account_obj.account_type == AccountType.CREDIT_CARD:
                liability = self._get_or_create_cc_liability(dest_account_obj)
                liability.outstanding_balance = max(0.0, liability.outstanding_balance - tx.amount)
                self.storage.save_liability(liability)
                dest_account_obj.current_balance = max(0.0, dest_account_obj.current_balance - tx.amount)
                self.storage.save_account(dest_account_obj)
            elif tx.liability_id:
                liability = self.storage.get_liability(tx.liability_id)
                if liability:
                    liability.outstanding_balance = max(0.0, liability.outstanding_balance - tx.amount)
                    self.storage.save_liability(liability)

        elif tx.type == TransactionType.ADJUSTMENT:
            account_obj.current_balance += tx.amount
            self.storage.save_account(account_obj)

        # Save Transaction
        tx.status = TransactionStatus.POSTED
        self.storage.save_transaction(tx)

        # Audit Log
        audit = AuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            entity_type="Transaction",
            entity_id=tx.transaction_id,
            action=AuditAction.CREATE,
            new_value=tx.model_dump_json(),
            actor=tx.created_by,
            reason=reason
        )
        self.storage.save_audit_log(audit)
        return tx

    def void_transaction(self, transaction_id: str, reason: str = "User Void") -> Transaction:
        """
        Soft deletes/voids a transaction (BR-014) and reverses its accounting effect.
        """
        tx = self.storage.get_transaction(transaction_id)
        if not tx:
            raise ValueError(f"Transaction {transaction_id} not found.")
        if tx.status == TransactionStatus.VOIDED:
            raise ValueError(f"Transaction {transaction_id} is already voided.")

        old_json = tx.model_dump_json()

        # Reversal Logic
        account_obj = self.storage.get_account_by_name(tx.account)
        dest_account_obj = self.storage.get_account_by_name(tx.destination_account) if tx.destination_account else None

        if tx.type == TransactionType.INCOME and account_obj:
            account_obj.current_balance -= tx.amount
            self.storage.save_account(account_obj)

        elif tx.type == TransactionType.EXPENSE and account_obj:
            if account_obj.account_type == AccountType.CREDIT_CARD:
                liability = self._get_or_create_cc_liability(account_obj)
                liability.outstanding_balance = max(0.0, liability.outstanding_balance - tx.amount)
                self.storage.save_liability(liability)
                account_obj.current_balance = max(0.0, account_obj.current_balance - tx.amount)
            else:
                account_obj.current_balance += tx.amount
            self.storage.save_account(account_obj)

        elif tx.type == TransactionType.TRANSFER and account_obj and dest_account_obj:
            account_obj.current_balance += tx.amount
            dest_account_obj.current_balance -= tx.amount
            self.storage.save_account(account_obj)
            self.storage.save_account(dest_account_obj)

        tx.status = TransactionStatus.VOIDED
        tx.updated_at = datetime.now().isoformat()
        self.storage.save_transaction(tx)

        # Save Audit Entry
        audit = AuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            entity_type="Transaction",
            entity_id=tx.transaction_id,
            action=AuditAction.VOID,
            old_value=old_json,
            new_value=tx.model_dump_json(),
            actor="User",
            reason=reason
        )
        self.storage.save_audit_log(audit)
        return tx

    def update_transaction(self, transaction_id: str, new_amount: float, new_description: Optional[str] = None, reason: str = "User Update") -> Transaction:
        """
        Updates an existing historical transaction (BR-013) by voiding the old state and applying the new state.
        """
        tx = self.storage.get_transaction(transaction_id)
        if not tx:
            raise ValueError(f"Transaction {transaction_id} not found.")

        old_json = tx.model_dump_json()

        # Reverse previous amount
        self.void_transaction(transaction_id, reason=f"Reversing prior state for edit: {reason}")

        # Re-fetch transaction and apply new parameters
        tx = self.storage.get_transaction(transaction_id)
        tx.amount = new_amount
        if new_description:
            tx.description = new_description

        # Re-post with new values
        tx.status = TransactionStatus.POSTED
        posted_tx = self.post_transaction(tx, reason=reason)

        audit = AuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            entity_type="Transaction",
            entity_id=tx.transaction_id,
            action=AuditAction.UPDATE,
            old_value=old_json,
            new_value=posted_tx.model_dump_json(),
            actor="User",
            reason=reason
        )
        self.storage.save_audit_log(audit)
        return posted_tx

    def edit_account_balance(self, account_name: str, new_balance: float, reason: str = "Manual adjustment") -> Account:
        """Modifies the current balance of an account (auto-creates if missing) and creates an audit log entry."""
        acc = self.storage.get_account_by_name(account_name)
        old_json = acc.model_dump_json() if acc else None

        if not acc:
            acc = self._auto_create_account(account_name)
            acc.opening_balance = new_balance

        acc.current_balance = new_balance
        acc.updated_at = datetime.now().isoformat()
        self.storage.save_account(acc)

        audit = AuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            entity_type="Account",
            entity_id=acc.account_id,
            action=AuditAction.SYSTEM_ADJUSTMENT,
            old_value=old_json,
            new_value=acc.model_dump_json(),
            actor="User",
            reason=reason
        )
        self.storage.save_audit_log(audit)
        return acc

    def rename_account(self, old_name: str, new_name: str) -> Account:
        """Renames an existing account and logs the change."""
        acc = self.storage.get_account_by_name(old_name)
        if not acc:
            raise ValueError(f"Account '{old_name}' not found.")

        old_json = acc.model_dump_json()
        acc.account_name = new_name
        acc.updated_at = datetime.now().isoformat()
        self.storage.save_account(acc)

        audit = AuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            entity_type="Account",
            entity_id=acc.account_id,
            action=AuditAction.UPDATE,
            old_value=old_json,
            new_value=acc.model_dump_json(),
            actor="User",
            reason=f"Renamed account from {old_name} to {new_name}"
        )
        self.storage.save_audit_log(audit)
        return acc

    def deactivate_account(self, account_name: str) -> Account:
        """Sets account status to Inactive (soft delete)."""
        acc = self.storage.get_account_by_name(account_name)
        if not acc:
            raise ValueError(f"Account '{account_name}' not found.")

        old_json = acc.model_dump_json()
        acc.status = "Inactive"
        acc.updated_at = datetime.now().isoformat()
        self.storage.save_account(acc)

        audit = AuditLog(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            entity_type="Account",
            entity_id=acc.account_id,
            action=AuditAction.UPDATE,
            old_value=old_json,
            new_value=acc.model_dump_json(),
            actor="User",
            reason="Deactivated account"
        )
        self.storage.save_audit_log(audit)
        return acc

    def run_depreciation(self, target_date: Optional[str] = None) -> List[Asset]:
        """
        Calculates straight-line depreciation for all active assets up to target_date (BR-006, BR-017).
        Formula:
        Annual Depreciation = Acquisition Cost / Useful Life
        Monthly Depreciation = Annual / 12
        """
        if not target_date:
            target_date = date.today().strftime("%Y-%m-%d")

        target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        assets = self.storage.get_all_assets()
        updated_assets = []

        for asset in assets:
            if asset.status != "Active" or asset.useful_life_years <= 0:
                continue

            acq_dt = datetime.strptime(asset.acquisition_date, "%Y-%m-%d").date()
            if target_dt < acq_dt:
                continue

            # Calculate total months elapsed
            months_elapsed = (target_dt.year - acq_dt.year) * 12 + (target_dt.month - acq_dt.month)
            if months_elapsed <= 0:
                continue

            monthly_dep = asset.acquisition_cost / (asset.useful_life_years * 12.0)
            accumulated = min(asset.acquisition_cost, monthly_dep * months_elapsed)
            net_book = max(0.0, asset.acquisition_cost - accumulated)

            asset.accumulated_depreciation = round(accumulated, 2)
            asset.net_book_value = round(net_book, 2)
            asset.updated_at = datetime.now().isoformat()

            self.storage.save_asset(asset)
            updated_assets.append(asset)

        return updated_assets

    def _auto_create_account(self, account_name: str) -> Account:
        """Helper to create account if missing."""
        acc_type = AccountType.CASH
        lower = account_name.lower()
        if any(w in lower for w in ["bca", "bri", "mandiri", "bni", "cimb", "bank"]):
            acc_type = AccountType.BANK
        elif any(w in lower for w in ["gopay", "ovo", "dana", "shopeepay", "linkaja"]):
            acc_type = AccountType.EWALLET
        elif any(w in lower for w in ["brizzi", "flazz", "e-money"]):
            acc_type = AccountType.PREPAID
        elif "cc" in lower or "credit card" in lower or "kartu kredit" in lower:
            acc_type = AccountType.CREDIT_CARD

        acc = Account(
            account_id=f"ACC-{uuid.uuid4().hex[:8].upper()}",
            account_name=account_name,
            account_type=acc_type,
            opening_balance=0.0,
            current_balance=0.0
        )
        self.storage.save_account(acc)
        return acc

    def _get_or_create_cc_liability(self, account_obj: Account) -> Liability:
        """Finds or creates liability matching a credit card account."""
        liabilities = self.storage.get_all_liabilities()
        for l in liabilities:
            if l.liability_name.lower() == account_obj.account_name.lower():
                return l

        liability = Liability(
            liability_id=f"LIA-{uuid.uuid4().hex[:8].upper()}",
            liability_name=account_obj.account_name,
            liability_type="Credit Card",
            principal_amount=0.0,
            outstanding_balance=account_obj.current_balance,
            start_date=date.today().strftime("%Y-%m-%d")
        )
        self.storage.save_liability(liability)
        return liability
