---
name: cost-attribution-chargeback
description: Atribuye costos de Databricks a equipos/proyectos/BUs usando system.billing + tags + usage logs. Genera reportes de chargeback con breakdown por workload type, cluster, y usuario. Úsala cuando necesites responder quién gasta cuánto y en qué, o implementar FinOps.
---

# Cost Attribution & Chargeback

Atribuir costos de Databricks a equipos, proyectos o business units.

## Query base: costo por equipo

```sql
SELECT
  COALESCE(usage_metadata.cluster_id, 'serverless') AS compute_id,
  custom_tags['team'] AS team,
  custom_tags['project'] AS project,
  sku_name,
  billing_origin_product,
  SUM(usage_quantity) AS total_dbus,
  -- Multiplicar por precio contractual (varía por cliente)
  SUM(usage_quantity) * 0.40 AS estimated_cost_usd  -- Placeholder: ajustar precio real
FROM system.billing.usage
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
GROUP BY ALL
ORDER BY total_dbus DESC
```

## Dashboard de chargeback mensual

```sql
-- Top consumers por BU
SELECT
  COALESCE(custom_tags['cost_center'], 'UNTAGGED') AS cost_center,
  billing_origin_product AS workload_type,
  SUM(usage_quantity) AS monthly_dbus,
  ROUND(SUM(usage_quantity) * 0.40, 2) AS monthly_cost_usd
FROM system.billing.usage
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
GROUP BY cost_center, workload_type
ORDER BY monthly_cost_usd DESC
```

## Alert: equipo excede budget

```sql
-- Alerta si un equipo supera su budget mensual
SELECT team, monthly_cost, budget,
  ROUND((monthly_cost - budget) / budget * 100, 1) AS overrun_pct
FROM (
  SELECT custom_tags['team'] AS team,
    SUM(usage_quantity * 0.40) AS monthly_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
  GROUP BY team
) costs
JOIN team_budgets b ON costs.team = b.team_name
WHERE monthly_cost > budget
```

## Gotchas

* `system.billing.usage` NO tiene precio en dólares — solo DBUs/unidades. Necesitas tabla de precios del contrato.
* Tags de cluster solo aparecen si el cluster los tenía AL MOMENTO del uso. Retroactivo NO funciona.
* Usage sin tags se atribuye a "UNTAGGED". Goal: <5% del consumo sin tag.
* Serverless usage tiene `serverless_compute_id` (no cluster_id). Para warehouses: key es `warehouse_id`.
* Los precios varían por SKU (ALL_PURPOSE vs JOBS vs SQL vs MODEL_SERVING). No usar un precio flat.
* Para accuracy: cruzar billing con `system.compute.clusters` para enricher con nombre/owner del cluster.
* Following workspace policies: usar tag `RemoveAfter` en recursos y `cost_center` para attribution.
