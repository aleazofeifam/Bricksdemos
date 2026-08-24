---
name: finops-autotermination-audit
description: Identifica clusters All-Purpose con auto-termination insuficiente (>60 min o deshabilitada) que podrían estar generando costos idle. Usar cuando el usuario pregunte sobre clusters que no se apagan, políticas de auto-termination, o capacidad ociosa en All-Purpose.
---

# Clusters con Auto-Termination Insuficiente

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Hay clusters que no se apagan?"
- "¿Cuáles clusters tienen auto-termination muy alta?"
- "Auditar políticas de terminación"
- "¿Cuánta capacidad ociosa tenemos en All-Purpose?"
- "Clusters con configuración de auto-stop inadecuada"

## Query SQL — Clusters con alto gasto y patrones de inactividad

```sql
WITH cluster_daily AS (
  SELECT
    u.workspace_id,
    u.usage_metadata.cluster_id AS cluster_id,
    u.usage_date,
    SUM(u.usage_quantity) AS dbus,
    SUM(u.usage_quantity * p.pricing.effective_list.default) AS list_cost_usd,
    MIN(u.usage_start_time) AS first_usage,
    MAX(u.usage_end_time) AS last_usage,
    TIMESTAMPDIFF(HOUR, MIN(u.usage_start_time), MAX(u.usage_end_time)) AS hours_span
  FROM system.billing.usage AS u
  LEFT JOIN system.billing.list_prices AS p
    ON u.cloud = p.cloud
    AND u.sku_name = p.sku_name
    AND u.usage_start_time >= p.price_start_time
    AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
    AND p.currency_code = 'USD'
  WHERE u.sku_name LIKE '%ALL_PURPOSE%'
    AND u.usage_unit = 'DBU'
    AND u.usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
  GROUP BY ALL
)
SELECT
  workspace_id,
  cluster_id,
  COUNT(DISTINCT usage_date) AS active_days,
  SUM(dbus) AS total_dbus,
  SUM(list_cost_usd) AS total_cost_usd,
  AVG(hours_span) AS avg_hours_active_per_day,
  SUM(list_cost_usd) / NULLIF(SUM(dbus), 0) AS effective_rate,
  CASE
    WHEN AVG(hours_span) > 16 THEN 'LIKELY_ALWAYS_ON'
    WHEN AVG(hours_span) > 8 THEN 'LONG_SESSIONS'
    ELSE 'NORMAL'
  END AS usage_pattern
FROM cluster_daily
GROUP BY ALL
HAVING SUM(list_cost_usd) > 50  -- ignorar clusters triviales
ORDER BY total_cost_usd DESC;
```

## Interpretación

| Patrón | Significado | Acción |
|--------|-------------|--------|
| LIKELY_ALWAYS_ON | Cluster activo >16h/día promedio | Verificar auto-termination; si es intencional, evaluar Jobs/Serverless |
| LONG_SESSIONS | Activo 8-16h/día | Revisar si las sesiones son continuas o con gaps idle |
| NORMAL | <8h/día | Probablemente bien configurado |

## Mejores prácticas de auto-termination

- **Desarrollo**: 10-20 minutos
- **Producción interactiva**: 30-60 minutos
- **Nunca**: >120 minutos sin justificación documentada
- Implementar via **Compute Policies** para enforcement:

```json
{
  "autotermination_minutes": {
    "type": "range",
    "maxValue": 60,
    "defaultValue": 20
  }
}
```

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
