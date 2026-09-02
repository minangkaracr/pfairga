from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.accounting.models import TransactionType

class ParsedItem(BaseModel):
    transaction_type: TransactionType = TransactionType.EXPENSE
    description: str
    amount: float
    currency: str = "IDR"
    account: Optional[str] = None
    destination_account: Optional[str] = None
    category: str = "Food & Beverage"
    transaction_date: str  # YYYY-MM-DD
    useful_life_years: Optional[float] = None  # If Asset Acquisition

class AIStructuredResult(BaseModel):
    is_financial_transaction: bool = True
    intent: str = "record_transaction"  # record_transaction, setup, query, correction
    items: List[ParsedItem] = Field(default_factory=list)
    missing_critical_fields: List[str] = Field(default_factory=list)  # e.g., ["account"]
    clarification_prompt: Optional[str] = None
    confidence_score: float = 0.95
    reasoning: Optional[str] = None

class BaseAIProvider(ABC):
    """Abstract AI Provider interface."""

    @abstractmethod
    def parse_financial_input(
        self,
        user_input: str,
        current_date_str: str,
        existing_accounts: List[str],
        existing_categories: List[str],
        existing_aliases: Dict[str, str]
    ) -> AIStructuredResult:
        pass
