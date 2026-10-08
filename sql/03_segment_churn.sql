-- Customer segments are fixed at acquisition; counts use at-risk customers at month start.
WITH segment_month AS (
    SELECT month, plan, acquisition_channel,
           SUM(CASE WHEN previous_mrr > 0 THEN 1 ELSE 0 END) AS opening_customers,
           SUM(is_churned) AS churned_customers,
           SUM(previous_mrr) AS opening_mrr,
           SUM(churned_mrr) AS churned_mrr
    FROM customer_months
    GROUP BY month, plan, acquisition_channel
)
SELECT *,
       ROUND(100.0 * churned_customers / NULLIF(opening_customers, 0), 2) AS logo_churn_pct,
       ROUND(100.0 * churned_mrr / NULLIF(opening_mrr, 0), 2) AS revenue_churn_pct,
       ROUND(100.0 * SUM(churned_customers) OVER
             (PARTITION BY plan, acquisition_channel ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) /
             NULLIF(SUM(opening_customers) OVER
             (PARTITION BY plan, acquisition_channel ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0), 2) AS churn_3m_pct
FROM segment_month
ORDER BY month, plan, acquisition_channel;

