import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app import config
from app.ai.base import BaseAIProvider, AIStructuredResult, ParsedItem
from app.accounting.models import TransactionType

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    """
    Google Gemini AI Provider implementation using free Google AI Studio API key.
    Includes deterministic offline regex fallback parser for standalone execution.
    """

    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini Client with Google AI Studio key.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini SDK ({e}). Fallback parser active.")

    def parse_financial_input(
        self,
        user_input: str,
        current_date_str: str,
        existing_accounts: List[str],
        existing_categories: List[str],
        existing_aliases: Dict[str, str]
    ) -> AIStructuredResult:
        if self.client:
            try:
                return self._call_gemini_api(
                    user_input, current_date_str, existing_accounts, existing_categories, existing_aliases
                )
            except Exception as e:
                logger.error(f"Gemini API call failed ({e}). Reverting to Rule-Based Fallback Parser.")

        return self._fallback_rule_based_parser(
            user_input, current_date_str, existing_accounts, existing_categories, existing_aliases
        )

    def _call_gemini_api(
        self,
        user_input: str,
        current_date_str: str,
        existing_accounts: List[str],
        existing_categories: List[str],
        existing_aliases: Dict[str, str]
    ) -> AIStructuredResult:
        prompt = f"""
You are an expert Personal Finance AI Accountant.
Target Date for context: {current_date_str}

Existing Accounts: {json.dumps(existing_accounts)}
Existing Categories: {json.dumps(existing_categories)}
Known Aliases: {json.dumps(existing_aliases)}

User input: "{user_input}"

Rules:
1. Determine if input is a financial transaction.
2. Classify transaction type strictly into: "Income", "Expense", "Transfer", "Asset Acquisition", "Liability", "Liability Payment".
   - Top-up / transfer between accounts (e.g. GoPay from BRI) = "Transfer".
   - Salary / receive money = "Income".
   - Expensive durable goods (e.g. laptop, smartphone) = "Asset Acquisition".
   - Paying credit card / loan = "Liability Payment".
   - Regular spending = "Expense".
3. Extract amount in IDR numeric float (e.g. "35 ribu" -> 35000, "10 juta" -> 10000000).
4. Resolve date (e.g., "kemarin" -> subtract 1 day from {current_date_str}).
5. Identify source account and destination account (if transfer).
6. Match category from Existing Categories if one clearly fits. If none fits well, suggest a NEW specific and meaningful category name in English (e.g. "Health & Beauty", "Personal Care", "Groceries", "Subscriptions", "Pets"). NEVER default to "Food & Beverage" for non-food items. NEVER use "Other" as a category.
7. If critical information (e.g. account) is missing and cannot be inferred, list missing fields in `missing_critical_fields` and provide a friendly Bahasa Indonesia `clarification_prompt`.

Return JSON strictly matching this structure:
{{
  "is_financial_transaction": true,
  "intent": "record_transaction",
  "items": [
    {{
      "transaction_type": "Expense",
      "description": "Makan",
      "amount": 35000,
      "currency": "IDR",
      "account": "GoPay",
      "destination_account": null,
      "category": "Food & Beverage",
      "transaction_date": "{current_date_str}",
      "useful_life_years": null
    }}
  ],
  "missing_critical_fields": [],
  "clarification_prompt": null,
  "confidence_score": 0.95,
  "reasoning": "Clear expense transaction"
}}
"""
        response = None
        for model_name in ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-001"]:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                break
            except Exception as e:
                logger.warning(f"Gemini model {model_name} failed: {e}")

        if not response:
            raise RuntimeError("All Gemini model calls failed.")

        data = json.loads(response.text)
        items = [ParsedItem(**item) for item in data.get("items", [])]
        return AIStructuredResult(
            is_financial_transaction=data.get("is_financial_transaction", True),
            intent=data.get("intent", "record_transaction"),
            items=items,
            missing_critical_fields=data.get("missing_critical_fields", []),
            clarification_prompt=data.get("clarification_prompt"),
            confidence_score=data.get("confidence_score", 0.95),
            reasoning=data.get("reasoning")
        )

    def _fallback_rule_based_parser(
        self,
        user_input: str,
        current_date_str: str,
        existing_accounts: List[str],
        existing_categories: List[str],
        existing_aliases: Dict[str, str]
    ) -> AIStructuredResult:
        """Deterministic NLP Fallback for local testing without internet/API keys."""
        text = user_input.lower().strip()

        if text.startswith("setup") or text.startswith("set saldo") or text.startswith("saldo awal"):
            return AIStructuredResult(
                is_financial_transaction=False,
                intent="setup_account",
                items=[],
                confidence_score=1.0,
                reasoning="Setup account command"
            )

        # 1. Parse Date
        tx_date = current_date_str
        if "kemarin" in text:
            dt = datetime.strptime(current_date_str, "%Y-%m-%d") - timedelta(days=1)
            tx_date = dt.strftime("%Y-%m-%d")

        # 2. Parse Amount (e.g. 35 ribu, 35k, 10 juta, 500.000, 50000)
        amount = 0.0
        juta_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:juta|jt|mian|m)", text)
        ribu_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:ribu|rb|k)", text)
        raw_num_match = re.search(r"(?:rp\.?\s*)?(\d{1,3}(?:\.\d{3})+|\d+)", text)

        if juta_match:
            amount = float(juta_match.group(1).replace(",", ".")) * 1_000_000
        elif ribu_match:
            amount = float(ribu_match.group(1).replace(",", ".")) * 1_000
        elif raw_num_match:
            num_str = raw_num_match.group(1).replace(".", "")
            amount = float(num_str)

        # 3. Identify Accounts
        found_accounts = []
        for acc in existing_accounts:
            if acc.lower() in text:
                found_accounts.append(acc)

        if "gopay" in text and "GoPay" not in found_accounts:
            found_accounts.append("GoPay")
        if "bri" in text and "BRI" not in found_accounts:
            found_accounts.append("BRI")
        if "bca" in text and "BCA" not in found_accounts:
            found_accounts.append("BCA")
        if "ovo" in text and "OVO" not in found_accounts:
            found_accounts.append("OVO")
        if "cash" in text or "tunai" in text:
            if "Cash" not in found_accounts:
                found_accounts.append("Cash")

        # 4. Determine Transaction Type & Category
        tx_type = TransactionType.EXPENSE
        category = "Food & Beverage"
        dest_account = None

        if "top up" in text or "topup" in text or "transfer" in text or "pindah" in text:
            tx_type = TransactionType.TRANSFER
            category = "Transfer"
            if len(found_accounts) >= 2:
                # e.g., Top up GoPay dari BRI -> source BRI, dest GoPay
                if "dari" in text:
                    parts = text.split("dari")
                    source_part = parts[1]
                    dest_part = parts[0]
                    src = next((a for a in found_accounts if a.lower() in source_part), found_accounts[0])
                    dst = next((a for a in found_accounts if a.lower() in dest_part), found_accounts[-1])
                    account = src
                    dest_account = dst
                else:
                    account = found_accounts[0]
                    dest_account = found_accounts[1]
            elif len(found_accounts) == 1:
                account = found_accounts[0]
            else:
                account = "BRI"
                dest_account = "GoPay"

        elif "gaji" in text or "income" in text or "masuk" in text or "terima" in text:
            tx_type = TransactionType.INCOME
            category = "Salary"
            account = found_accounts[0] if found_accounts else "BRI"

        elif "laptop" in text or "hp" in text or "motor" in text or "tv" in text:
            tx_type = TransactionType.ASSET_ACQUISITION
            category = "Electronics"
            account = found_accounts[0] if found_accounts else "BRI"

        elif "kartu kredit" in text or "bayar cc" in text or "bayar kartu kredit" in text:
            if "bayar" in text:
                tx_type = TransactionType.LIABILITY_PAYMENT
                category = "Credit Card Payment"
                account = found_accounts[0] if found_accounts else "BRI"
                dest_account = "BRI Credit Card"
            else:
                tx_type = TransactionType.EXPENSE
                category = "Shopping"
                account = "BRI Credit Card"
        else:
            tx_type = TransactionType.EXPENSE
            account = found_accounts[0] if found_accounts else None

            # Category resolution: check aliases first
            resolved_category = None
            for word in text.split():
                if word in existing_aliases:
                    resolved_category = existing_aliases[word]
                    break

            # If no alias matched, use keyword-based smart categorization
            if not resolved_category:
                if any(w in text for w in ["masker", "skincare", "sabun", "shampo", "vitamin", "obat", "apotek", "klinik", "dokter", "rs ", "rumah sakit"]):
                    resolved_category = "Health & Beauty"
                elif any(w in text for w in ["makan", "minum", "kopi", "coffee", "cafe", "resto", "warung", "bakso", "nasi", "ayam", "soto", "snack"]):
                    resolved_category = "Food & Beverage"
                elif any(w in text for w in ["bensin", "parkir", "tol", "grab", "gojek", "ojol", "bus", "kereta", "tiket"]):
                    resolved_category = "Transportation"
                elif any(w in text for w in ["listrik", "air", "pdam", "internet", "wifi", "pulsa", "token"]):
                    resolved_category = "Utilities"
                elif any(w in text for w in ["baju", "sepatu", "celana", "pakaian", "fashion", "tas"]):
                    resolved_category = "Shopping"
                elif any(w in text for w in ["netflix", "spotify", "bioskop", "game", "hiburan"]):
                    resolved_category = "Entertainment"
                elif any(w in text for w in ["kost", "sewa", "kontrakan", "rumah"]):
                    resolved_category = "Housing"
                else:
                    # Derive a new meaningful category from significant words in the input
                    # Strip common stopwords and use the most descriptive word as category
                    stopwords = {"beli", "beli", "via", "dari", "ke", "di", "untuk", "dengan", "pakai",
                                 "the", "a", "an", "and", "or", "in", "on", "at", "by", "of",
                                 "aku", "saya", "kita", "ini", "itu", "yang", "ada", "sudah", "tadi"}
                    words = [w for w in text.split() if len(w) > 3 and w not in stopwords]
                    # Skip account names
                    account_names_lower = [a.lower() for a in existing_accounts]
                    meaningful = [w for w in words if w not in account_names_lower]
                    if meaningful:
                        resolved_category = meaningful[0].title()
                    else:
                        resolved_category = user_input.strip().split()[0].title() if user_input.strip() else "Expense"

            category = resolved_category

        # Check missing critical fields
        missing = []
        clarification = None

        if not account and tx_type != TransactionType.TRANSFER:
            missing.append("account")
            clarification = (
                f"Saya mendeteksi transaksi pengeluaran {category} sebesar Rp{amount:,.0f}.\n"
                f"Account belum diketahui. Dibayar menggunakan apa (misal: GoPay, BRI, Cash)?"
            )

        item = ParsedItem(
            transaction_type=tx_type,
            description=user_input.capitalize(),
            amount=amount if amount > 0 else 50000,
            account=account or "GoPay",
            destination_account=dest_account,
            category=category,
            transaction_date=tx_date
        )

        return AIStructuredResult(
            is_financial_transaction=True,
            intent="record_transaction",
            items=[item],
            missing_critical_fields=missing,
            clarification_prompt=clarification,
            confidence_score=0.90,
            reasoning="Parsed via deterministic rule-based fallback engine."
        )
