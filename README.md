# Personal Expense Tracker with Data Visualization

An end-to-end Python personal finance analytics project that ingests transactions (standard CSVs, arbitrary bank/UPI CSV exports, or manual entries), auto-categorizes them via regex rules and optional Naive Bayes ML, stores normalized records and monthly budgets in **SQLite**, generates **Matplotlib/Seaborn** charts, exports monthly reports (`.csv`, `.txt`, `.md`, `.xlsx`), and provides an interactive **Streamlit** dashboard.

---

## Problem Statement

Students and young professionals often track expenses across scattered UPI apps, bank exports, and cash notes without clear visibility into monthly cashflow, savings rate, or category overspending. This project turns raw, messy transaction logs into structured relational data, budget alerts, and actionable charts—completely offline.

---

## Key Features

- **Normalized 3-Table SQLite Schema:** `categories`, `transactions` (with `UNIQUE(tx_date, description, amount, account)` deduplication and `category_id` foreign key), and per-month `budgets`.
- **Flexible Ingestion:** Load synthetic/standard CSVs, map arbitrary bank CSV columns via `read_bank_csv()`, or log manual income/expenses via CLI (`python main.py --add`) or Streamlit.
- **Data Cleaning & Signed Cashflow:** Standardizes account labels, parses dates, removes zero/invalid/duplicate rows, and supports both expenses (`amount < 0`) and income (`amount > 0`).
- **Rule-Based + Optional ML Categorizer:** Uses regex rules first (`Swiggy` → `Food & Dining`, `Salary/Stipend` → `Income`) with an optional `MultinomialNB` (`scikit-learn`) classifier on labeled history.
- **Cashflow & Budget Analytics:** Computes Total Income, Total Spend, Net Savings, Savings Rate %, MoM spend changes, 7-day rolling daily average, and monthly budget variance (`over_by`).
- **Charts & Exports:** Generates 4 PNG charts in `images/`, 4 CSV tables in `outputs/`, and `.txt` / `.md` / `.xlsx` (or monthly CSV fallback) reports in `reports/`.

---

## Folder Structure

```text
Personal-Expense-Tracker-Visualization/
│
├── data/                        # Raw CSV dataset and normalized SQLite database (expenses.db)
├── notebooks/                   # Exploratory Data Analysis (EDA) script
├── src/                         # Modular Python source code
│   ├── config.py                # Paths, regex rules, and default monthly budgets
│   ├── data_generator.py        # 6-month synthetic income & expense simulator
│   ├── categorizer.py           # Regex + optional Naive Bayes auto-categorizer
│   ├── loader.py                # Standard CSV, arbitrary bank CSV, and manual entry loader
│   ├── cleaner.py               # Data cleaning, validation & feature engineering
│   ├── database.py              # Normalized SQLite schema, upserts & budget queries
│   ├── analyzer.py              # Cashflow KPIs, category/monthly/payment/daily analytics
│   ├── visualizer.py            # Matplotlib/Seaborn chart generation
│   ├── reporter.py              # CSV, TXT, Markdown, and Excel workbook exporters
│   └── dashboard.py             # Interactive Streamlit web dashboard
├── outputs/                     # Cleaned CSV & summary CSV tables
├── images/                      # Generated PNG charts
├── reports/                     # Monthly executive reports (.txt, .md, .xlsx/.csv)
├── docs/                        # Architecture & extensions roadmap
├── tests/                       # Pytest unit and integration tests
├── main.py                      # CLI pipeline runner
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration
└── .gitignore                   # Git ignore rules
```

---

## How to Run

### 1. Create a virtual environment & install dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run the full ETL, visualization, and reporting pipeline
```bash
python main.py --regenerate
```

### 3. Add a manual income or expense entry via CLI
```bash
python main.py --add
```

### 4. Launch the interactive Streamlit dashboard
```bash
streamlit run src/dashboard.py
```

### 5. Run automated tests
```bash
pytest -v
```
