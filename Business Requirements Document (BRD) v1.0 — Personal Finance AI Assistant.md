# Business Requirements Document (BRD) v1.0
## Personal Finance AI Assistant — Telegram + Google Sheets

**Document Version:** 1.0  
**Product Type:** Personal Finance Management System  
**Target User:** Single Personal User  
**Primary Interface:** Telegram Bot  
**Database / Source of Truth:** Google Sheets  
**AI Layer:** Provider-agnostic, free API provider  
**Reporting:** Telegram + downloadable PDF  
**Currency — MVP:** IDR  
**Status:** Initial Product Requirements

---

# 1. Executive Summary

Personal Finance AI Assistant adalah sistem pencatatan dan analisis keuangan pribadi yang memungkinkan user mencatat transaksi melalui Telegram menggunakan bahasa natural.

Sistem menggunakan AI untuk memahami input user, kemudian mengubahnya menjadi struktur transaksi yang dapat diproses oleh accounting engine. Google Sheets digunakan sebagai persistent data store dan source of truth.

Sistem tidak hanya mencatat pemasukan dan pengeluaran, tetapi juga memahami:

- rekening bank
- cash
- e-wallet
- prepaid balance seperti BRIZZI
- transfer antar-account
- aset
- liability
- cicilan
- investasi
- depresiasi aset
- income
- operational expense
- net worth
- balance sheet
- income statement
- historical transaction changes

Prinsip utama sistem:

> **AI memahami maksud user. Accounting Engine memastikan angka dan financial statement tetap benar.**

---

# 2. Product Vision

Membangun personal finance assistant yang memungkinkan user mengelola kondisi keuangan hanya dengan berbicara secara natural melalui Telegram.

User tidak perlu memahami accounting secara mendalam untuk menggunakan sistem.

Contoh:

> "Tadi beli makan 35 ribu pakai GoPay."

Sistem harus dapat memahami bahwa:

- transaction type = expense
- amount = Rp35.000
- category = Food & Beverage
- account = GoPay
- transaction date = hari ini
- GoPay balance berkurang Rp35.000
- expense bertambah Rp35.000

Contoh lain:

> "Top up GoPay 500 ribu dari BRI."

Sistem harus memahami bahwa ini **bukan expense**, melainkan transfer antar-account:

- BRI −Rp500.000
- GoPay +Rp500.000

---

# 3. Problem Statement

Pencatatan keuangan pribadi secara manual memiliki beberapa masalah:

1. User malas melakukan input transaksi satu per satu.
2. User sering menggunakan bahasa natural yang tidak cocok dengan format spreadsheet.
3. Kategori transaksi dapat tidak konsisten.
4. Transfer antar rekening sering salah dianggap sebagai expense.
5. Pembelian aset dapat salah dianggap sebagai expense.
6. Cicilan dapat salah dicatat sebagai expense penuh.
7. Kondisi balance sheet sulit dipelihara secara manual.
8. Perubahan transaksi historis dapat menyebabkan laporan keuangan tidak konsisten.
9. User membutuhkan cara cepat untuk mengetahui:
   - pengeluaran bulan ini
   - pemasukan bulan ini
   - saldo account
   - liability
   - asset
   - net worth
   - financial position
10. User membutuhkan sistem yang memahami konteks transaksi, bukan hanya keyword matching.

---

# 4. Product Objectives

## 4.1 Primary Objectives

Sistem harus:

1. Memungkinkan pencatatan transaksi melalui Telegram.
2. Mendukung natural-language transaction input.
3. Menggunakan AI untuk memahami transaksi.
4. Mengotomatisasi categorization.
5. Memelihara account balance.
6. Memelihara asset dan liability.
7. Memelihara income statement.
8. Memelihara balance sheet.
9. Menghitung net worth.
10. Mendukung depreciation sederhana.
11. Menyediakan audit trail.
12. Menyediakan PDF financial report.
13. Menjaga accounting consistency.

## 4.2 Secondary Objectives

Sistem harus dapat:

- memahami tanggal transaksi historis
- memahami synonym/category alias
- membuat category baru secara otomatis
- melakukan correction transaksi melalui natural language
- memberikan confirmation ketika informasi transaksi belum lengkap
- memberikan warning jika terjadi accounting inconsistency

---

# 5. Non-Goals / Out of Scope MVP

Fitur berikut tidak menjadi bagian MVP:

- multi-user
- mobile application
- public web application
- live web dashboard
- multi-currency
- bank API integration
- automatic bank transaction import
- automatic e-wallet API integration
- stock market live price integration
- advanced investment portfolio management
- tax reporting
- tax calculation
- advanced budgeting
- financial forecasting
- advanced depreciation methods
- automated financial recommendations
- automatic financial product recommendations

Fitur tersebut dapat masuk Phase 2 atau Phase 3.

---

# 6. Target User

## 6.1 Persona

**Primary User:** Individual personal finance owner.

Karakteristik:

- memiliki beberapa bank/account
- menggunakan e-wallet
- memiliki asset
- dapat memiliki credit card / installment
- melakukan transaksi sehari-hari
- tidak ingin melakukan manual spreadsheet entry
- ingin memahami financial position secara keseluruhan

## 6.2 User Goal

User ingin dapat berkata:

> "Aku habis ngapain saja dengan uangku?"

dan sistem mampu menjawab secara akurat.

---

