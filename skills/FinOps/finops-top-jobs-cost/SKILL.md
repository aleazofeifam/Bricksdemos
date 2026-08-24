---
name: finops-top-jobs-cost
description: Identifica los Jobs con mayor costo de lista por ejecución, atribuyendo DBUs y costo a cada job_id y run_id. Usar cuando el usuario pregunte cuáles jobs son los más caros, cuánto cuesta cada ejecución, o necesite priorizar workloads para optimización.
---

# Top Jobs por Costo de Lista

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Cuáles son los jobs más caros?"
- "¿Cuánto cuesta cada ejecución de un job?"
- "Necesito priorizar qué workloads optimizar"
- "¿Quién ejecuta los jobs más costosos?"
- "Top 10 jobs por gasto"

## Query SQL

```sql
WITH usage_with_cost AS (
  SELECT
    u.workspace_id,
    u.usage_metadata.job_id AS job_id,
    u.usage_metadata.job_run_id AS run_id,
    u.identity_metadata.run_as AS run_as,
    u.usage_quantity,
    u.usage_quantity * p.pricing.effective_list.default AS list_cost_usd
  FROM system.billing.usage AS u
  INNER JOIN system.billing.list_prices AS p
    ON u.cloud = p.cloud
   AND u.sku_name = p.sku_name
   AND u.usage_start_time >= p.price_start_time
   AND (p.price_end_time IS NULL OR u.usage_end_time <= p.price_end_time)
   AND p.currency_code = 'USD'
  WHERE u.billing_origin_product = 'JOBS'
    AND u.usage_unit = 'DBU'
    AND u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
), latest_jobs AS (
  SELECT workspace_id, job_id, name
  FROM (
    SELECT
      workspace_id,
      job_id,
      name,
      ROW_NUMBER() OVER (
        PARTITION BY workspace_id, job_id ORDER BY change_time DESC
      ) AS rn
    FROM system.lakeflow.jobs
  )
  WHERE rn = 1
)
SELECT
  u.workspace_id,
  j.name AS job_name,
  u.job_id,
  COUNT(DISTINCT u.run_id) AS runs,
  FIRST(u.run_as, TRUE) AS run_as,
  SUM(u.usage_quantity) AS dbus,
  SUM(u.list_cost_usd) AS list_cost_usd,
  TRY_DIVIDE(SUM(u.list_cost_usd), COUNT(DISTINCT u.run_id)) AS list_cost_per_run
FROM usage_with_cost AS u
LEFT JOIN latest_jobs AS j
  USING (workspace_id, job_id)
WHERE u.job_id IS NOT NULL
GROUP BY ALL
ORDER BY list_cost_usd DESC
LIMIT 100;
```

## Notas de interpretación

- Solo atribuye Jobs con `billing_origin_product = 'JOBS'`. Jobs sobre All-Purpose o SQL warehouses NO aparecen aquí (usar skill `finops-allpurpose-migration` para esos).
- `list_cost_per_run` es el indicador clave para comparar antes/después de una optimización.
- El nombre del job proviene de `system.lakeflow.jobs` (última versión por `change_time`).
- `run_as` identifica el service principal o usuario que ejecuta el job.

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
- `system.lakeflow.jobs` (SELECT)
