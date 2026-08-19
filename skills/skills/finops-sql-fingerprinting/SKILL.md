---
name: finops-sql-fingerprinting
description: Agrupa queries SQL por fingerprint normalizado y clasifica patrones de ineficiencia (spill, colas, joins explosivos, filtros tardíos). Usar cuando el usuario pregunte cuáles queries consumen más recursos, necesite un backlog de optimización SQL, o quiera identificar patrones problemáticos en Databricks SQL.
---

# Fingerprinting de Queries SQL

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Cuáles queries son las más costosas?"
- "¿Qué patrones SQL deberíamos optimizar primero?"
- "¿Hay queries con joins explosivos o spill?"
- "Dame un backlog de queries para investigar"
- "¿Cuáles queries tienen problemas de rendimiento?"

## Query SQL

```sql
WITH query_runs AS (
  SELECT
    workspace_id,
    compute.warehouse_id                   AS warehouse_id,
    REGEXP_REPLACE(
      REGEXP_REPLACE(LOWER(statement_text), '''[^'']*''', '?'),
      '\\b[0-9]+(\\.[0-9]+)?\\b', '?'
    )                                      AS query_fingerprint,
    statement_id,
    execution_status,
    total_duration_ms,
    waiting_at_capacity_duration_ms,
    read_bytes,
    read_rows,
    produced_rows,
    spilled_local_bytes,
    shuffle_read_bytes
  FROM system.query.history
  WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
    AND compute.warehouse_id IS NOT NULL
), patterns AS (
  SELECT
    workspace_id,
    warehouse_id,
    query_fingerprint,
    COUNT(*)                                              AS executions,
    COUNT_IF(execution_status = 'FAILED')                AS failures,
    PERCENTILE_APPROX(total_duration_ms, 0.95)           AS p95_total_ms,
    AVG(waiting_at_capacity_duration_ms)                 AS avg_capacity_wait_ms,
    SUM(COALESCE(read_bytes, 0))                         AS read_bytes,
    SUM(COALESCE(read_rows, 0))                          AS read_rows,
    SUM(COALESCE(produced_rows, 0))                      AS produced_rows,
    SUM(COALESCE(spilled_local_bytes, 0))                AS spilled_bytes,
    SUM(COALESCE(shuffle_read_bytes, 0))                 AS shuffle_bytes,
    MAX_BY(statement_id, total_duration_ms)              AS example_statement_id
  FROM query_runs
  GROUP BY ALL
)
SELECT
  *,
  CASE
    WHEN spilled_bytes > 536870912        THEN 'CRITICAL_SPILL'
    WHEN avg_capacity_wait_ms > 15000     THEN 'CRITICAL_QUEUE'
    WHEN produced_rows > read_rows * 10
         AND read_rows > 0               THEN 'EXPLODING_JOIN'
    WHEN read_rows > produced_rows * 10
         AND produced_rows > 0           THEN 'FILTER_AFTER_READ'
    WHEN p95_total_ms > 90000            THEN 'CRITICAL_RUNTIME'
    ELSE 'REVIEW'
  END AS primary_signal
FROM patterns
ORDER BY p95_total_ms DESC, executions DESC
LIMIT 100;
```

## Señales y su interpretación

| Señal | Significa | Acción recomendada |
|-------|----------|-------------------|
| CRITICAL_SPILL | >512MB de datos derramados a disco | Optimizar SQL, revisar joins, considerar warehouse más grande |
| CRITICAL_QUEUE | >15s esperando capacidad | Escalar warehouse o aislar workloads |
| EXPLODING_JOIN | produced_rows > read_rows × 10 | Revisar condiciones de JOIN (cross join accidental) |
| FILTER_AFTER_READ | read_rows > produced_rows × 10 | Mover filtros más cerca del scan (pushdown) |
| CRITICAL_RUNTIME | p95 > 90 segundos | Revisar Query Profile para plan físico |

## Notas importantes

- Los umbrales son **señales de priorización**, no pruebas de causa raíz. Confirmar con Query Profile.
- El `example_statement_id` permite navegar directamente al Query Profile de la ejecución más lenta.
- El fingerprint normaliza literales de texto y números para agrupar queries equivalentes.
- El regex usa `\\b` (doble backslash) para word boundary — requerido en contextos SQL.

## Tablas requeridas

- `system.query.history` (SELECT)