# 7. Product Scope

MVP terdiri dari:

### Transaction Management
- Income
- Expense
- Transfer
- Asset acquisition
- Liability
- Liability payment
- Investment transaction
- Adjustment

### Account Management
- Bank account
- Cash
- E-wallet
- Prepaid account
- Credit card
- Investment account

### Financial Statements
- Income Statement
- Balance Sheet
- Net Worth
- Account Balance

### AI
- Natural language understanding
- Category classification
- Account identification
- Transaction type identification
- Date extraction
- Asset vs expense classification
- Liability classification
- Entity normalization
- Category alias management

### Telegram
- `/start`
- `/setup`
- `/catat`
- `/summary`
- `/balance`
- `/expense`
- `/income`
- `/accounts`
- `/debt`
- `/report`
- `/help`

### Data
- Google Sheets
- Audit trail
- Master data
- Financial statements

### Reporting
- Telegram summary
- Downloadable PDF

---

# 8. High-Level Architecture

```text
Telegram User
      │
      ▼
Telegram Bot
      │
      ▼
Backend / Application Layer
      │
      ├──────────────► AI Provider
      │                    │
      │                    ▼
      │              Structured Intent
      │
      ▼
Transaction Validator
      │
      ▼
Confirmation Layer
      │
      ▼
Accounting Engine
      │
      ├──────────────► Transaction Ledger
      ├──────────────► Account Balances
      ├──────────────► Assets
      ├──────────────► Liabilities
      └──────────────► Financial Statements
                         │
                         ▼
                    Google Sheets
                         │
                         ▼
                  Reporting Engine
                         │
                         ▼
                   Telegram / PDF
```

---

# 9. Core Design Principle

## 9.1 AI Is Not The Accounting Engine

AI bertugas:

> Understand → Classify → Extract → Suggest

Accounting engine bertugas:

> Validate → Calculate → Post → Maintain Financial Integrity

AI tidak boleh memiliki direct unrestricted access untuk mengubah Google Sheets.

---

# 10. Transaction Model

Setiap transaksi minimal memiliki:

| Field | Description |
|---|---|
| transaction_id | Unique transaction identifier |
| transaction_date | Date transaction actually occurred |
| recorded_at | Date/time transaction entered |
| type | Income / Expense / Transfer / Asset / Liability / etc. |
| description | Transaction description |
| amount | Transaction amount |
| currency | IDR |
| account | Source/destination account |
| category | Financial category |
| asset_id | Related asset if applicable |
| liability_id | Related liability if applicable |
| status | Posted / Pending / Voided / Reversed |
| source | Telegram |
| ai_confidence | AI confidence score |
| created_by | User / AI / System |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |

---

# 11. Account Model

Account adalah tempat uang atau financial value berada.

Contoh:

### Cash
- Cash

### Bank
- BRI
- BCA

### E-Wallet
- GoPay
- OVO

### Prepaid
- BRIZZI

### Investment
- Reksa Dana
- Gold

### Liability Account
- BRI Credit Card
- Installment

Account harus memiliki running balance.

---

# 12. Account Balance Rules

Untuk asset/cash account:

> Current Balance = Previous Balance + Inflows − Outflows

Contoh:

GoPay:

Opening balance = Rp0

Top up:

+Rp50.000

Expense:

−Rp22.000

Current balance:

**Rp28.000**

---

# 13. Transfer Rules

Transfer antar-account tidak dianggap sebagai income atau expense.

## Example

User:

> "Top up GoPay 50 ribu dari BRI."

Accounting:

```text
BRI       -50.000
GoPay     +50.000
```

Income Statement:

```text
No impact
```

Balance Sheet:

```text
Total Assets
No net change
```

---

# 14. Expense Rules

Expense mengurangi equity/net income dan mengurangi account balance.

Example:

> "Makan Rp22.000 pakai GoPay."

Accounting:

```text
GoPay              -22.000
Food & Beverage    +22.000 Expense
```

Income Statement:

```text
Food & Beverage    Rp22.000
```

---

# 15. Income Rules

Example:

> "Gaji bulan ini 10 juta masuk BRI."

Accounting:

```text
BRI             +10.000.000
Salary Income   +10.000.000
```

Income Statement:

```text
Salary Income   Rp10.000.000
```

---

# 16. Asset Acquisition

AI harus dapat membedakan operational expense dengan asset acquisition.

Example:

> "Beli laptop Rp15 juta pakai BRI."

Accounting:

```text
Laptop Asset       +15.000.000
BRI                -15.000.000
```

Tidak dicatat sebagai operational expense penuh pada saat pembelian.

Balance Sheet:

```text
Assets
Laptop             Rp15.000.000
BRI                berkurang Rp15.000.000
```

---

# 17. Asset Depreciation

MVP menggunakan **straight-line depreciation**.

Formula:

```text
Annual Depreciation =
Acquisition Cost / Useful Life
```

Contoh:

Laptop:

Cost = Rp15.000.000  
Useful life = 5 tahun

Annual depreciation:

```text
15.000.000 / 5
= 3.000.000 per year
```

Monthly depreciation:

```text
3.000.000 / 12
= 250.000 per month
```

Balance Sheet:

```text
Gross Asset Value
- Accumulated Depreciation
= Net Book Value
```

User dapat mengatur useful life pada asset configuration.

---

# 18. Asset Master

Asset minimal memiliki:

