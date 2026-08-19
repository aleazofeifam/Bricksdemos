---
name: finops-daily-rate-anomalies
description: Detecta anomalías en la tasa diaria de gasto por producto comparando contra el promedio móvil de 7 días. Usar cuando el usuario pregunte si hubo picos de gasto, necesite alertas tempranas de desviación, o quiera detectar anomalías antes del cierre mensual.
---

# Anomalías de Tasa Diaria (Alertas Tempranas)

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Hubo picos de gasto esta semana?"
- "¿Algún producto se disparó?"
- "Detectar anomalías de costo"
- "¿Hay algo inusual en el gasto reciente?"
- "Alertas de desviación de tasa diaria"

## Query SQL

```sql
WITH daily_cost AS (
  SELECT
    u.workspace_id,
    u.billing_origin_product,
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
  GROUP BY ALL
), with_moving_avg AS (
  SELECT
    *,
    AVG(daily_cost_usd) OVER (
      PARTITION BY workspace_id, billing_origin_product
      ORDER BY usage_date
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS avg_7d_prior,
    daily_cost_usd / NULLIF(
      AVG(daily_cost_usd) OVER (
        PARTITION BY workspace_id, billing_origin_product
        ORDER BY usage_date
        ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
      ), 0
    ) - 1 AS pct_deviation
  FROM daily_cost
)
SELECT
  workspace_id,
  billing_origin_product,
  usage_date,
  daily_cost_usd,
  avg_7d_prior,
  ROUND(pct_deviation * 100, 1) AS deviation_pct,
  CASE
    WHEN pct_deviation > 0.5 THEN 'SPIKE_HIGH'
    WHEN pct_deviation > 0.2 THEN 'ELEVATED'
    WHEN pct_deviation < -0.3 THEN 'DROP'
    ELSE 'NORMAL'
  END AS alert_level
FROM with_moving_avg
WHERE ABS(pct_deviation) > 0.2
  AND avg_7d_prior > 10  -- ignorar productos con gasto mínimo
ORDER BY usage_date DESC, ABS(pct_deviation) DESC;
```

## Niveles de alerta

| Nivel | Criterio | Acción |
|-------|----------|--------|
| SPIKE_HIGH | >50% sobre promedio 7d | Investigación inmediata: ¿nuevo workload, error, o cambio de configuración? |
| ELEVATED | >20% sobre promedio 7d | Monitorear 24-48h; si persiste, investigar |
| DROP | >30% bajo promedio 7d | Verificar si es intencional (optimización) o problemático (job roto) |

## Notas importantes

- El filtro `avg_7d_prior > 10` evita alertas en productos con gasto trivial.
- Los primeros 7 días del rango no tienen promedio móvil completo (serán NULL).
- Ideal para crear una alerta SQL programada que notifique diariamente.
- No distingue causas: un spike puede ser crecimiento legítimo o desperdicio.

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
