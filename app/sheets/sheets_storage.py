import logging
from typing import List, Optional
from datetime import datetime
from app import config
from app.storage.base import BaseStorage
from app.accounting.models import (
    Transaction, Account, Category, CategoryAlias, Asset, Liability, AuditLog,
    AccountType, TransactionType, TransactionStatus, CategoryType, AuditAction
)

logger = logging.getLogger(__name__)


class SheetsStorage(BaseStorage):
    """
    Google Sheets-only implementation of BaseStorage using gspread.
    All data is read from and written to Google Sheets.
    No local JSON fallback — Sheets is the single source of truth.
    """

    def __init__(self):
        self.spreadsheet_id = config.GOOGLE_SHEETS_SPREADSHEET_ID
        self.service_account_file = config.GOOGLE_SERVICE_ACCOUNT_FILE
        self.client = None
        self.spreadsheet = None

        if self.spreadsheet_id and self.service_account_file:
            try:
                import gspread
                self.client = gspread.service_account(filename=self.service_account_file)
                self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                logger.info("Successfully connected to Google Sheets!")
            except Exception as e:
                logger.error(f"Failed to connect to Google Sheets: {e}")
                raise RuntimeError(f"Cannot connect to Google Sheets: {e}")
        else:
            raise RuntimeError("Google Sheets configuration (SPREADSHEET_ID / SERVICE_ACCOUNT_FILE) is missing.")

    def _sheet(self, name: str):
        """Get a worksheet by name."""
        return self.spreadsheet.worksheet(name)

    # ─────────────────────────────────────────────
    # TRANSACTIONS
    # ─────────────────────────────────────────────

    def save_transaction(self, transaction: Transaction) -> None:
        try:
            sheet = self._sheet("Transactions")
            all_cells = sheet.get_all_values()
            status_val = transaction.status.value if hasattr(transaction.status, 'value') else str(transaction.status)
            type_val = transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type)

            row_idx = None
            for idx, r in enumerate(all_cells[1:], start=2):
                if len(r) >= 1 and r[0].strip().upper() == transaction.transaction_id.strip().upper():
                    row_idx = idx
                    break

            row_data = [
                transaction.transaction_id,
                transaction.transaction_date,
                transaction.recorded_at,
                type_val,
                transaction.description,
                transaction.amount,
                transaction.currency,
                transaction.account,
                transaction.destination_account or "",
                transaction.category,
                transaction.asset_id or "",
                transaction.liability_id or "",
                status_val,
                transaction.source,
                transaction.ai_confidence,
                transaction.created_by,
                transaction.created_at,
                transaction.updated_at
            ]

            if row_idx:
                sheet.update(f"A{row_idx}:R{row_idx}", [row_data])
                logger.info(f"Updated transaction {transaction.transaction_id} in Sheets row {row_idx}.")
            else:
                sheet.append_row(row_data)
                logger.info(f"Appended transaction {transaction.transaction_id} to Sheets.")
        except Exception as e:
            logger.error(f"Error saving transaction to Sheets: {e}")
            raise

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        for tx in self.get_all_transactions():
            if tx.transaction_id.strip().upper() == transaction_id.strip().upper():
                return tx
        return None

    def get_all_transactions(self) -> List[Transaction]:
        try:
            sheet = self._sheet("Transactions")
            rows = sheet.get_all_values()
            tx_map = {}
            for r in rows[1:]:
                if len(r) >= 13 and r[0].strip():
                    try:
                        tx = Transaction(
                            transaction_id=r[0],
                            transaction_date=r[1],
                            recorded_at=r[2],
                            type=r[3],
                            description=r[4],
                            amount=float(r[5]) if r[5] else 0.0,
                            currency=r[6] if len(r) > 6 and r[6] else "IDR",
                            account=r[7],
                            destination_account=r[8] if len(r) > 8 and r[8] else None,
                            category=r[9] if len(r) > 9 and r[9] else "General",
                            asset_id=r[10] if len(r) > 10 and r[10] else None,
                            liability_id=r[11] if len(r) > 11 and r[11] else None,
                            status=r[12] if len(r) > 12 and r[12] else "Posted"
                        )
                        tx_map[r[0].strip().upper()] = tx
                    except Exception as parse_err:
                        logger.warning(f"Error parsing transaction row {r[0]}: {parse_err}")
            return list(tx_map.values())
        except Exception as e:
            logger.error(f"Error reading transactions from Sheets: {e}")
            return []

    def get_transactions_by_period(self, start_date: str, end_date: str) -> List[Transaction]:
        return [tx for tx in self.get_all_transactions() if start_date <= tx.transaction_date <= end_date]

    # ─────────────────────────────────────────────
    # ACCOUNTS
    # ─────────────────────────────────────────────

    def save_account(self, account: Account) -> None:
        try:
            sheet = self._sheet("Accounts")
            all_cells = sheet.get_all_values()
            acc_type_val = account.account_type.value if hasattr(account.account_type, 'value') else str(account.account_type)

            row_idx = None
            for idx, r in enumerate(all_cells[1:], start=2):
                if len(r) >= 2 and (
                    r[0].strip() == account.account_id.strip()
                    or r[1].lower().strip() == account.account_name.lower().strip()
                ):
                    row_idx = idx
                    break

            row_data = [
                account.account_id,
                account.account_name,
                acc_type_val,
                account.currency,
                account.opening_balance,
                account.current_balance,
                account.status,
                account.created_at,
                account.updated_at
            ]

            if row_idx:
                sheet.update(f"A{row_idx}:I{row_idx}", [row_data])
                logger.info(f"Updated account '{account.account_name}' in Sheets row {row_idx}.")
            else:
                sheet.append_row(row_data)
                logger.info(f"Appended account '{account.account_name}' to Sheets.")
        except Exception as e:
            logger.error(f"Error saving account to Sheets: {e}")
            raise

    def get_account_by_name(self, account_name: str) -> Optional[Account]:
        target = account_name.lower().strip()
        for acc in self.get_all_accounts():
            if acc.account_name.lower().strip() == target:
                return acc
        return None

    def get_all_accounts(self) -> List[Account]:
        try:
            sheet = self._sheet("Accounts")
            rows = sheet.get_all_values()
            accounts = []
            for r in rows[1:]:
                if len(r) >= 6 and r[0].strip():
                    try:
                        accounts.append(Account(
                            account_id=r[0],
                            account_name=r[1],
                            account_type=r[2],
                            currency=r[3] if len(r) > 3 and r[3] else "IDR",
                            opening_balance=float(r[4]) if r[4] else 0.0,
                            current_balance=float(r[5]) if r[5] else 0.0,
                            status=r[6] if len(r) > 6 and r[6] else "Active"
                        ))
                    except Exception as parse_err:
                        logger.warning(f"Error parsing account row '{r[1]}': {parse_err}")
            return accounts
        except Exception as e:
            logger.error(f"Error reading accounts from Sheets: {e}")
            return []

    # ─────────────────────────────────────────────
    # CATEGORIES
    # ─────────────────────────────────────────────

    def save_category(self, category: Category) -> None:
        try:
            sheet = self._sheet("Categories")
            all_cells = sheet.get_all_values()
            cat_type_val = category.category_type.value if hasattr(category.category_type, 'value') else str(category.category_type)

            row_idx = None
            for idx, r in enumerate(all_cells[1:], start=2):
                if len(r) >= 1 and r[0].strip() == category.category_id.strip():
                    row_idx = idx
                    break

            row_data = [
                category.category_id,
                category.category_name,
                cat_type_val,
                category.parent_category or "",
                category.description or "",
                category.created_by,
                category.created_at,
                category.status
            ]

            if row_idx:
                sheet.update(f"A{row_idx}:H{row_idx}", [row_data])
            else:
                sheet.append_row(row_data)
        except Exception as e:
            logger.error(f"Error saving category to Sheets: {e}")
            raise

    def get_all_categories(self) -> List[Category]:
        try:
            sheet = self._sheet("Categories")
            rows = sheet.get_all_values()
            categories = []
            for r in rows[1:]:
                if len(r) >= 3 and r[0].strip():
                    try:
                        categories.append(Category(
                            category_id=r[0],
                            category_name=r[1],
                            category_type=r[2],
                            parent_category=r[3] if len(r) > 3 and r[3] else None,
                            description=r[4] if len(r) > 4 else "",
                            created_by=r[5] if len(r) > 5 and r[5] else "System",
                            created_at=r[6] if len(r) > 6 and r[6] else datetime.now().isoformat(),
                            status=r[7] if len(r) > 7 and r[7] else "Active"
                        ))
                    except Exception as parse_err:
                        logger.warning(f"Error parsing category row '{r[1]}': {parse_err}")
            return categories
        except Exception as e:
            logger.error(f"Error reading categories from Sheets: {e}")
            return []

    # ─────────────────────────────────────────────
    # CATEGORY ALIASES
    # ─────────────────────────────────────────────

    def save_category_alias(self, alias: CategoryAlias) -> None:
        try:
            sheet = self._sheet("Category_Aliases")
            row_data = [
                alias.alias_id,
                alias.alias,
                alias.category_id,
                alias.category_name,
                alias.created_by,
                alias.created_at
            ]
            sheet.append_row(row_data)
        except Exception as e:
            logger.error(f"Error saving alias to Sheets: {e}")
            raise

    def get_all_category_aliases(self) -> List[CategoryAlias]:
        try:
            sheet = self._sheet("Category_Aliases")
            rows = sheet.get_all_values()
            aliases = []
            for r in rows[1:]:
                if len(r) >= 4 and r[0].strip():
                    try:
                        aliases.append(CategoryAlias(
                            alias_id=r[0],
                            alias=r[1],
                            category_id=r[2],
                            category_name=r[3],
                            created_by=r[4] if len(r) > 4 and r[4] else "System",
                            created_at=r[5] if len(r) > 5 and r[5] else datetime.now().isoformat()
                        ))
                    except Exception as parse_err:
                        logger.warning(f"Error parsing alias row '{r[1]}': {parse_err}")
            return aliases
        except Exception as e:
            logger.error(f"Error reading aliases from Sheets: {e}")
            return []

    # ─────────────────────────────────────────────
    # ASSETS
    # ─────────────────────────────────────────────

    def save_asset(self, asset: Asset) -> None:
        try:
            sheet = self._sheet("Assets")
            all_cells = sheet.get_all_values()

            row_idx = None
            for idx, r in enumerate(all_cells[1:], start=2):
                if len(r) >= 1 and r[0].strip() == asset.asset_id.strip():
                    row_idx = idx
                    break

            row_data = [
                asset.asset_id,
                asset.asset_name,
                asset.asset_category,
                asset.acquisition_date,
                asset.acquisition_cost,
                asset.useful_life_years,
                asset.depreciation_method,
                asset.accumulated_depreciation,
                asset.net_book_value,
                asset.status
            ]

            if row_idx:
                sheet.update(f"A{row_idx}:J{row_idx}", [row_data])
            else:
                sheet.append_row(row_data)
        except Exception as e:
            logger.error(f"Error saving asset to Sheets: {e}")
            raise

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        for a in self.get_all_assets():
            if a.asset_id == asset_id:
                return a
        return None

    def get_all_assets(self) -> List[Asset]:
        try:
            sheet = self._sheet("Assets")
            rows = sheet.get_all_values()
            assets = []
            for r in rows[1:]:
                if len(r) >= 9 and r[0].strip():
                    try:
                        assets.append(Asset(
                            asset_id=r[0],
                            asset_name=r[1],
                            asset_category=r[2] if len(r) > 2 and r[2] else "General",
                            acquisition_date=r[3] if len(r) > 3 and r[3] else "",
                            acquisition_cost=float(r[4]) if len(r) > 4 and r[4] else 0.0,
                            useful_life_years=float(r[5]) if len(r) > 5 and r[5] else 5.0,
                            depreciation_method=r[6] if len(r) > 6 and r[6] else "Straight Line",
                            accumulated_depreciation=float(r[7]) if len(r) > 7 and r[7] else 0.0,
                            net_book_value=float(r[8]) if len(r) > 8 and r[8] else 0.0,
                            status=r[9] if len(r) > 9 and r[9] else "Active"
                        ))
                    except Exception as parse_err:
                        logger.warning(f"Error parsing asset row '{r[1]}': {parse_err}")
            return assets
        except Exception as e:
            logger.error(f"Error reading assets from Sheets: {e}")
            return []

    # ─────────────────────────────────────────────
    # LIABILITIES
    # ─────────────────────────────────────────────

    def save_liability(self, liability: Liability) -> None:
        try:
            sheet = self._sheet("Liabilities")
            all_cells = sheet.get_all_values()

            row_idx = None
            for idx, r in enumerate(all_cells[1:], start=2):
                if len(r) >= 1 and r[0].strip() == liability.liability_id.strip():
                    row_idx = idx
                    break

            row_data = [
                liability.liability_id,
                liability.liability_name,
                liability.liability_type,
                liability.principal_amount,
                liability.outstanding_balance,
                liability.interest_rate,
                liability.start_date,
                liability.due_date or "",
                liability.status
            ]

            if row_idx:
                sheet.update(f"A{row_idx}:I{row_idx}", [row_data])
            else:
                sheet.append_row(row_data)
        except Exception as e:
            logger.error(f"Error saving liability to Sheets: {e}")
            raise

    def get_liability(self, liability_id: str) -> Optional[Liability]:
        for l in self.get_all_liabilities():
            if l.liability_id == liability_id:
                return l
        return None

    def get_all_liabilities(self) -> List[Liability]:
        try:
            sheet = self._sheet("Liabilities")
            rows = sheet.get_all_values()
            liabilities = []
            for r in rows[1:]:
                if len(r) >= 5 and r[0].strip():
                    try:
                        liabilities.append(Liability(
                            liability_id=r[0],
                            liability_name=r[1],
                            liability_type=r[2] if len(r) > 2 and r[2] else "Other",
                            principal_amount=float(r[3]) if len(r) > 3 and r[3] else 0.0,
                            outstanding_balance=float(r[4]) if len(r) > 4 and r[4] else 0.0,
                            interest_rate=float(r[5]) if len(r) > 5 and r[5] else 0.0,
                            start_date=r[6] if len(r) > 6 and r[6] else "",
                            due_date=r[7] if len(r) > 7 and r[7] else None,
                            status=r[8] if len(r) > 8 and r[8] else "Active"
                        ))
                    except Exception as parse_err:
                        logger.warning(f"Error parsing liability row '{r[1]}': {parse_err}")
            return liabilities
        except Exception as e:
            logger.error(f"Error reading liabilities from Sheets: {e}")
            return []

    # ─────────────────────────────────────────────
    # AUDIT LOG
    # ─────────────────────────────────────────────

    def save_audit_log(self, audit: AuditLog) -> None:
        try:
            sheet = self._sheet("Audit_Log")
            action_val = audit.action.value if hasattr(audit.action, 'value') else str(audit.action)
            row_data = [
                audit.audit_id,
                audit.timestamp,
                audit.entity_type,
                audit.entity_id,
                action_val,
                audit.old_value or "",
                audit.new_value or "",
                audit.actor,
                audit.reason or ""
            ]
            sheet.append_row(row_data)
        except Exception as e:
            logger.error(f"Error saving audit log to Sheets: {e}")
            raise

    def get_all_audit_logs(self) -> List[AuditLog]:
        try:
            sheet = self._sheet("Audit_Log")
            rows = sheet.get_all_values()
            logs = []
            for r in rows[1:]:
                if len(r) >= 5 and r[0].strip():
                    try:
                        logs.append(AuditLog(
                            audit_id=r[0],
                            timestamp=r[1] if len(r) > 1 and r[1] else datetime.now().isoformat(),
                            entity_type=r[2] if len(r) > 2 and r[2] else "",
                            entity_id=r[3] if len(r) > 3 and r[3] else "",
                            action=r[4] if len(r) > 4 and r[4] else "UPDATE",
                            old_value=r[5] if len(r) > 5 and r[5] else None,
                            new_value=r[6] if len(r) > 6 and r[6] else None,
                            actor=r[7] if len(r) > 7 and r[7] else "System",
                            reason=r[8] if len(r) > 8 and r[8] else ""
                        ))
                    except Exception as parse_err:
                        logger.warning(f"Error parsing audit log row: {parse_err}")
            return logs
        except Exception as e:
            logger.error(f"Error reading audit logs from Sheets: {e}")
            return []