| Field | Description |
|---|---|
| asset_id | Unique ID |
| asset_name | Name |
| asset_category | Category |
| acquisition_date | Purchase date |
| acquisition_cost | Initial value |
| useful_life | Years |
| depreciation_method | Straight Line |
| accumulated_depreciation | Current accumulated depreciation |
| net_book_value | Current book value |
| status | Active / Disposed |

---

# 19. Liability

Liability merepresentasikan kewajiban finansial user.

Examples:

- Credit Card
- Personal Loan
- Installment
- PayLater

Liability harus memiliki balance.

Example:

Credit Card:

```text
Opening Liability      Rp3.300.000
New Credit Card Spend  +Rp500.000
Payment                -Rp1.000.000
Current Liability      Rp2.800.000
```

---

# 20. Installment

Installment bukan sekadar expense category.

Contoh:

Laptop Rp15 juta melalui installment.

Saat liability terbentuk:

```text
Asset              +15M
Liability          +15M
```

Ketika pembayaran dilakukan:

```text
Cash/Bank          -monthly payment
Liability          -principal
Interest Expense   +interest
```

Jika installment tidak memiliki interest, seluruh payment dapat mengurangi principal sesuai outstanding balance.

---

# 21. Credit Card

Credit card diperlakukan sebagai liability account.

Example:

> "Beli sepatu 500 ribu pakai BRI Credit Card."

Accounting:

```text
Shopping Expense       +500.000
Credit Card Liability  +500.000
```

Tidak ada cash outflow pada saat transaksi.

Saat tagihan dibayar:

```text
BRI Bank               -500.000
Credit Card Liability  -500.000
```

Payment bukan expense baru.

---

# 22. Investment

MVP mendukung simple investment tracking.

Investment dapat dicatat sebagai asset.

Contoh:

> "Beli reksa dana Rp1 juta dari BRI."

Accounting:

```text
BRI                 -1.000.000
Investment Asset    +1.000.000
```

Tidak dianggap expense.

Initial launch memungkinkan user mengisi investment account/master secara manual.

---

# 23. Category Management

Category disimpan pada master `Categories`.

AI dapat:

1. memilih existing category
2. menggunakan alias
3. membuat category baru jika konsep benar-benar belum tersedia

AI tidak membutuhkan approval user untuk membuat category.

Namun seluruh category creation dicatat dalam audit trail.

---

# 24. Category Normalization

Sistem harus menghindari duplicate semantic categories.

Example:

```text
coffee
kopi
ngopi
cafe
café
```

harus dapat dipetakan ke category yang sama.

Contoh:

```text
Category:
Food & Beverage

Aliases:
coffee
kopi
ngopi
cafe
café
```

AI harus melakukan semantic normalization, bukan exact string matching.

---

# 25. "Other" Category Policy

Kategori `Other` tidak boleh digunakan sebagai default dumping ground.

Jika AI tidak menemukan category yang cocok:

1. AI mencoba semantic matching.
2. AI mengecek aliases.
3. AI mengecek existing categories.
4. Jika benar-benar tidak ada, AI membuat category baru.
5. Category baru dicatat di master category.

---

# 26. Natural Language Processing

Sistem harus mendukung input seperti:

> "Tadi makan 35 ribu pakai GoPay."

> "Kemarin bayar listrik 200 ribu dari BRI."

> "Gaji bulan ini masuk BRI 10 juta."

> "Top up GoPay 500 ribu dari BRI."

> "Beli laptop 15 juta cash."

> "Bayar kartu kredit 2 juta."

> "Beli kopi 25 ribu."

AI harus mengekstrak:

- transaction date
- transaction type
- amount
- currency
- description
- category
- source account
- destination account
- asset/liability relation
- relevant metadata

---

# 27. Transaction Date

`transaction_date` berbeda dari `recorded_at`.

Example:

User pada 16 August mengatakan:

> "Kemarin makan 50 ribu."

System:

```text
recorded_at      = 16 Aug 2026
transaction_date = 15 Aug 2026
```

Natural language date expression harus diproses berdasarkan timezone user.

---

# 28. Confirmation Engine

Confirmation adalah mandatory ketika informasi penting belum cukup jelas.

Example:

User:

> "Makan 50 ribu."

Bot:

> Saya menemukan:
>
> Expense — Food & Beverage  
> Rp50.000  
> Tanggal: 16 Aug 2026
>
> Account belum diketahui. Dibayar menggunakan apa?

Setelah user menjawab:

> GoPay

System melakukan posting.

---

# 29. Confirmation Principle

System **tidak perlu meminta confirmation untuk hal yang sudah jelas**.

Example:

> "Tadi makan 50 ribu pakai GoPay."

Jika semua field critical telah diketahui dan validation berhasil, transaksi dapat langsung diproses.

Confirmation digunakan untuk **missing information / ambiguity**, bukan setiap transaksi.

---

# 30. AI Confidence

AI harus menghasilkan confidence/uncertainty signal.

Critical fields:

- amount
- date
- transaction type
- account
- category
- asset/liability classification

Jika confidence rendah atau terdapat ambiguity, system harus meminta clarification.

---

# 31. Multi-Transaction Input

User dapat memasukkan beberapa transaksi sekaligus.

Example:

> "Hari ini makan 35 ribu, kopi 20 ribu dan parkir 5 ribu pakai GoPay."

