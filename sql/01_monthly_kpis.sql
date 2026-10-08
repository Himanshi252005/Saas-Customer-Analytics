-- Grain: one calendar month. USD, nominal. December 2025 is the final observation.
WITH movements AS (
    SELECT month,
           SUM(previous_mrr) AS opening_mrr,
           SUM(mrr) AS closing_mrr,
           SUM(new_mrr) AS new_mrr,
           SUM(expansion_mrr) AS expansion_mrr,
           SUM(contraction_mrr) AS contraction_mrr,
           SUM(churned_mrr) AS churned_mrr,
           SUM(CASE WHEN previous_mrr > 0 THEN 1 ELSE 0 END) AS opening_customers,
           SUM(is_active) AS active_customers,
           SUM(is_churned) AS churned_customers,
           SUM(CASE WHEN new_mrr > 0 THEN 1 ELSE 0 END) AS new_customers
    FROM customer_months
    GROUP BY month
), kpis AS (
    SELECT *,
           ROUND(12 * closing_mrr, 2) AS arr_run_rate,
           ROUND(100.0 * churned_customers / NULLIF(opening_customers, 0), 2) AS logo_churn_pct,
           ROUND(100.0 * (contraction_mrr + churned_mrr) / NULLIF(opening_mrr, 0), 2) AS gross_revenue_churn_pct,
           ROUND(100.0 * (opening_mrr + expansion_mrr - contraction_mrr - churned_mrr)
                 / NULLIF(opening_mrr, 0), 2) AS nrr_pct,
           ROUND(closing_mrr / NULLIF(active_customers, 0), 2) AS arpa,
           ROUND((closing_mrr / NULLIF(active_customers, 0)) /
                 NULLIF(churned_customers * 1.0 / NULLIF(opening_customers, 0), 0), 2) AS ltv_proxy
    FROM movements
)
SELECT *,
       ROUND(100.0 * (closing_mrr - LAG(closing_mrr) OVER (ORDER BY month)) /
             NULLIF(LAG(closing_mrr) OVER (ORDER BY month), 0), 2) AS mrr_growth_pct
FROM kpis
ORDER BY month;

