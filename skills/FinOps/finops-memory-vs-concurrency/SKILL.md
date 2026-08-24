---
name: finops-memory-vs-concurrency
description: Diagnostica si los warehouses SQL tienen problemas de memoria (spill) o de concurrencia (colas). Usar cuando el usuario pregunte por qué los queries están lentos, si debe escalar el warehouse, o necesite distinguir entre presión de memoria y saturación de capacidad.
---

# Presión de Memoria vs Concurrencia

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Por qué los queries están lentos?"
- "¿Debo escalar el warehouse o optimizar SQL?"
- "¿Hay problemas de concurrencia?"
- "¿Los warehouses tienen presión de memoria?"
- "Diagnóstico de performance de warehouses"

## Query SQL

```sql
SELECT
  workspace_id,
  compute.warehouse_id                                    AS warehouse_id,
  DATE_TRUNC('hour', start_time)                         AS hour,
  COUNT(*)                                               AS queries,
  COUNT_IF(waiting_at_capacity_duration_ms > 0)          AS queued_queries,
  PERCENTILE_APPROX(waiting_at_capacity_duration_ms, 0.95) AS p95_capacity_wait_ms,
  SUM(COALESCE(spilled_local_bytes, 0)) / POW(1024, 3)  AS spilled_gib,
  PERCENTILE_APPROX(total_duration_ms, 0.95)            AS p95_total_ms
FROM system.query.history
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
  AND compute.warehouse_id IS NOT NULL
GROUP BY ALL
ORDER BY hour DESC, p95_capacity_wait_ms DESC;
```

## Matriz de diagnóstico

| Cola | Spill | Latencia | Diagnóstico | Acción |
|------|-------|----------|-------------|--------|
| Alta | Bajo | Alta | Saturación de concurrencia | Escalar clusters, aislar workloads, separar BI de ad-hoc |
| Baja | Alto | Alta | Presión de memoria | Optimizar SQL (joins, agregaciones), revisar layout de datos |
| Baja | Bajo | Alta | Consultas inherentemente pesadas | Investigar scans, compilación, diseño de la consulta |
| Alta | Alto | Alta | Problema dual | Aislar primero, luego optimizar SQL |

## Notas importantes

- **No asignar causa raíz automáticamente**. Estas son señales de priorización. Confirmar con Query Profile.
- Una cola alta NO siempre significa "necesito más capacity". Puede ser un query bloqueador que se resuelve optimizándolo.
- Spill alto puede indicar que un warehouse XS debería ser S, O que un join está mal escrito.

## Tablas requeridas

- `system.query.history` (SELECT)
