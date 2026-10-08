"""Reproducible EDA: writes charts and a short data-quality summary."""
from pathlib import Path
import duckdb
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports"


def run() -> None:
    df = pd.read_csv(ROOT / "data" / "processed" / "customer_months.csv")
    con = duckdb.connect()
    con.register("customer_months", df)
    monthly = con.execute((ROOT / "sql" / "01_monthly_kpis.sql").read_text()).df()
    cohorts = con.execute((ROOT / "sql" / "02_cohort_retention.sql").read_text()).df()
    con.close()
    OUTPUT.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(pd.to_datetime(monthly.month), monthly.closing_mrr, color="#7C3AED", linewidth=2.5)
    ax.set(title="Synthetic SaaS monthly recurring revenue", ylabel="MRR (USD)", xlabel="")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUTPUT / "mrr_trend.png", dpi=160)
    plt.close(fig)
    curve = cohorts[cohorts.cohort_age <= 12].groupby("cohort_age").apply(
        lambda g: 100 * g.retained_customers.sum() / g.cohort_size.sum(), include_groups=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(curve.index, curve.values, marker="o", color="#14B8A6", linewidth=2.5)
    ax.set(title="Weighted cohort retention (observed cohorts)", xlabel="Months since signup", ylabel="Retention (%)", ylim=(0, 105))
    fig.tight_layout()
    fig.savefig(OUTPUT / "cohort_retention.png", dpi=160)
    plt.close(fig)
    latest = monthly.iloc[-1]
    summary = f"""# Exploratory analysis snapshot\n\nAll values below describe **synthetic data** through {latest.month}.\n\n- Customers: {df.customer_id.nunique():,}\n- Customer-month records: {len(df):,}\n- Duplicate customer-month keys: {df.duplicated(['customer_id','month']).sum()}\n- Missing values: {int(df.isna().sum().sum())}\n- Latest MRR: ${latest.closing_mrr:,.2f}\n- Latest ARR run rate: ${latest.arr_run_rate:,.2f}\n- Latest NRR: {latest.nrr_pct:.2f}%\n- Latest logo churn: {latest.logo_churn_pct:.2f}%\n\nThe retention curve pools only cohorts with an observed age. Young cohorts therefore do not contribute to older ages. See README.md for metric caveats.\n"""
    (OUTPUT / "eda_summary.md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    run()