AI harus menghasilkan:

```text
Transaction 1
Food & Beverage
35.000
GoPay

Transaction 2
Food & Beverage
20.000
GoPay

Transaction 3
Parking
5.000
GoPay
```

System dapat meminta satu confirmation untuk keseluruhan batch apabila diperlukan.

---

# 32. Telegram Bot

Telegram merupakan primary interaction interface.

Bot dibuat khusus untuk satu user.

Telegram User ID digunakan sebagai authorization identity.

User lain tidak boleh mengakses financial data.

---

# 33. Telegram Commands

## `/start`

Menampilkan welcome dan status setup.

## `/setup`

Initial financial setup.

## `/catat`

Structured/manual transaction mode.

## `/summary`

Monthly financial summary.

## `/balance`

Current balance sheet / financial position.

## `/expense`

Expense report.

## `/income`

Income report.

## `/accounts`

Current account balances.

## `/debt`

Current liabilities.

## `/report`

Generate PDF financial report.

## `/help`

List commands dan penggunaan natural language.

---

# 34. Natural Language as Primary Interaction

Command bukan satu-satunya method.

User dapat langsung mengirim:

> "Beli makan 30 ribu pakai BRI."

Tanpa `/catat`.

Bot harus memproses message tersebut sebagai potential financial instruction.

---

# 35. Initial Setup

Saat pertama kali digunakan:

```text
/start
   ↓
/setup
   ↓
Accounts
   ↓
Opening Balance
   ↓
Assets
   ↓
Liabilities
   ↓
Investment
   ↓
Categories
   ↓
Depreciation Settings
```

User dapat mengisi data awal sesuai kondisi aktual saat launch.

---

# 36. Account Setup

User dapat mendefinisikan:

- account name
- account type
- opening balance
- currency

Examples:

```text
BRI
BCA
Cash
GoPay
OVO
BRIZZI
```

---

# 37. Opening Balance

Opening balance adalah posisi finansial pada saat sistem mulai digunakan.

Opening balance tidak dianggap sebagai income/expense.

Example:

```text
BRI             Rp10M
GoPay           Rp500K
Cash            Rp1M
Investment      Rp20M
Credit Card     Rp3.3M
```

System menggunakan nilai tersebut sebagai starting financial position.

---

# 38. Financial Statements

MVP menghasilkan:

1. Income Statement
2. Balance Sheet
3. Net Worth
4. Account Balance Summary
5. Expense Breakdown
6. Income Breakdown

---

# 39. Income Statement

Minimal:

```text
Income
  Salary
  Other Income

Total Income

Expenses
  Food & Beverage
  Transportation
  Housing
  Shopping
  etc.

Total Expenses

Net Income
```

Period dapat berupa:

- current month
- previous month
- custom period

---

# 40. Balance Sheet

Format:

```text
ASSETS

Cash & Bank
E-Wallet
Prepaid
Investment
Fixed Assets
Other Assets

TOTAL ASSETS


LIABILITIES

Credit Card
Installment
Loan
Other Liabilities

TOTAL LIABILITIES


EQUITY

Opening Equity
Accumulated Net Income
Adjustments

TOTAL EQUITY


TOTAL LIABILITIES + EQUITY
```

---

# 41. Balance Sheet Integrity

Hard business rule:

```text
Assets = Liabilities + Equity
```

System harus melakukan validation.

Jika tidak balance:

```text
⚠️ Financial Integrity Warning

Assets:
Rp50.000.000

Liabilities + Equity:
Rp48.000.000

Difference:
Rp2.000.000
```

System tidak boleh silently ignore discrepancy.

---

# 42. Net Worth

Formula:

```text
Net Worth = Total Assets - Total Liabilities
```

Example:

```text
Assets       Rp100M
Liabilities  Rp20M

Net Worth    Rp80M
```

---

# 43. Monthly Summary

`/summary`

Example response:

```text
📊 August 2026

Income
Rp10.000.000

Expense
Rp6.250.000

Net Income
Rp3.750.000

Assets
RpXX.XXX.XXX

Liabilities
RpXX.XXX.XXX

Net Worth
RpXX.XXX.XXX
```

---

# 44. Expense Report

`/expense`

System menampilkan:

```text
August 2026

Food & Beverage       Rp1.250.000
Housing               Rp1.850.000
Transportation          Rp650.000
Shopping                Rp400.000
Entertainment           Rp300.000

Total                  Rp4.450.000
```

---

# 45. Account Report

`/accounts`

Example:

```text
💳 Account Balances

BRI             Rp8.500.000
BCA             Rp4.200.000
GoPay             Rp280.000
OVO               Rp150.000
Cash              Rp500.000
BRIZZI            Rp75.000
```

---

# 46. Liability Report

`/debt`

Example:

```text
💳 Liabilities

BRI Credit Card       Rp2.300.000
Laptop Installment    Rp8.750.000

Total Liability       Rp11.050.000
```

---

# 47. PDF Report

PDF adalah primary downloadable financial report.

User:

```text
/report
```

Bot menghasilkan PDF.

Minimal PDF berisi:

1. Reporting period
2. Executive summary
3. Income
4. Expenses
5. Expense by category
6. Net income
7. Assets
8. Liabilities
9. Equity
10. Net worth
11. Account balances
12. Major asset information
13. Depreciation
14. Financial integrity status

---

