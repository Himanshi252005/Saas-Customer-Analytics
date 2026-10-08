-- Logo retention: active customers at age n / original cohort size.
-- Only observed cohort ages appear; customers who churn remain in the denominator.
WITH sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_months
    WHERE cohort_age = 0
    GROUP BY cohort_month
), observed_ages AS (
    SELECT s.cohort_month, date_diff('month', CAST(s.cohort_month AS DATE), CAST(m.month AS DATE)) AS cohort_age
    FROM sizes s CROSS JOIN (SELECT DISTINCT month FROM customer_months) m
    WHERE CAST(m.month AS DATE) >= CAST(s.cohort_month AS DATE)
), active AS (
    SELECT cohort_month, cohort_age, SUM(is_active) AS retained_customers
    FROM customer_months
    GROUP BY cohort_month, cohort_age
)
SELECT a.cohort_month, a.cohort_age, s.cohort_size,
       COALESCE(x.retained_customers, 0) AS retained_customers,
       ROUND(100.0 * COALESCE(x.retained_customers, 0) / s.cohort_size, 2) AS retention_pct
FROM observed_ages a
JOIN sizes s USING (cohort_month)
LEFT JOIN active x USING (cohort_month, cohort_age)
ORDER BY a.cohort_month, a.cohort_age;

