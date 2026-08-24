---
name: finops-cost-daily-product
description: Calcula el costo diario y mensual por producto Databricks usando System Tables. Usar cuando el usuario pregunte cuánto se gasta por producto, cuál es la tasa diaria, o necesite establecer un baseline de consumo.
---

# Costo Diario y Mensual por Producto

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Cuánto estamos gastando por producto?"
- "¿Cuál es nuestra tasa diaria?"
- "¿Cómo se distribuye el gasto entre SQL, Jobs, All-Purpose?"
- "Necesito un baseline de consumo"
- "¿Cuál es el costo por día activo de cada SKU?"

## Query SQL

```sql
WITH usage_cost AS (
  SELECT
    u.workspace_id,
    u.billing_origin_product,
    u.sku_name,
    u.usage_date,
    u.usage_quantity,
    u.usage_quantity * p.pricing.effective_list.default AS list_cost_usd
  FROM system.billing.usage AS u
  LEFT JOIN system.billing.list_prices AS p
    ON u.cloud = p.cloud
    AND u.sku_name = p.sku_name
    AND u.usage_end_time >= p.price_start_time
    AND (p.price_end_time IS NULL OR u.usage_end_time < p.price_end_time)
    AND p.currency_code = 'USD'
  WHERE u.usage_unit = 'DBU'
    AND u.usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
)
SELECT
  workspace_id,
  billing_origin_product,
  sku_name,
  DATE_TRUNC('month', usage_date)        AS usage_month,
  SUM(usage_quantity)                     AS dbus,
  SUM(list_cost_usd)                     AS list_cost_usd,
  SUM(list_cost_usd) / COUNT(DISTINCT usage_date) AS cost_per_active_day
FROM usage_cost
GROUP BY ALL
ORDER BY usage_month DESC, list_cost_usd DESC;
```

## Notas de interpretación

- El costo reportado es **precio de lista** (`pricing.effective_list.default`). No incluye descuentos contractuales.
- El filtro `usage_unit = 'DBU'` excluye registros de TOKENS, STORAGE_SPACE y otros tipos no-DBU.
- `cost_per_active_day` divide el costo total entre días con actividad (no días calendario), para evitar subestimar la tasa cuando hay días sin uso.
- Para baseline comparable, usar ventanas de meses cerrados completos.
- Conciliar siempre con Azure Cost Management y precio contractual antes de comunicar ahorros.

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
