---
name: finops-serverless-comparison
description: Compara consumo DBU entre Serverless Standard y Performance-Optimized por producto. Usar cuando el usuario pregunte sobre eficiencia de serverless, diferencias entre modos, o necesite datos para decidir si migrar a Standard mode.
---

# Comparación Serverless Standard vs Performance-Optimized

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Cuánto consumimos en Serverless Standard vs Performance-Optimized?"
- "¿Vale la pena migrar a Standard mode?"
- "¿Cómo se comparan los modos serverless?"
- "Datos de consumo serverless por modo"
- "¿Está funcionando Standard mode para nuestros workloads?"

## Query SQL

```sql
SELECT
  workspace_id,
  product_features.performance_target AS performance_target,
  billing_origin_product,
  COUNT(DISTINCT usage_date) AS active_days,
  SUM(usage_quantity) AS total_dbus,
  SUM(usage_quantity) / COUNT(DISTINCT usage_date) AS dbus_per_day
FROM system.billing.usage
WHERE product_features.is_serverless
  AND billing_origin_product IN ('JOBS', 'DLT')
  AND usage_unit = 'DBU'
  AND usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY ALL
ORDER BY total_dbus DESC;
```

## Contexto de referencia

| Modo | Características | Referencia |
|------|----------------|------------|
| Performance-Optimized | Arranque rápido (<30s), mayor consumo DBU | Default para serverless |
| Standard | Arranque 4-6 min, ~50% menos DBUs, hasta 70% ahorro vs Perf-Optimized | GA Jun 2025 |

## Notas de interpretación

- `performance_target` será `STANDARD` o `PERFORMANCE_OPTIMIZED` (o NULL para classic).
- La comparación solo es válida entre workloads equivalentes ejecutados en ambos modos.
- **Advertencia crítica**: Standard puede ser 2.2x más caro que Classic con Spot instances. El benchmark contra la configuración actual es obligatorio antes de migrar.
- Si no aparecen registros con `STANDARD`, significa que aún no se ha habilitado para ningún workload.

## Tablas requeridas

- `system.billing.usage` (SELECT)
