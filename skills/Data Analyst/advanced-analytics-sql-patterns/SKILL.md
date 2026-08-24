---
name: advanced-analytics-sql-patterns
description: Patrones SQL analíticos avanzados — cohortes de retención, LTV (Lifetime Value), RFM scoring, funnel conversion, y churn prediction en SQL puro. Úsala cuando el analista necesite métricas complejas de negocio sin escribir Python.
---

# Advanced Analytics SQL Patterns

Patrones listos para copiar para análisis de negocio comunes.

## Cohort Retention Analysis

```sql
WITH first_purchase AS (
  SELECT customer_id, DATE_TRUNC('MONTH', MIN(order_date)) AS cohort_month
  FROM orders GROUP BY customer_id
),
activity AS (
  SELECT o.customer_id, f.cohort_month,
    DATEDIFF(MONTH, f.cohort_month, DATE_TRUNC('MONTH', o.order_date)) AS month_number
  FROM orders o JOIN first_purchase f ON o.customer_id = f.customer_id
)
SELECT cohort_month, month_number,
  COUNT(DISTINCT customer_id) AS active_users,
  COUNT(DISTINCT customer_id) * 100.0 /
    FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (PARTITION BY cohort_month ORDER BY month_number) AS retention_pct
FROM activity
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number
```

## RFM Scoring

```sql
WITH rfm AS (
  SELECT customer_id,
    DATEDIFF(DAY, MAX(order_date), CURRENT_DATE()) AS recency,
    COUNT(DISTINCT order_id) AS frequency,
    SUM(amount) AS monetary
  FROM orders
  WHERE order_date >= CURRENT_DATE() - INTERVAL 365 DAYS
  GROUP BY customer_id
)
SELECT *,
  NTILE(5) OVER (ORDER BY recency DESC) AS r_score,  -- Menos días = mejor
  NTILE(5) OVER (ORDER BY frequency) AS f_score,
  NTILE(5) OVER (ORDER BY monetary) AS m_score,
  CONCAT(
    NTILE(5) OVER (ORDER BY recency DESC),
    NTILE(5) OVER (ORDER BY frequency),
    NTILE(5) OVER (ORDER BY monetary)
  ) AS rfm_segment
FROM rfm
```

## Funnel Conversion

```sql
SELECT
  COUNT(DISTINCT CASE WHEN step >= 1 THEN user_id END) AS step1_visit,
  COUNT(DISTINCT CASE WHEN step >= 2 THEN user_id END) AS step2_add_cart,
  COUNT(DISTINCT CASE WHEN step >= 3 THEN user_id END) AS step3_checkout,
  COUNT(DISTINCT CASE WHEN step >= 4 THEN user_id END) AS step4_purchase,
  ROUND(step2 * 100.0 / step1, 1) AS conv_1_to_2_pct,
  ROUND(step4 * 100.0 / step1, 1) AS overall_conv_pct
FROM funnel_events
WHERE event_date >= CURRENT_DATE() - 30
```

## Gotchas

* Cohorte requiere DATE_TRUNC consistente — no mezclar WEEK y MONTH en el mismo análisis.
* RFM con NTILE puede dar buckets desiguales si hay empates. Usar PERCENT_RANK para más granularidad.
* Funnel debe ser ORDERED (step 1 antes de step 2). Sin orden temporal es vanity metric.
* Churn definition varía por negocio: ¿30 días sin actividad? ¿90 días? Definir ANTES de medir.
* LTV con ROWS BETWEEN UNBOUNDED PRECEDING es acumulativo (total lifetime), no moving average.
* Para cohortes grandes (>1M users), considerar materializar la CTE como tabla temporal para performance.
