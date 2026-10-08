"""Interactive portfolio dashboard for synthetic SaaS customer analytics."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed" / "customer_months.csv"
PURPLE, TEAL, CORAL = "#7C3AED", "#14B8A6", "#FB7185"

st.set_page_config(page_title="SaaS Pulse | Customer Analytics", page_icon="◈", layout="wide")
st.markdown("""<style>
 .block-container {padding-top: 1.7rem; max-width: 1450px;}
 .hero {background: linear-gradient(115deg,#21134c,#5533ac 60%,#8b5cf6); color:white;
        border-radius:22px; padding:30px 36px; margin-bottom:18px;}
 .hero h1 {color:white; font-size:2.35rem; margin:3px 0 7px;}
 .hero p {color:#e9ddff; margin:0; font-size:1.02rem;}
 .eyebrow {letter-spacing:.19em; text-transform:uppercase; font-size:.72rem; font-weight:700; color:#c8b5ff;}
 [data-testid="stMetric"] {background:#fff; border:1px solid #ebe7f7; border-radius:16px; padding:14px 18px; box-shadow:0 5px 20px #1e1b4b0b;}
 [data-testid="stMetricLabel"] {color:#625b7b;}
 [data-testid="stMetricValue"] {font-size:1.55rem; font-weight:700;}
 .note {background:#f0ebff; border-left:4px solid #7c3aed; padding:11px 15px; border-radius:9px; color:#332267;}
 </style>""", unsafe_allow_html=True)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA.exists():
        raise FileNotFoundError("Missing processed data. Run the generation and ETL commands in README.md.")
    return pd.read_csv(DATA, parse_dates=["month", "cohort_month"])


def query(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    con = duckdb.connect()
    con.register("customer_months", df)
    result = con.execute((ROOT / "sql" / filename).read_text(encoding="utf-8")).df()
    con.close()
    return result


def fig_style(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=35, b=8),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#302a4d"), legend_title_text="")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#ebe7f7", zeroline=False)
    return fig


try:
    data = load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

st.markdown('<div class="hero"><div class="eyebrow">Portfolio project · synthetic data</div>'
            '<h1>SaaS Pulse</h1><p>Customer retention, churn and recurring revenue in one decision view.</p></div>',
            unsafe_allow_html=True)

with st.sidebar:
    st.header("Explore the business")
    st.caption("Filters apply to every chart and metric.")
    plans = st.multiselect("Plan", sorted(data.plan.unique()), default=sorted(data.plan.unique()))
    regions = st.multiselect("Region", sorted(data.region.unique()), default=sorted(data.region.unique()))
    channels = st.multiselect("Acquisition channel", sorted(data.acquisition_channel.unique()), default=sorted(data.acquisition_channel.unique()))
    date_min, date_max = data.month.min().date(), data.month.max().date()
    selected_dates = st.slider("Reporting months", min_value=date_min, max_value=date_max,
                               value=(date_min, date_max), format="MMM YYYY")
    st.divider()
    st.info("All customer records are generated for this portfolio. No real customers or company results are represented.")

scope = data[data.plan.isin(plans) & data.region.isin(regions) & data.acquisition_channel.isin(channels)].copy()
if scope.empty:
    st.warning("The selected segments have no data. Select at least one value in each filter.")
    st.stop()
start, end = map(pd.Timestamp, selected_dates)
monthly = query(scope, "01_monthly_kpis.sql")
monthly["month"] = pd.to_datetime(monthly.month)
monthly = monthly[(monthly.month >= start) & (monthly.month <= end)].copy()
if monthly.empty:
    st.warning("No reporting months in this range.")
    st.stop()
latest = monthly.iloc[-1]
previous = monthly.iloc[-2] if len(monthly) > 1 else None

def delta(field, fmt="${:,.0f}"):
    return fmt.format(latest[field] - previous[field]) if previous is not None else None

cols = st.columns(5)
cols[0].metric("MRR", f"${latest.closing_mrr:,.0f}", delta("closing_mrr"))
cols[1].metric("ARR run rate", f"${latest.arr_run_rate:,.0f}")
cols[2].metric("Active customers", f"{int(latest.active_customers):,}",
               f"{int(latest.active_customers - previous.active_customers):+,}" if previous is not None else None)
cols[3].metric("Net revenue retention", f"{latest.nrr_pct:.1f}%" if pd.notna(latest.nrr_pct) else "n/a")
cols[4].metric("Logo churn", f"{latest.logo_churn_pct:.1f}%" if pd.notna(latest.logo_churn_pct) else "n/a")

overview, retention, segments, methodology = st.tabs(["Revenue overview", "Cohort retention", "Churn explorer", "Definitions & data"])
with overview:
    left, right = st.columns([1.65, 1])
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly.month, y=monthly.closing_mrr, name="Closing MRR", mode="lines+markers",
                                 line=dict(color=PURPLE, width=3), fill="tozeroy", fillcolor="rgba(124,58,237,.10)"))
        fig.update_layout(title="Recurring revenue trend", yaxis_title="USD")
        st.plotly_chart(fig_style(fig), width="stretch")
    with right:
        movements = monthly[["month", "new_mrr", "expansion_mrr", "contraction_mrr", "churned_mrr"]].melt(
            "month", var_name="Movement", value_name="USD")
        movements["USD"] *= movements.Movement.map({"new_mrr":1,"expansion_mrr":1,"contraction_mrr":-1,"churned_mrr":-1})
        movements.Movement = movements.Movement.map({"new_mrr":"New", "expansion_mrr":"Expansion", "contraction_mrr":"Contraction", "churned_mrr":"Churn"})
        fig = px.bar(movements, x="month", y="USD", color="Movement", title="MRR movements",
                     color_discrete_map={"New":PURPLE,"Expansion":TEAL,"Contraction":"#FBBF24","Churn":CORAL})
        st.plotly_chart(fig_style(fig), width="stretch")
    left, right = st.columns(2)
    with left:
        fig = px.line(monthly, x="month", y="nrr_pct", markers=True, title="Net revenue retention", labels={"nrr_pct":"NRR (%)"})
        fig.update_traces(line_color=TEAL, line_width=3)
        fig.add_hline(y=100, line_dash="dash", line_color="#9b94ac")
        st.plotly_chart(fig_style(fig, 310), width="stretch")
    with right:
        churn_plot = monthly[["month", "logo_churn_pct", "gross_revenue_churn_pct"]].rename(
            columns={"logo_churn_pct":"Logo churn", "gross_revenue_churn_pct":"Gross revenue churn"})
        fig = px.line(churn_plot, x="month", y=["Logo churn", "Gross revenue churn"], markers=True,
                      title="Customer vs revenue churn", labels={"value":"Rate (%)", "variable":"Measure"},
                      color_discrete_sequence=[CORAL, PURPLE])
        st.plotly_chart(fig_style(fig, 310), width="stretch")

with retention:
    cohorts = query(scope, "02_cohort_retention.sql")
    cohorts["cohort_month"] = pd.to_datetime(cohorts.cohort_month)
    cohorts = cohorts[(cohorts.cohort_month >= start) & (cohorts.cohort_month <= end) & (cohorts.cohort_age <= 12)]
    pivot = cohorts.pivot(index="cohort_month", columns="cohort_age", values="retention_pct")
    pivot.index = pivot.index.strftime("%b %Y")
    fig = px.imshow(pivot, color_continuous_scale=[[0,"#f5edff"],[0.5,"#ad86ee"],[1,"#432087"]],
                    zmin=0, zmax=100, aspect="auto", labels=dict(x="Months since signup",y="Signup cohort",color="Retention %"),
                    title="Customer retention by signup cohort")
    st.plotly_chart(fig_style(fig, max(450, 22 * len(pivot) + 90)), width="stretch")
    st.caption("Blank cells are not yet observed. Each row uses the original signup cohort as its denominator.")
    st.dataframe(cohorts, width="stretch", hide_index=True)

with segments:
    segment = query(scope, "03_segment_churn.sql")
    segment["month"] = pd.to_datetime(segment.month)
    segment = segment[(segment.month >= start) & (segment.month <= end)]
    rollup = segment.groupby(["plan", "acquisition_channel"], as_index=False)[["opening_customers", "churned_customers", "opening_mrr", "churned_mrr"]].sum()
    rollup["logo_churn_pct"] = 100 * rollup.churned_customers / rollup.opening_customers.replace(0, float("nan"))
    rollup["revenue_churn_pct"] = 100 * rollup.churned_mrr / rollup.opening_mrr.replace(0, float("nan"))
    left, right = st.columns([1.3, 1])
    with left:
        fig = px.bar(rollup, x="plan", y="logo_churn_pct", color="acquisition_channel", barmode="group",
                     title="Weighted logo churn by segment", labels={"logo_churn_pct":"Churn (%)"},
                     color_discrete_sequence=[PURPLE, TEAL, CORAL, "#FBBF24"])
        st.plotly_chart(fig_style(fig), width="stretch")
    with right:
        st.subheader("Segment detail")
        st.dataframe(rollup.round(2), width="stretch", hide_index=True)
    st.caption("Rates are calculated from summed churn events and summed at-risk customer-months, not averaged monthly percentages.")

with methodology:
    st.markdown("""### How to read this dashboard
**MRR** is the sum of active subscription revenue at month end. **ARR run rate** is 12 × MRR; it is not booked annual revenue.

**NRR** = (opening MRR + expansion − contraction − churned MRR) / opening MRR. New customer MRR is excluded.

**Logo churn** = customers lost this month / active customers at month start. **Gross revenue churn** = (contraction + churned MRR) / opening MRR.

**LTV proxy** in the SQL output = current ARPA / monthly logo churn. It is undefined when no customer churn occurs, assumes a stable churn rate and gross margin of 100%, and should not be treated as a forecast. Customer-level realized revenue is observed revenue only; active customers are right-censored.

The data is **fully synthetic**, generated with fixed random seeds. Plans and channels have deliberately different churn probabilities for an illustrative analysis. There are no taxes, refunds, usage fees, multi-currency conversions, or reactivations. See the README for full provenance and limitations.""")
    st.download_button("Download filtered customer-month ledger", scope.to_csv(index=False).encode(),
                       file_name="synthetic_customer_months_filtered.csv", mime="text/csv")
