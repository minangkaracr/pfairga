from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field

class TransactionType(str, Enum):
    INCOME = "Income"
    EXPENSE = "Expense"
    TRANSFER = "Transfer"
    ASSET_ACQUISITION = "Asset Acquisition"
    LIABILITY = "Liability"
    LIABILITY_PAYMENT = "Liability Payment"
    INVESTMENT = "Investment"
    ADJUSTMENT = "Adjustment"

class AccountType(str, Enum):
    CASH = "Cash"
    BANK = "Bank"
    EWALLET = "E-Wallet"
    PREPAID = "Prepaid"
    CREDIT_CARD = "Credit Card"
    INVESTMENT = "Investment"
    LIABILITY_ACCOUNT = "Liability Account"

class CategoryType(str, Enum):
    INCOME = "Income"
    EXPENSE = "Expense"
    ASSET = "Asset"
    LIABILITY = "Liability"
    TRANSFER = "Transfer"
    INVESTMENT = "Investment"

class TransactionStatus(str, Enum):
    POSTED = "Posted"
    PENDING = "Pending"
    VOIDED = "Voided"
    REVERSED = "Reversed"

class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VOID = "VOID"
    REVERSE = "REVERSE"
    SYSTEM_ADJUSTMENT = "SYSTEM_ADJUSTMENT"

class Transaction(BaseModel):
    transaction_id: str
    transaction_date: str  # YYYY-MM-DD
    recorded_at: str  # ISO format string
    type: TransactionType
    description: str
    amount: float
    currency: str = "IDR"
    account: str  # Source account name / ID
    destination_account: Optional[str] = None  # For Transfers or Asset/Liability accounts
    category: str
    asset_id: Optional[str] = None
    liability_id: Optional[str] = None
    status: TransactionStatus = TransactionStatus.POSTED
    source: str = "Telegram"
    ai_confidence: float = 1.0
    created_by: str = "User"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Account(BaseModel):
    account_id: str
    account_name: str
    account_type: AccountType
    currency: str = "IDR"
    opening_balance: float = 0.0
    current_balance: float = 0.0
    status: str = "Active"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Category(BaseModel):
    category_id: str
    category_name: str
    category_type: CategoryType
    parent_category: Optional[str] = None
    description: Optional[str] = ""
    created_by: str = "System"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "Active"

class CategoryAlias(BaseModel):
    alias_id: str
    alias: str
    category_id: str
    category_name: str
    created_by: str = "System"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Asset(BaseModel):
    asset_id: str
    asset_name: str
    asset_category: str
    acquisition_date: str  # YYYY-MM-DD
    acquisition_cost: float
    useful_life_years: float = 5.0
    depreciation_method: str = "Straight Line"
    accumulated_depreciation: float = 0.0
    net_book_value: float = 0.0
    status: str = "Active"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Liability(BaseModel):
    liability_id: str
    liability_name: str
    liability_type: str  # Credit Card, Installment, Loan, PayLater
    principal_amount: float
    outstanding_balance: float
    interest_rate: float = 0.0
    start_date: str
    due_date: Optional[str] = None
    status: str = "Active"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class AuditLog(BaseModel):
    audit_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    entity_type: str  # Transaction, Account, Asset, Liability, Category
    entity_id: str
    action: AuditAction
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    actor: str = "User"
    reason: Optional[str] = ""
