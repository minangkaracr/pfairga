from app.sheets.sheets_storage import SheetsStorage
from app.accounting.statements import FinancialStatementGenerator

storage = SheetsStorage()
gen = FinancialStatementGenerator(storage)
bs = gen.generate_balance_sheet()

ast = bs['assets']
lia = bs['liabilities']
eq = bs['equity']

print('=== ASSETS ===')
for k, v in ast.items():
    print(f'  {k}: {v:,.0f}')

print('\n=== LIABILITIES ===')
for k, v in lia.items():
    print(f'  {k}: {v:,.0f}')

print('\n=== EQUITY ===')
for k, v in eq.items():
    print(f'  {k}: {v:,.0f}')

total_assets = ast['total_assets']
total_lia = lia['total_liabilities']
total_eq = eq['total_equity']
liab_equity = bs['liabilities_and_equity']
net_worth = bs['net_worth']

print(f'\nTotal Assets:            {total_assets:,.0f}')
print(f'Total Liabilities:       {total_lia:,.0f}')
print(f'Total Equity:            {total_eq:,.0f}')
print(f'Liabilities + Equity:    {liab_equity:,.0f}')
print(f'NET WORTH (Assets-Lia):  {net_worth:,.0f}')
print(f'Is Balanced?             {bs["is_balanced"]}')
print(f'Discrepancy:             {bs["discrepancy"]:,.2f}')

# Show accounts breakdown
print('\n=== ACCOUNTS ===')
accounts = storage.get_all_accounts()
for acc in accounts:
    print(f'  {acc.account_name} ({acc.account_type}) | opening={acc.opening_balance:,.0f} | current={acc.current_balance:,.0f} | status={acc.status}')

print('\n=== ASSETS (fixed) ===')
assets_list = storage.get_all_assets()
for a in assets_list:
    print(f'  {a.asset_name} | NBV={a.net_book_value:,.0f} | status={a.status}')

print('\n=== TRANSACTIONS summary ===')
txs = storage.get_all_transactions()
income = sum(t.amount for t in txs if t.status.value == 'Posted' and t.type.value == 'Income')
expense = sum(t.amount for t in txs if t.status.value == 'Posted' and t.type.value == 'Expense')
print(f'  Total Income (posted):  {income:,.0f}')
print(f'  Total Expense (posted): {expense:,.0f}')
print(f'  Net Income:             {income - expense:,.0f}')
