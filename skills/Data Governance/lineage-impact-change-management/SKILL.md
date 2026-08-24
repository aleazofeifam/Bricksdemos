---
name: lineage-impact-change-management
description: Usa el linaje de UC para análisis de impacto antes de cambios — deprecar tabla, renombrar columna, cambiar tipo de dato. Identifica consumidores downstream y genera plan de comunicación. Úsala antes de cualquier breaking change en el catálogo.
---

# Lineage-Based Impact Analysis & Change Management

Proceso para evaluar impacto antes de hacer cambios en esquemas de producción.

## Identificar downstream consumers

```sql
-- ¿Quién consume esta tabla?
SELECT
  target_table_full_name AS consumer_table,
  target_type,
  COUNT(*) AS query_count,
  MAX(event_date) AS last_accessed
FROM system.access.table_lineage
WHERE source_table_full_name = 'production.raw.legacy_customers'
  AND event_date >= CURRENT_DATE() - 30
GROUP BY target_table_full_name, target_type
ORDER BY query_count DESC
```

## Column-level impact

```sql
-- ¿Quién usa la columna que quiero deprecar?
SELECT
  target_table_full_name,
  target_column_name,
  COUNT(*) AS usage_count
FROM system.access.column_lineage
WHERE source_table_full_name = 'production.raw.legacy_customers'
  AND source_column_name = 'old_status_code'
  AND event_date >= CURRENT_DATE() - 30
GROUP BY target_table_full_name, target_column_name
ORDER BY usage_count DESC
```

## Change Management Workflow

1. Identify: consultar lineage (queries arriba)
2. Classify: hard break (DROP COLUMN) vs soft (deprecate + alias)
3. Communicate: notificar owners de consumers con timeline (7 días mínimo)
4. Execute: hacer el cambio
5. Validate: verificar que no hay errores en downstream (24h monitoring)
6. Cleanup: remover aliases/compatibility layers después de 30 días

## Gotchas

* table_lineage solo captura queries ejecutadas en SQL warehouse o serverless. Notebooks en all-purpose pueden NO aparecer.
* El lag de lineage es ~1 día. No refleja queries de HOY.
* Materialized views aparecen como "TABLE" en lineage (no como "VIEW"). Verificar con information_schema.tables.table_type.
* Para recursividad (tabla A → vista B → dashboard C): hacer 2-3 hops manuales con queries encadenadas.
* column_lineage está en preview y puede faltar para transformaciones complejas (ej: CASE WHEN con múltiples sources).
* Si una tabla no tiene lineage entries: puede significar que nadie la usa O que se accede solo desde all-purpose clusters.
