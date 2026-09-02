"""
Helper script to initialize Google Sheets worksheets and header columns according to BRD §49-56.
"""
import sys
import logging
from app import config
from app.sheets.sheets_storage import SheetsStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHEET_SCHEMAS = {
    "Transactions": [
        "transaction_id", "date", "recorded_at", "type", "description", "amount",
        "currency", "account", "destination_account", "category", "asset_id",
        "liability_id", "status", "source", "ai_confidence", "created_by", "created_at", "updated_at"
    ],
    "Accounts": [
        "account_id", "account_name", "account_type", "currency", "opening_balance",
        "current_balance", "status", "created_at", "updated_at"
    ],
    "Categories": [
        "category_id", "category_name", "category_type", "parent_category",
        "description", "created_by", "created_at", "status"
    ],
    "Category_Aliases": [
        "alias_id", "alias", "category_id", "category_name", "created_by", "created_at"
    ],
    "Assets": [
        "asset_id", "asset_name", "asset_category", "acquisition_date", "acquisition_cost",
        "useful_life_years", "depreciation_method", "accumulated_depreciation", "net_book_value", "status"
    ],
    "Liabilities": [
        "liability_id", "liability_name", "liability_type", "principal_amount",
        "outstanding_balance", "interest_rate", "start_date", "due_date", "status"
    ],
    "Installments": [
        "installment_id", "item_name", "total_amount", "monthly_amount", "tenor_months",
        "paid_months", "remaining_balance", "source_account", "status"
    ],
    "Investments": [
        "investment_id", "asset_name", "asset_type", "units", "cost_basis", "current_value", "updated_at"
    ],
    "Audit_Log": [
        "audit_id", "timestamp", "entity_type", "entity_id", "action", "old_value", "new_value", "actor", "reason"
    ],
    "Settings": [
        "key", "value", "description"
    ],
    "Monthly_Summary": [
        "period", "total_income", "total_expense", "net_income", "total_assets", "total_liabilities", "net_worth"
    ],
    "Income_Statement": [
        "category", "category_type", "amount", "period"
    ],
    "Balance_Sheet": [
        "component", "type", "amount", "timestamp"
    ]
}

def init_google_sheets():
    logger.info("Initializing Google Sheets structure...")
    storage = SheetsStorage()
    
    if not storage.spreadsheet:
        logger.error("❌ Google Sheets not connected! Check GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_SHEETS_SPREADSHEET_ID in .env.")
        sys.exit(1)

    spreadsheet = storage.spreadsheet
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]

    for sheet_name, headers in SHEET_SCHEMAS.items():
        if sheet_name not in existing_sheets:
            logger.info(f"Creating sheet '{sheet_name}'...")
            ws = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols=str(len(headers)))
            ws.append_row(headers)
        else:
            logger.info(f"Sheet '{sheet_name}' already exists. Verifying headers...")
            ws = spreadsheet.worksheet(sheet_name)
            rows = ws.get_all_values()
            if not rows:
                ws.append_row(headers)

    logger.info("🎉 Google Sheets initialization complete! All 13 worksheets are ready.")

if __name__ == "__main__":
    init_google_sheets()
