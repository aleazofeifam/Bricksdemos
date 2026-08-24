---
name: finops-owner-attribution
description: Atribuye el gasto de Databricks por owner (usuario o service principal), custom tags y billing_origin_product. Usar cuando el usuario necesite chargeback por equipo, identificar quién consume más, o implementar gobernanza de costos por owner.
---

# Atribución de Gasto por Owner

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Quién está consumiendo más?"
- "¿Cuánto gasta cada equipo/proyecto?"
- "Necesito hacer chargeback"
- "¿Qué porcentaje del gasto está atribuido?"
- "Gasto por service principal o usuario"

## Query SQL

```sql
WITH attributed AS (
  SELECT
    u.workspace_id,
    u.billing_origin_product,
    COALESCE(u.identity_metadata.run_as, 'UNATTRIBUTED') AS owner,
    COALESCE(u.custom_tags['team'], 'NO_TAG') AS team_tag,
    COALESCE(u.custom_tags['project'], 'NO_TAG') AS project_tag,
    u.usage_date,
    u.usage_quantity,
    u.usage_quantity * p.pricing.effective_list.default AS list_cost_usd
  FROM system.billing.usage AS u
  LEFT JOIN system.billing.list_prices AS p
    ON u.cloud = p.cloud
    AND u.sku_name = p.sku_name
    AND u.usage_start_time >= p.price_start_time
    AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
    AND p.currency_code = 'USD'
  WHERE u.usage_unit = 'DBU'
    AND u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT
  workspace_id,
  owner,
  team_tag,
  project_tag,
  billing_origin_product,
  SUM(usage_quantity) AS dbus,
  SUM(list_cost_usd) AS list_cost_usd,
  COUNT(DISTINCT usage_date) AS active_days
FROM attributed
GROUP BY ALL
ORDER BY list_cost_usd DESC
LIMIT 100;
```

## Query complementaria — % de gasto atribuido

```sql
SELECT
  workspace_id,
  COUNT_IF(identity_metadata.run_as IS NOT NULL) * 100.0 / COUNT(*) AS pct_attributed_by_owner,
  COUNT_IF(custom_tags['team'] IS NOT NULL) * 100.0 / COUNT(*) AS pct_attributed_by_team_tag
FROM system.billing.usage
WHERE usage_unit = 'DBU'
  AND usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY workspace_id;
```

## Notas de interpretación

- `identity_metadata.run_as` identifica el principal que ejecutó el workload.
- `custom_tags` provienen de tags en clusters, jobs y warehouses. Si están vacíos, se necesita implementar tagging obligatorio via Compute Policies o Usage Policies.
- Meta recomendada: >90% del gasto atribuido a un owner.
- Si `UNATTRIBUTED` es alto, la prioridad es implementar tags antes de optimizar.
- Los tags `team` y `project` son ejemplos — adaptar a la taxonomía del cliente.

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
