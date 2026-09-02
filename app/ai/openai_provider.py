import json
import logging
from typing import List, Dict
from app import config
from app.ai.base import BaseAIProvider, AIStructuredResult, ParsedItem
from app.ai.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider adapter."""

    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.fallback_provider = GeminiProvider()

    def parse_financial_input(
        self,
        user_input: str,
        current_date_str: str,
        existing_accounts: List[str],
        existing_categories: List[str],
        existing_aliases: Dict[str, str]
    ) -> AIStructuredResult:
        if not self.api_key:
            return self.fallback_provider.parse_financial_input(
                user_input, current_date_str, existing_accounts, existing_categories, existing_aliases
            )

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            prompt = f"""
Target Date: {current_date_str}
User input: "{user_input}"
Accounts: {existing_accounts}
Categories: {existing_categories}
Aliases: {existing_aliases}
Parse as JSON financial transaction.
"""
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            items = [ParsedItem(**i) for i in data.get("items", [])]
            return AIStructuredResult(
                is_financial_transaction=data.get("is_financial_transaction", True),
                intent=data.get("intent", "record_transaction"),
                items=items,
                missing_critical_fields=data.get("missing_critical_fields", []),
                clarification_prompt=data.get("clarification_prompt"),
                confidence_score=data.get("confidence_score", 0.95),
                reasoning=data.get("reasoning")
            )
        except Exception as e:
            logger.error(f"OpenAI parsing failed ({e}). Using Gemini fallback.")
            return self.fallback_provider.parse_financial_input(
                user_input, current_date_str, existing_accounts, existing_categories, existing_aliases
            )
