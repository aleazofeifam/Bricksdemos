---
name: window-functions-masterclass
description: Dominio de window functions en Databricks SQL — running totals, moving averages, percentiles, ranking, gaps & islands, year-over-year comparisons. Úsala cuando el analista necesite cálculos que requieren contexto de filas vecinas o comparaciones temporales.
---

# Window Functions Masterclass

Patrones prácticos con window functions para análisis de negocio.

## Running Total

```sql
SELECT order_date, daily_revenue,
  SUM(daily_revenue) OVER (ORDER BY order_date ROWS UNBOUNDED PRECEDING) AS cumulative_revenue
FROM daily_revenue_summary
```

## Moving Average (7 días)

```sql
SELECT order_date, daily_revenue,
  AVG(daily_revenue) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d
FROM daily_revenue_summary
```

## Year-over-Year Growth

```sql
SELECT month, revenue,
  LAG(revenue, 12) OVER (ORDER BY month) AS revenue_ly,
  ROUND((revenue / LAG(revenue, 12) OVER (ORDER BY month) - 1) * 100, 1) AS yoy_growth_pct
FROM monthly_revenue
```

## Ranking con ties

```sql
SELECT product, revenue,
  RANK() OVER (ORDER BY revenue DESC) AS rank_with_gaps,
  DENSE_RANK() OVER (ORDER BY revenue DESC) AS rank_no_gaps,
  ROW_NUMBER() OVER (ORDER BY revenue DESC) AS unique_position
FROM product_sales
```

## Gaps & Islands (sesiones de usuario)

```sql
WITH flagged AS (
  SELECT *, CASE WHEN DATEDIFF(MINUTE, LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time), event_time) > 30
    THEN 1 ELSE 0 END AS new_session
  FROM events
)
SELECT user_id, event_time,
  SUM(new_session) OVER (PARTITION BY user_id ORDER BY event_time) AS session_id
FROM flagged
```

## Gotchas

* ROWS vs RANGE: ROWS cuenta filas literales. RANGE agrupa por valor. Si hay gaps de fecha, RANGE los ignora — usar date spine + LEFT JOIN.
* LAG/LEAD no tienen frame clause (solo PARTITION + ORDER BY). No se puede hacer LAG con ROWS BETWEEN.
* Window functions NO se pueden usar en WHERE. Solución: CTE o subquery.
* NTILE(N) con N > count(rows) pone 1 fila por bucket (no da error, no empty buckets).
* En Photon, windows sobre >1M filas por partición pueden spill to disk. Monitorear con EXPLAIN ANALYZE.
* DEFAULT value en LAG/LEAD: `LAG(revenue, 12, 0)` — el tercer argumento evita NULLs en los primeros 12 meses.
