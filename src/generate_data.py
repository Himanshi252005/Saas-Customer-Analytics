"""Create a deterministic, explicitly synthetic SaaS subscription dataset."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "synthetic_customers.csv"
MONTHS = pd.date_range("2023-01-01", "2025-12-01", freq="MS")


def generate(seed: int = 42, n: int = 1400) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    plans = rng.choice(["Starter", "Growth", "Enterprise"], n, p=[0.57, 0.33, 0.10])
    regions = rng.choice(["North America", "Europe", "APAC", "Latin America"], n, p=[0.39, 0.31, 0.21, 0.09])
    channels = rng.choice(["Organic", "Paid Search", "Partner", "Referral"], n, p=[0.37, 0.29, 0.16, 0.18])
    weights = np.linspace(1.3, 0.7, len(MONTHS))
    cohort_index = rng.choice(len(MONTHS), n, p=weights / weights.sum())
    base = {"Starter": 49, "Growth": 149, "Enterprise": 499}
    rows = []
    for i in range(n):
        plan = str(plans[i])
        start = int(cohort_index[i])
        # Higher churn in Starter and Paid Search makes segment analysis meaningful.
        monthly_churn = {"Starter": 0.042, "Growth": 0.027, "Enterprise": 0.016}[plan]
        if channels[i] == "Paid Search":
            monthly_churn += 0.011
        if regions[i] == "Latin America":
            monthly_churn += 0.006
        tenure = int(rng.geometric(monthly_churn))
        churn_index = start + tenure if start + tenure < len(MONTHS) else None
        rows.append({
            "customer_id": f"C{i + 1:05d}",
            "cohort_month": MONTHS[start].strftime("%Y-%m-%d"),
            "plan": plan,
            "region": str(regions[i]),
            "acquisition_channel": str(channels[i]),
            "base_mrr_usd": base[plan],
            "churn_month": MONTHS[churn_index].strftime("%Y-%m-%d") if churn_index is not None else "",
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df):,} synthetic customers to {OUT}")
