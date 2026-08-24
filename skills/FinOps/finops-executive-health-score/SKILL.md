---
name: finops-executive-health-score
description: Genera un resumen ejecutivo FinOps con indicadores clave de salud de costos — tasa diaria, gasto atribuido, warehouses idle, jobs fallidos, anomalías. Usar cuando el usuario necesite un overview rápido del estado de costos, un reporte para management, o un diagnóstico general de la postura FinOps.
---

# Resumen Ejecutivo FinOps (Health Score)

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Cómo está nuestra salud de costos?"
- "Dame un resumen ejecutivo de FinOps"
- "Overview general de gasto y eficiencia"
- "Reporte para management sobre costos Databricks"
- "¿Estamos bien o hay problemas de costos?"

## Query SQL — Dashboard de indicadores

```sql
WITH daily_spend AS (
  SELECT
    u.usage_date,
    SUM(u.usage_quantity * p.pricing.effective_list.default) AS daily_cost_usd
  FROM system.billing.usage AS u
  LEFT JOIN system.billing.list_prices AS p
    ON u.cloud = p.cloud
    AND u.sku_name = p.sku_name
    AND u.usage_start_time >= p.price_start_time
    AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
    AND p.currency_code = 'USD'
  WHERE u.usage_unit = 'DBU'
    AND u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY u.usage_date
),
attribution AS (
  SELECT
    COUNT_IF(identity_metadata.run_as IS NOT NULL) * 100.0 / COUNT(*) AS pct_attributed
  FROM system.billing.usage
  WHERE usage_unit = 'DBU'
    AND usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
idle_warehouses AS (
  SELECT COUNT(*) AS idle_count
  FROM (
    SELECT warehouse_id, MAX(event_time) AS last_event
    FROM system.compute.warehouse_events
    WHERE event_type IN ('RUNNING', 'SCALED_UP')
    GROUP BY warehouse_id
    HAVING TIMESTAMPDIFF(MINUTE, MAX(event_time), CURRENT_TIMESTAMP()) >= 120
  )
),
failed_jobs AS (
  SELECT
    COUNT(DISTINCT run_id) AS failed_runs_30d,
    COUNT(DISTINCT job_id) AS failed_jobs_30d
  FROM system.lakeflow.job_run_timeline
  WHERE result_state = 'FAILED'
    AND period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
)
SELECT
  -- Tasa diaria
  ROUND(AVG(ds.daily_cost_usd), 2) AS avg_daily_cost_usd,
  ROUND(MAX(ds.daily_cost_usd), 2) AS max_daily_cost_usd,
  ROUND(SUM(ds.daily_cost_usd), 2) AS total_30d_cost_usd,
  
  -- Atribución
  ROUND((SELECT pct_attributed FROM attribution), 1) AS pct_spend_attributed,
  
  -- Warehouses idle
  (SELECT idle_count FROM idle_warehouses) AS warehouses_idle_now,
  
  -- Jobs fallidos
  (SELECT failed_runs_30d FROM failed_jobs) AS failed_runs_30d,
  (SELECT failed_jobs_30d FROM failed_jobs) AS unique_failed_jobs_30d,
  
  -- Health indicators
  CASE
    WHEN (SELECT pct_attributed FROM attribution) < 50 THEN '🟡 LOW_ATTRIBUTION'
    WHEN (SELECT idle_count FROM idle_warehouses) > 3 THEN '🟡 IDLE_COMPUTE'
    WHEN (SELECT failed_runs_30d FROM failed_jobs) > 100 THEN '🟡 HIGH_FAILURES'
    WHEN MAX(ds.daily_cost_usd) > AVG(ds.daily_cost_usd) * 2 THEN '🟡 COST_SPIKES'
    ELSE '🟢 HEALTHY'
  END AS health_status
FROM daily_spend ds;
```

## Indicadores y semaforización

| Indicador | 🟢 Saludable | 🟡 Atención | 🔴 Crítico |
|-----------|-----------|-----------|----------|
| % gasto atribuido | >90% | 50-90% | <50% |
| Warehouses idle (>2h) | 0 | 1-3 | >3 |
| Failed runs / mes | <20 | 20-100 | >100 |
| Spike máx / promedio | <1.5x | 1.5-2x | >2x |
| Tasa diaria vs mes anterior | ±10% | 10-20% | >20% |

## Notas importantes

- Este skill combina señales de múltiples dominios. Para drill-down en cualquier indicador, usar el skill específico.
- El `health_status` es heurístico y prioriza el primer problema encontrado. En realidad pueden coexistir múltiples issues.
- Ideal para una revisión FinOps semanal o mensual.
- Los umbrales deben ajustarse al baseline real del cliente después del primer mes.

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
- `system.compute.warehouse_events` (SELECT)
- `system.lakeflow.job_run_timeline` (SELECT)
