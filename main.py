"""CLI entry point for the Personal Expense Tracker with Data Visualization."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.analyzer import (
    analyze_categories,
    analyze_daily_spending,
    analyze_monthly_trends,
    analyze_payment_methods,
    compute_summary_kpis,
)
from src.cleaner import clean_expense_data
from src.config import CURRENCY_SYMBOL, DB_PATH, RAW_CSV_PATH, ensure_directories
from src.data_generator import generate_synthetic_expenses
from src.database import (
    check_budget_status,
    insert_single_transaction,
    load_budgets_from_db,
    load_transactions_from_db,
    upsert_transactions,
)
from src.loader import (
    append_transaction_to_csv,
    create_manual_transaction,
    load_expenses_csv,
)
from src.reporter import export_analysis_csvs, export_month_workbook, generate_text_report
from src.visualizer import generate_all_charts


def run_pipeline(csv_path: Path = RAW_CSV_PATH, regenerate: bool = False) -> None:
    """Execute the end-to-end ingestion, cleaning, SQLite storage, analysis, and reporting pipeline."""
    ensure_directories()

    if regenerate or not csv_path.exists():
        print(f"[1/6] Generating synthetic income & expense dataset at {csv_path} ...")
        generate_synthetic_expenses(output_path=csv_path)
    else:
        print(f"[1/6] Using existing transaction dataset at {csv_path}")

    print("[2/6] Loading and cleaning transactions ...")
    raw_df = load_expenses_csv(csv_path)
    cleaned_df, metrics = clean_expense_data(raw_df)

    print(
        f"      Raw rows: {metrics['initial_rows']} | "
        f"Auto-categorized: {metrics['auto_categorized_rows']} | "
        f"Dropped invalid/duplicates: {metrics['initial_rows'] - metrics['cleaned_rows']} | "
        f"Clean rows: {metrics['cleaned_rows']}"
    )

    print(f"[3/6] Persisting normalized records to SQLite ({DB_PATH}) ...")
    rows_saved = upsert_transactions(cleaned_df, db_path=DB_PATH, replace=True)
    db_df = load_transactions_from_db(db_path=DB_PATH)
    latest_month = db_df["year_month"].max()
    budgets = load_budgets_from_db(month=latest_month, db_path=DB_PATH)
    print(f"      Saved {rows_saved} transactions across {db_df['year_month'].nunique()} months.")

    print("[4/6] Running category, cashflow, payment method, and budget analyses ...")
    cat_df = analyze_categories(db_df, budgets=budgets)
    monthly_df = analyze_monthly_trends(db_df)
    pay_df = analyze_payment_methods(db_df)
    daily_df = analyze_daily_spending(db_df)
    kpis = compute_summary_kpis(db_df, budgets=budgets)
    _ = check_budget_status(latest_month, db_path=DB_PATH)

    print("[5/6] Generating visualization charts in images/ ...")
    chart_paths = generate_all_charts(cat_df, monthly_df, pay_df, daily_df)
    for path in chart_paths:
        print(f"      Saved chart: {path.name}")

    print("[6/6] Exporting CSV summaries, monthly workbook, and executive reports ...")
    csv_outputs = export_analysis_csvs(db_df, cat_df, monthly_df, pay_df)
    report_outputs = generate_text_report(kpis, metrics, cat_df, monthly_df, pay_df)
    workbook_path = export_month_workbook(db_df, cat_df, latest_month)

    print("\n" + "=" * 64)
    print("PERSONAL EXPENSE TRACKER — SUMMARY INSIGHTS")
    print("=" * 64)
    print(f"Period Covered      : {kpis['date_start']} -> {kpis['date_end']}")
    print(f"Total Income        : {CURRENCY_SYMBOL}{kpis['total_income']:,.2f}")
    print(f"Total Spending      : {CURRENCY_SYMBOL}{kpis['total_spent']:,.2f} ({kpis['expense_count']} expenses)")
    print(f"Net Savings         : {CURRENCY_SYMBOL}{kpis['net_savings']:,.2f} ({kpis['savings_rate_pct']:.1f}% rate)")
    print(f"Avg Monthly Spend   : {CURRENCY_SYMBOL}{kpis['avg_monthly_spend']:,.2f}")
    print(f"Avg Daily Spend     : {CURRENCY_SYMBOL}{kpis['avg_daily_spend']:,.2f}")
    print(f"Highest Category    : {kpis['highest_category']} ({CURRENCY_SYMBOL}{kpis['highest_category_spend']:,.2f})")
    print(f"Top Payment Method  : {kpis['top_payment_method']}")
    print(f"Latest Month ({kpis['latest_month']}): {CURRENCY_SYMBOL}{kpis['latest_month_spend']:,.2f}")

    if kpis["overspending_alerts"]:
        print(f"\nBudget Alerts ({latest_month}):")
        for alert in kpis["overspending_alerts"]:
            print(
                f"  ! {alert['category']}: {CURRENCY_SYMBOL}{alert['latest_spend']:,.2f} "
                f"/ {CURRENCY_SYMBOL}{alert['budget']:,.2f} ({alert['utilization_pct']:.1f}%)"
            )

    print("\nOutputs generated:")
    all_outputs = {**csv_outputs, **report_outputs}
    if workbook_path is not None:
        all_outputs["monthly_workbook"] = workbook_path
    for label, path in all_outputs.items():
        print(f"  - {label}: {path}")
    print("=" * 64)


def add_manual_expense_cli() -> None:
    """Interactive terminal prompt to add a manual income or expense entry and refresh outputs."""
    print("\n--- Add Manual Transaction ---")
    tx_type = input("Type (Expense / Income) [Expense]: ").strip() or "Expense"
    date_str = input("Date (YYYY-MM-DD) [today]: ").strip() or "today"
    amount_str = input("Amount: ").strip()
    note = input("Description / Merchant: ").strip()
    category = input("Category (leave blank for auto-categorize): ").strip()
    payment_method = input("Account / Payment Method (UPI / HDFC Bank / Debit Card / Credit Card / Cash) [UPI]: ").strip() or "UPI"

    tx = create_manual_transaction(
        date_str=date_str,
        amount=float(amount_str),
        payment_method=payment_method,
        note=note,
        category=category,
        tx_type=tx_type,
    )
    append_transaction_to_csv(tx, RAW_CSV_PATH)
    insert_single_transaction(tx, DB_PATH)
    print(f"Added transaction: {tx}")
    run_pipeline(csv_path=RAW_CSV_PATH, regenerate=False)


def main() -> None:
    """Parse CLI arguments and dispatch either manual entry or full pipeline."""
    parser = argparse.ArgumentParser(description="Personal Expense Tracker with Data Visualization")
    parser.add_argument("--csv", type=Path, default=RAW_CSV_PATH, help="Path to input CSV file")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate synthetic dataset before running")
    parser.add_argument("--add", action="store_true", help="Interactively add a manual transaction")
    args = parser.parse_args()

    if args.add:
        add_manual_expense_cli()
    else:
        run_pipeline(csv_path=args.csv, regenerate=args.regenerate)


if __name__ == "__main__":
    main()