# 48. Reporting Period

Report dapat dibuat berdasarkan:

- current month
- previous month
- year-to-date
- custom date range

MVP minimum:

- monthly
- custom range

---

# 49. Google Sheets Data Architecture

Google Spreadsheet minimal memiliki sheets:

```text
Transactions
Accounts
Categories
Category_Aliases
Assets
Liabilities
Installments
Investments
Recurring
Audit_Log
Settings
Monthly_Summary
Income_Statement
Balance_Sheet
```

`Recurring` dapat disiapkan sebagai schema namun functionality dapat masuk Phase 2.

---

# 50. Transactions Sheet

Contoh:

| transaction_id | date | type | description | amount | account | category | status |
|---|---|---|---|---:|---|---|---|
| TX001 | 2026-08-16 | Expense | Lunch | 35000 | GoPay | Food & Beverage | Posted |
| TX002 | 2026-08-16 | Transfer | Top Up GoPay | 500000 | BRI | Transfer | Posted |

Untuk transfer, source dan destination account harus dapat direpresentasikan.

---

# 51. Accounts Sheet

Field:

```text
account_id
account_name
account_type
currency
opening_balance
current_balance
status
created_at
updated_at
```

---

# 52. Categories Sheet

Field:

```text
category_id
category_name
category_type
parent_category
description
created_by
created_at
status
```

Category type dapat berupa:

- Income
- Expense
- Asset
- Liability
- Transfer
- Investment

---

# 53. Category Alias Sheet

Field:

```text
alias_id
alias
category_id
created_by
created_at
```

Example:

```text
kopi     → Food & Beverage
coffee   → Food & Beverage
ngopi    → Food & Beverage
cafe     → Food & Beverage
```

---

# 54. Assets Sheet

Field:

```text
asset_id
asset_name
asset_category
acquisition_date
acquisition_cost
useful_life_years
depreciation_method
accumulated_depreciation
net_book_value
status
```

---

# 55. Liabilities Sheet

Field:

```text
liability_id
liability_name
liability_type
principal_amount
outstanding_balance
interest_rate
start_date
due_date
status
```

---

# 56. Audit Log

Semua perubahan penting harus dicatat.

Field:

```text
audit_id
timestamp
entity_type
entity_id
action
old_value
new_value
actor
reason
```

Actions:

```text
CREATE
UPDATE
DELETE
VOID
REVERSE
SYSTEM_ADJUSTMENT
```

---

# 57. Historical Integrity

User dapat mengubah transaksi lama.

Contoh:

Original:

```text
Food
Rp50.000
```

User mengatakan:

> "Transaksi kemarin ternyata 75 ribu."

System tidak hanya overwrite tanpa history.

Audit:

```text
UPDATE

Old:
Rp50.000

New:
Rp75.000
```

Financial statements direcalculate.

---

# 58. Delete Policy

Transaction tidak boleh hilang secara irreversible dari audit history.

Delete operation harus menggunakan:

- VOID
- REVERSE
- soft delete

Original record tetap dapat ditelusuri.

---

# 59. Accounting Engine

Accounting engine bertanggung jawab terhadap:

- debit/credit logical mapping
- balance calculation
- account balance
- income/expense classification
- asset recognition
- liability recognition
- depreciation
- net worth
- financial statement generation
- integrity check

---

# 60. Accounting Examples

## Example A — Expense

Input:

> "Makan 50 ribu pakai GoPay."

Result:

```text
GoPay              -50K
Food Expense       +50K
```

---

## Example B — Income

Input:

> "Gaji 10 juta masuk BRI."

Result:

```text
BRI                 +10M
Salary Income       +10M
```

---

## Example C — Transfer

Input:

> "Top up GoPay 500 ribu dari BRI."

Result:

```text
BRI                 -500K
GoPay               +500K
```

No expense.

---

## Example D — Expense after top-up

Input:

> "Beli makan 22 ribu pakai GoPay."

Result:

```text
GoPay               -22K
Food Expense        +22K
```

GoPay remaining balance:

```text
500K - 22K = 478K
```

---

## Example E — Asset

Input:

> "Beli laptop 15 juta dari BRI."

Result:

```text
Laptop Asset        +15M
BRI                 -15M
```

---

## Example F — Credit Card Purchase

Input:

> "Beli sepatu 500 ribu pakai CC."

Result:

```text
Shopping Expense       +500K
Credit Card Liability  +500K
```

---

## Example G — Credit Card Payment

Input:

> "Bayar kartu kredit 2 juta dari BRI."

Result:

```text
BRI                    -2M
Credit Card Liability -2M
```

No additional expense.

---

# 61. AI Classification Framework

AI harus melakukan classification terhadap:

```text
Intent
Transaction Type
Amount
Date
Account
Destination Account
Category
Asset/Expense
Liability
Investment
Description
```

AI output harus berupa structured data yang dapat divalidasi backend.

---

# 62. AI Provider Abstraction

System tidak boleh tightly coupled dengan satu AI vendor.

Concept:

```text
AI Provider Interface
       │
       ├── Provider A
       ├── Provider B
       └── Provider C
```

Provider dipilih berdasarkan:

- free API availability
- quota
- model capability
- reliability
- latency
- structured output support

Tidak ada requirement untuk menggunakan paid API pada MVP.

---

# 63. AI Safety Rules

AI tidak boleh:

