---
name: finops-allpurpose-migration
description: Identifica Jobs ejecutándose sobre clusters All-Purpose que pagan tarifa premium ($0.55/DBU) cuando podrían usar Jobs Compute ($0.15/DBU). Usar cuando el usuario pregunte por candidatos a migración de All-Purpose a Jobs, oportunidades de ahorro inmediato, o workloads pagando tarifa incorrecta.
---

# Jobs en All-Purpose — Candidatos a Migración

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Qué jobs están pagando tarifa All-Purpose?"
- "Candidatos a migración de compute"
- "¿Dónde está la oportunidad de ahorro más rápida?"
- "¿Cuánto estamos pagando de más por usar All-Purpose para jobs?"
- "Workloads en compute incorrecto"

## Query SQL

```sql
SELECT
  u.usage_metadata.job_id       AS job_id,
  u.usage_metadata.cluster_id   AS cluster_id,
  u.sku_name,
  SUM(u.usage_quantity)         AS total_dbus,
  SUM(u.usage_quantity * p.pricing.effective_list.default) AS list_cost_usd,
  SUM(u.usage_quantity * p.pricing.effective_list.default) * 0.73 AS estimated_savings_usd
FROM system.billing.usage AS u
LEFT JOIN system.billing.list_prices AS p
  ON u.cloud = p.cloud
  AND u.sku_name = p.sku_name
  AND u.usage_start_time >= p.price_start_time
  AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
  AND p.currency_code = 'USD'
WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND u.usage_metadata.job_id IS NOT NULL
  AND u.sku_name LIKE '%ALL_PURPOSE%'
GROUP BY ALL
ORDER BY list_cost_usd DESC;
```

## Contexto de precios

| Compute | Precio DBU | Ahorro vs All-Purpose |
|---------|:----------:|:---------------------:|
| All-Purpose Classic | $0.55/DBU | — (baseline) |
| Jobs Classic | $0.15/DBU | 73% en tasa DBU |
| Serverless Standard | $0.40/DBU (pero ~50% menos DBUs) | Variable |

## Notas importantes

- `estimated_savings_usd` asume migración a Jobs Classic (73% reducción en tasa DBU). Es una **estimación superior** porque:
  - No incluye el costo de VMs (que se pagan aparte en Classic)
  - No considera posible aumento de duración por startup time
  - No aplica a workloads interactivos o de corta duración (<5 min)
- **Regla**: NO migrar automáticamente. Benchmark obligatorio midiendo costo total por ejecución.
- Documentación oficial describe esta migración como "the single biggest cost optimization impact".

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
