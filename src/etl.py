"""Build a monthly customer revenue ledger from synthetic source records."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "synthetic_customers.csv"
LEDGER = ROOT / "data" / "processed" / "customer_months.csv"
MONTHS = pd.date_range("2023-01-01", "2025-12-01", freq="MS")


def transform(customers: pd.DataFrame, seed: int = 2024) -> pd.DataFrame:
    required = {"customer_id", "cohort_month", "plan", "region", "acquisition_channel", "base_mrr_usd", "churn_month"}
    missing = required - set(customers.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if customers.customer_id.duplicated().any():
        raise ValueError("customer_id must be unique")
    rng = np.random.default_rng(seed)
    rows = []
    for c in customers.sort_values("customer_id").itertuples(index=False):
        cohort = pd.Timestamp(c.cohort_month)
        churn = pd.Timestamp(c.churn_month) if pd.notna(c.churn_month) and str(c.churn_month) else None
        if churn is not None and churn <= cohort:
            raise ValueError(f"Invalid churn date for {c.customer_id}")
        previous = 0.0
        for month in MONTHS[MONTHS >= cohort]:
            if churn is not None and month > churn:
                break
            is_churn = churn is not None and month == churn
            if is_churn:
                mrr = 0.0
            elif previous == 0:
                mrr = float(c.base_mrr_usd)
            else:
                movement = rng.random()
                if movement < 0.055:
                    mrr = round(previous * 1.20, 2)
                elif movement < 0.082:
                    mrr = round(previous * 0.85, 2)
                else:
                    mrr = previous
            delta = round(mrr - previous, 2)
            rows.append({
                "month": month.strftime("%Y-%m-%d"),
                "customer_id": c.customer_id,
                "cohort_month": cohort.strftime("%Y-%m-%d"),
                "cohort_age": (month.year - cohort.year) * 12 + month.month - cohort.month,
                "plan": c.plan,
                "region": c.region,
                "acquisition_channel": c.acquisition_channel,
                "previous_mrr": round(previous, 2),
                "mrr": round(mrr, 2),
                "new_mrr": round(mrr, 2) if previous == 0 and mrr > 0 else 0.0,
                "expansion_mrr": delta if previous > 0 and delta > 0 else 0.0,
                "contraction_mrr": -delta if mrr > 0 and delta < 0 else 0.0,
                "churned_mrr": round(previous, 2) if is_churn else 0.0,
                "is_active": int(mrr > 0),
                "is_churned": int(is_churn),
            })
            previous = mrr
    ledger = pd.DataFrame(rows)
    ledger = ledger.sort_values(["month", "customer_id"]).reset_index(drop=True)
    movement = ledger.previous_mrr + ledger.new_mrr + ledger.expansion_mrr - ledger.contraction_mrr - ledger.churned_mrr
    if not np.allclose(ledger.mrr, movement, atol=0.011):
        raise AssertionError("MRR movement does not reconcile")
    if ledger.duplicated(["month", "customer_id"]).any():
        raise AssertionError("Duplicate customer-month")
    return ledger


if __name__ == "__main__":
    if not RAW.exists():
        raise SystemExit("Run python -m src.generate_data first")
    source = pd.read_csv(RAW)
    result = transform(source)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(LEDGER, index=False, float_format="%.2f")
    print(f"Wrote {len(result):,} customer-months to {LEDGER}")