1. Mengubah financial record tanpa validation.
2. Mengubah balance sheet secara langsung.
3. Menghapus historical record secara permanen.
4. Mengarang transaction amount.
5. Mengarang account.
6. Menganggap transfer sebagai expense.
7. Menganggap asset sebagai expense tanpa classification.
8. Menggunakan `Other` tanpa proses classification terlebih dahulu.

---

# 64. Error Handling

Jika AI tidak memahami:

> "tadi keluar 50 ribu"

Bot tidak boleh menebak account/category secara sembarangan.

Bot:

> "Saya bisa mencatat Rp50.000 sebagai transaksi pengeluaran, tetapi belum tahu digunakan untuk apa. Bisa jelaskan pengeluarannya?"

---

# 65. Duplicate Transaction Detection

System sebaiknya mendeteksi kemungkinan duplicate.

Example:

User memasukkan:

> "Makan 50 ribu pakai BRI."

Kemudian beberapa menit kemudian:

> "Tadi makan 50 ribu."

System dapat memberi warning:

> "Transaksi serupa Rp50.000 pada hari ini sudah tercatat. Apakah ini transaksi baru?"

MVP dapat menggunakan:

- amount
- date
- account
- category
- description similarity

---

# 66. Adjustment

System harus menyediakan mechanism untuk initial adjustment atau correction.

Adjustment harus:

- memiliki reason
- memiliki timestamp
- masuk audit log
- tidak menghilangkan historical record

---

# 67. Security Requirements

Karena financial data bersifat sensitif:

### Mandatory

- Telegram User ID whitelist
- Google Sheets private
- API credentials disimpan sebagai secret
- AI API key tidak berada di spreadsheet
- backend authentication
- least privilege access
- audit logging
- no public access to financial data
- no unrestricted spreadsheet editing

---

# 68. Data Backup

Google Sheets merupakan source of truth, tetapi backup tetap diperlukan.

MVP minimum:

- Google Sheets version history
- periodic export/backup mechanism

Future:

- automated backup
- separate storage

---

# 69. Privacy

Financial data tidak boleh digunakan untuk tujuan selain menjalankan system.

AI request harus mengirim hanya informasi yang diperlukan untuk classification.

Sensitive unnecessary information harus diminimalkan.

---

# 70. Performance Requirements

Untuk transaksi normal:

Target response:

```text
User Input
    ↓
AI Processing
    ↓
Validation
    ↓
Response
```

Target UX:

**<10 seconds** untuk transaksi normal.

Jika provider AI lambat atau unavailable:

Bot harus memberikan error yang jelas dan tidak melakukan partial transaction posting.

---

# 71. Reliability

Financial transaction harus memiliki atomic behavior.

Tidak boleh terjadi:

```text
BRI -500K
GoPay update gagal
```

tanpa system mengetahui transaction tersebut incomplete.

Idealnya:

```text
Validate
→ Post
→ Verify
→ Commit
```

atau transaction ditandai sebagai failed/pending.

---

# 72. Financial Integrity

Setiap posting harus menjaga:

```text
Account Balance
+
Income Statement
+
Balance Sheet
+
Net Worth
```

tetap konsisten.

---

# 73. User Experience Principles

1. Natural language first.
2. Minimal interaction.
3. Jangan bertanya jika informasi sudah jelas.
4. Jangan menebak informasi kritikal.
5. Jangan menggunakan accounting jargon berlebihan kepada user.
6. User-facing language menggunakan Bahasa Indonesia yang sederhana.
7. Sistem boleh menggunakan accounting logic kompleks di backend.

---

# 74. Example User Journey

## Scenario

User:

> "Top up GoPay 500 ribu dari BRI."

Bot:

> ✅ Transfer berhasil dicatat.
>
> BRI → GoPay  
> Rp500.000

Kemudian:

> "Tadi makan 22 ribu pakai GoPay."

Bot:

> ✅ Pengeluaran tercatat.
>
> Food & Beverage  
> Rp22.000  
> GoPay

Kemudian:

> `/summary`

Bot:

```text
📊 August 2026

Income
Rp10.000.000

Expense
Rp22.000

Net Income
Rp9.978.000

GoPay
Rp478.000
```

---

# 75. Example Asset Journey

User:

> "Beli laptop 15 juta dari BRI."

AI mendeteksi:

```text
Asset acquisition
```

Bot:

> Saya mendeteksi pembelian aset:
>
> Laptop  
> Rp15.000.000  
> Dibayar dari BRI
>
> Useful life belum ditentukan.
> Berapa tahun masa depresiasinya?

User:

> "5 tahun."

System:

```text
Asset = 15M
Useful Life = 5 years
Annual Depreciation = 3M
Monthly Depreciation = 250K
```

---

# 76. Example Ambiguous Transaction

User:

> "Beli HP 8 juta."

System:

> Saya menemukan pembelian HP sebesar Rp8.000.000.
>
> Pembayaran menggunakan account apa?

User:

> "BCA."

Jika configuration menunjukkan HP sebagai asset:

> Saya akan mencatat HP sebagai aset dengan nilai Rp8.000.000. Masa depresiasi belum ditentukan. Berapa tahun?

---

# 77. Example Historical Correction

User:

> "Transaksi makan kemarin sebenarnya 75 ribu, bukan 50 ribu."

System:

