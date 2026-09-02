import logging
from datetime import date
from typing import List, Dict, Tuple
from app import config
from app.ai.base import BaseAIProvider, AIStructuredResult
from app.ai.gemini_provider import GeminiProvider
from app.ai.openai_provider import OpenAIProvider
from app.storage.base import BaseStorage
from app.accounting.models import Category, CategoryType, CategoryAlias
import uuid

logger = logging.getLogger(__name__)

class AIParserService:
    """
    High-level AI Parser Service coordinating providers, alias resolution,
    category normalization, and missing attribute dialog handling.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        if config.AI_PROVIDER == "openai":
            self.provider: BaseAIProvider = OpenAIProvider()
        else:
            self.provider: BaseAIProvider = GeminiProvider()

    def parse_user_message(self, user_input: str, target_date: str = None) -> AIStructuredResult:
        if not target_date:
            target_date = date.today().strftime("%Y-%m-%d")

        # 1. Fetch current context from storage
        existing_accounts = [acc.account_name for acc in self.storage.get_all_accounts()]
        existing_categories = [cat.category_name for cat in self.storage.get_all_categories()]
        aliases = {a.alias.lower(): a.category_name for a in self.storage.get_all_category_aliases()}

        # 2. Call AI provider
        result = self.provider.parse_financial_input(
            user_input=user_input,
            current_date_str=target_date,
            existing_accounts=existing_accounts,
            existing_categories=existing_categories,
            existing_aliases=aliases
        )

        # 3. Post-process categories: Normalize and auto-create missing categories (BR-018, BR-025)
        for item in result.items:
            cat_name = item.category.strip()
            if cat_name.lower() in aliases:
                item.category = aliases[cat_name.lower()]
            elif cat_name not in existing_categories:
                # Auto-register new category in master (BR-018)
                new_cat = Category(
                    category_id=f"CAT-{uuid.uuid4().hex[:8].upper()}",
                    category_name=cat_name,
                    category_type=CategoryType.EXPENSE,
                    description="Auto-created by AI",
                    created_by="AI"
                )
                self.storage.save_category(new_cat)
                existing_categories.append(cat_name)

        return result
