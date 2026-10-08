-- Realized revenue is observed subscription revenue, not a prediction of future LTV.
-- Active customers are right-censored at the dataset end.
WITH lifetime AS (
    SELECT customer_id, cohort_month, plan, region, acquisition_channel,
           SUM(mrr) AS realized_revenue_usd,
           SUM(is_active) AS paid_months,
           MAX(is_churned) AS observed_churn
    FROM customer_months
    GROUP BY customer_id, cohort_month, plan, region, acquisition_channel
)
SELECT *,
       ROUND(realized_revenue_usd / NULLIF(paid_months, 0), 2) AS observed_arpa,
       CASE WHEN observed_churn = 1 THEN 'complete' ELSE 'right_censored' END AS lifetime_status,
       NTILE(4) OVER (ORDER BY realized_revenue_usd DESC) AS observed_revenue_quartile
FROM lifetime
ORDER BY realized_revenue_usd DESC;