```text
Transaction found:
TX-20260815-001

Old amount: Rp50.000
New amount: Rp75.000
Difference: +Rp25.000
```

Bot:

> ✅ Transaksi diperbarui.
>
> Audit history tetap disimpan.

---

# 78. Initial Category Framework

Initial category dapat berupa:

### Income
- Salary
- Bonus
- Interest Income
- Other Income

### Expense
- Food & Beverage
- Housing
- Utilities
- Transportation
- Shopping
- Entertainment
- Health
- Education
- Personal Care
- Subscription
- Financial Cost
- Tax
- Other Income/Expense only where appropriate

### Asset
- Cash
- Bank
- E-Wallet
- Investment
- Gold
- Vehicle
- Electronics
- Equipment
- Other Asset

### Liability
- Credit Card
- Installment
- Loan
- PayLater
- Other Liability

Category master dapat berkembang melalui AI.

---

# 79. MVP Acceptance Criteria

MVP dianggap berhasil apabila:

### Transaction

- [ ] User dapat mencatat income.
- [ ] User dapat mencatat expense.
- [ ] User dapat melakukan transfer.
- [ ] User dapat mencatat asset.
- [ ] User dapat mencatat liability.
- [ ] User dapat mencatat credit card transaction.
- [ ] User dapat mencatat historical transaction.
- [ ] User dapat melakukan correction.
- [ ] User dapat melakukan void/reversal.

### AI

- [ ] AI memahami natural language.
- [ ] AI dapat menentukan transaction type.
- [ ] AI dapat menentukan amount.
- [ ] AI dapat menentukan transaction date.
- [ ] AI dapat menentukan account.
- [ ] AI dapat menentukan category.
- [ ] AI dapat membedakan transfer vs expense.
- [ ] AI dapat membedakan asset vs expense.
- [ ] AI dapat menggunakan aliases.
- [ ] AI dapat membuat category baru.
- [ ] AI meminta clarification jika informasi kritikal kurang.

### Accounting

- [ ] Account balance akurat.
- [ ] Income Statement tersedia.
- [ ] Balance Sheet tersedia.
- [ ] Net Worth tersedia.
- [ ] Depreciation berjalan.
- [ ] Liability balance berjalan.
- [ ] Balance Sheet integrity check berjalan.

### Telegram

- [ ] `/start`
- [ ] `/setup`
- [ ] `/catat`
- [ ] `/summary`
- [ ] `/balance`
- [ ] `/expense`
- [ ] `/income`
- [ ] `/accounts`
- [ ] `/debt`
- [ ] `/report`
- [ ] `/help`

### Reporting

- [ ] Monthly summary tersedia.
- [ ] Custom period report tersedia.
- [ ] PDF dapat dihasilkan.
- [ ] PDF mencerminkan data terbaru.

### Audit

- [ ] CREATE tercatat.
- [ ] UPDATE tercatat.
- [ ] VOID/DELETE tercatat.
- [ ] REVERSE tercatat.
- [ ] Historical value dapat ditelusuri.

---

# 80. MVP Definition of Done

MVP dinyatakan selesai apabila user dapat menjalankan seluruh siklus:

```text
Setup Financial Position
        ↓
Create Account
        ↓
Record Transaction
        ↓
AI Classification
        ↓
Validation
        ↓
Accounting Posting
        ↓
Update Account Balance
        ↓
Update Financial Statements
        ↓
Check Balance Sheet
        ↓
Generate Report
```

Tanpa membutuhkan input manual langsung ke spreadsheet untuk transaksi normal.

---

# 81. Phase 2

Setelah MVP stabil:

### Recurring Transaction

- Salary recurring
- Rent
- Internet
- Subscription
- Installment schedule

### Budget

- Monthly budget
- Category budget
- Budget utilization
- Overspending alert

### Investment

- Investment transaction history
- Units
- Cost basis
- Current value
- Gain/loss

### Dashboard

Web-based dashboard dapat dipertimbangkan setelah accounting engine stabil.

---

# 82. Phase 3

Personal Financial Analyst.

Contoh query:

> "Pengeluaran bulan ini paling besar di mana?"

> "Apakah pengeluaran bulan ini lebih boros dari bulan lalu?"

> "Kalau aku beli laptop 15 juta bulan depan, cash flow aman tidak?"

> "Berapa rata-rata pengeluaran Food & Beverage 6 bulan terakhir?"

> "Berapa net worth-ku dibanding tiga bulan lalu?"

> "Kalau aku berhenti membeli subscription, berapa yang bisa dihemat setahun?"

System berkembang dari:

**Transaction Recorder**

menjadi:

**Personal Financial Intelligence Assistant.**

---

# 83. Future Architecture Direction

Walaupun MVP menggunakan Google Sheets, backend harus dibuat dengan abstraction sehingga database dapat diganti di masa depan.

Potential future:

```text
MVP
Google Sheets
      ↓
Future
PostgreSQL / Cloud Database
```

Telegram Bot dan Accounting Engine tidak boleh terlalu bergantung pada struktur cell Google Sheets.

---

# 84. Product Success Metrics

Karena sistem ini personal, success metric utama bukan jumlah user.

### Primary Metrics

1. Transaction recording accuracy.
2. AI categorization accuracy.
3. Financial statement integrity.
4. Successful transaction completion rate.
5. Number of transactions requiring manual correction.
6. Duplicate transaction rate.
7. AI clarification rate.
8. Report generation success rate.

