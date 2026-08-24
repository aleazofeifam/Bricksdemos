---
name: finops-failed-jobs-waste
description: Cuantifica el dinero gastado en Jobs que fallan sin producir valor. Usar cuando el usuario pregunte cuánto se desperdicia en fallas, qué jobs fallan más, o necesite priorizar la confiabilidad por impacto financiero.
---

# Dinero Quemado en Jobs Fallidos

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Cuánto gastamos en jobs que fallan?"
- "¿Cuáles jobs fallan más y cuánto cuestan?"
- "Dinero desperdiciado en fallas"
- "Priorizar confiabilidad por impacto financiero"
- "¿Cuánto ahorraríamos si estos jobs no fallaran?"

## Query SQL

```sql
SELECT
  u.usage_metadata.job_id       AS job_id,
  COUNT(DISTINCT u.usage_metadata.job_run_id) AS failed_runs,
  SUM(u.usage_quantity)         AS wasted_dbus,
  SUM(u.usage_quantity * p.pricing.effective_list.default) AS wasted_usd
FROM system.billing.usage AS u
LEFT JOIN system.billing.list_prices AS p
  ON u.cloud = p.cloud
  AND u.sku_name = p.sku_name
  AND u.usage_start_time >= p.price_start_time
  AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
  AND p.currency_code = 'USD'
JOIN system.lakeflow.job_run_timeline r
  ON u.usage_metadata.job_run_id = r.run_id
WHERE r.result_state = 'FAILED'
  AND u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY ALL
ORDER BY wasted_usd DESC
LIMIT 20;
```

## Notas de interpretación

- `wasted_usd` es dinero gastado en ejecuciones que no producen resultado útil. Corregir estas fallas es **ahorro puro**.
- Un job que falla 50% del tiempo y cuesta $10/run está quemando ~$150/mes.
- Priorizar por `wasted_usd` descendente — el primer job de la lista tiene mayor ROI de corrección.
- Considerar:
  - ¿Es un problema de datos (upstream)? → Mejorar validación de entrada.
  - ¿Es un problema de recursos (OOM)? → Right-size o rediseñar.
  - ¿Es un problema intermitente (red, timeouts)? → Reintentos con backoff.
- El join con `job_run_timeline` solo cubre Jobs con `run_id` registrado en billing.

## Tablas requeridas

- `system.billing.usage` (SELECT)
- `system.billing.list_prices` (SELECT)
- `system.lakeflow.job_run_timeline` (SELECT)
