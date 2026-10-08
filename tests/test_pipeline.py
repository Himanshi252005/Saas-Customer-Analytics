from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import pytest
from src.generate_data import generate
from src.etl import transform

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ledger():
    return transform(generate(n=180))


def test_reproducible_and_unique(ledger):
    pd.testing.assert_frame_equal(ledger, transform(generate(n=180)))
    assert not ledger.duplicated(["customer_id", "month"]).any()
    assert set(ledger.is_active.unique()) <= {0, 1}


def test_mrr_movement_identity(ledger):
    expected = ledger.previous_mrr + ledger.new_mrr + ledger.expansion_mrr - ledger.contraction_mrr - ledger.churned_mrr
    assert np.allclose(ledger.mrr, expected, atol=.011)
    churn_rows = ledger[ledger.is_churned == 1]
    assert (churn_rows.mrr == 0).all()
    assert np.allclose(churn_rows.churned_mrr, churn_rows.previous_mrr)


def test_sql_reconciliation_and_retention(ledger):
    con = duckdb.connect()
    con.register("customer_months", ledger)
    monthly = con.execute((ROOT / "sql" / "01_monthly_kpis.sql").read_text()).df()
    cohorts = con.execute((ROOT / "sql" / "02_cohort_retention.sql").read_text()).df()
    lifetime = con.execute((ROOT / "sql" / "04_customer_lifetime.sql").read_text()).df()
    con.close()
    assert np.allclose(monthly.closing_mrr, monthly.opening_mrr + monthly.new_mrr + monthly.expansion_mrr - monthly.contraction_mrr - monthly.churned_mrr)
    assert (cohorts.retention_pct.between(0, 100)).all()
    assert (cohorts[cohorts.cohort_age == 0].retention_pct == 100).all()
    assert len(lifetime) == ledger.customer_id.nunique()


def test_invalid_source_rejected():
    bad = generate(n=5)
    bad.loc[1, "customer_id"] = bad.loc[0, "customer_id"]
    with pytest.raises(ValueError, match="unique"):
        transform(bad)