Target awal:

> **Accounting correctness > AI sophistication.**

Sistem lebih baik meminta clarification daripada mencatat transaksi dengan angka yang salah.

---

# 85. Key Product Risks

## Risk 1 — AI hallucination

Mitigation:

- structured output
- validation
- confirmation
- accounting engine

## Risk 2 — Wrong classification

Mitigation:

- category master
- aliases
- confidence
- correction mechanism
- audit trail

## Risk 3 — Balance Sheet inconsistency

Mitigation:

- accounting engine
- integrity check
- atomic posting

## Risk 4 — Google Sheets limitation

Mitigation:

- backend abstraction
- controlled writes
- data validation
- future database migration path

## Risk 5 — Free AI API limitations

Mitigation:

- provider abstraction
- configurable model
- fallback provider
- lightweight prompts
- structured output

---

# 86. Recommended Technical Stack

BRD tidak mengunci implementation stack, tetapi recommended MVP:

### Interface
**Telegram Bot API**

### Backend
**Python / FastAPI** atau **Node.js / TypeScript**

### AI
Provider abstraction:

```text
AIService
 ├── OpenAIAdapter
 ├── GeminiAdapter
 └── ClaudeAdapter
```

### Data
**Google Sheets API**

### Authentication
Telegram User ID whitelist.

### Reporting
Server-side PDF generation.

### Hosting
Free/low-cost cloud runtime yang sesuai dengan quota dan workload MVP.

---

# 87. Recommended Backend Modules

```text
/app
│
├── telegram/
│   ├── handlers
│   ├── commands
│   └── conversation
│
├── ai/
│   ├── parser
│   ├── classifier
│   └── provider
│
├── accounting/
│   ├── transaction
│   ├── account
│   ├── asset
│   ├── liability
│   ├── depreciation
│   └── statements
│
├── sheets/
│   ├── transactions
│   ├── accounts
│   ├── categories
│   └── audit
│
├── reporting/
│   └── pdf
│
└── security/
```

---

# 88. Core Business Rules

| Rule | Requirement |
|---|---|
| BR-001 | Transfer antar-account bukan expense |
| BR-002 | Transfer antar-account bukan income |
| BR-003 | Expense mengurangi net income |
| BR-004 | Income meningkatkan net income |
| BR-005 | Asset acquisition masuk Balance Sheet |
| BR-006 | Asset depreciation mengurangi carrying value |
| BR-007 | Credit card purchase meningkatkan liability |
| BR-008 | Credit card payment mengurangi liability |
| BR-009 | Loan installment mengurangi outstanding liability |
| BR-010 | Opening balance bukan income |
| BR-011 | Opening balance bukan expense |
| BR-012 | Transaction date berbeda dengan recorded date |
| BR-013 | Historical changes harus diaudit |
| BR-014 | Hard delete financial transaction tidak diperbolehkan |
| BR-015 | AI tidak boleh direct-post tanpa validation |
| BR-016 | Balance Sheet harus balance |
| BR-017 | `Other` tidak boleh menjadi default classification |
| BR-018 | AI boleh membuat category baru |
| BR-019 | Category alias harus digunakan untuk normalization |
| BR-020 | Currency MVP adalah IDR |

---

# 89. Requirement Priority

## P0 — Must Have

- Telegram bot
- Telegram authentication
- `/start`
- `/setup`
- Natural language input
- `/catat`
- Income
- Expense
- Transfer
- Account balance
- Category AI
- Confirmation
- Google Sheets integration
- Accounting engine
- Balance Sheet
- Income Statement
- Net Worth
- Asset
- Liability
- Depreciation
- Audit trail
- Correction
- `/summary`
- `/balance`
- `/accounts`
- `/expense`
- `/income`
- `/debt`
- `/report`
- PDF report
- Balance integrity check

## P1 — Phase 2

- Recurring transactions
- Budget
- Investment enhancement
- Web dashboard
- Notifications

## P2 — Phase 3

- Financial analysis
- Forecasting
- Financial recommendations
- Advanced investment analysis
- Advanced financial intelligence

---

# 90. Final Product Definition

Personal Finance AI Assistant MVP adalah:

> **A private, single-user, Telegram-based personal accounting assistant that converts natural-language financial transactions into validated accounting entries, maintains accounts, assets, liabilities and financial statements through Google Sheets, and produces downloadable financial reports.**

Sistem harus memiliki tiga lapisan utama:

```text
┌─────────────────────────────────────┐
│            USER / TELEGRAM          │
│       Natural Language Interface    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│                AI                   │
│ Understand / Extract / Classify     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│          ACCOUNTING ENGINE          │
│ Validate / Post / Calculate         │
│ Asset / Liability / Depreciation    │
│ Income Statement / Balance Sheet    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│          GOOGLE SHEETS              │
│           SOURCE OF TRUTH           │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│             REPORTING               │
│ Telegram Summary + PDF Report       │
└─────────────────────────────────────┘
```

**Core product principle:**

> **AI boleh memahami dan menyarankan, tetapi hanya Accounting Engine yang boleh menentukan bagaimana transaksi memengaruhi financial position.**

Dengan prinsip tersebut, sistem tidak hanya menjadi **expense tracker**, tetapi memiliki fondasi untuk berkembang menjadi **personal financial accounting system dan financial analyst** pada Phase 2–3.