---
name: pipeline-observability-sla
description: Configura observabilidad end-to-end para pipelines de datos — alertas de freshness, SLA monitoring con system tables, dashboards de salud operativa, y escalation paths. Úsala cuando el usuario necesite monitorear que un pipeline cumple su SLA, detectar degradaciones de latencia, o crear alertas de freshness sobre tablas destino.
---

# Pipeline Observability & SLA Monitoring

Guía para implementar observabilidad proactiva en pipelines de datos usando system tables de Databricks, alertas SQL, y dashboards de salud operativa.

## Instrucciones paso a paso

1. **Definir el SLA** — Acuerda con el consumidor: "la tabla gold debe estar fresca antes de las 6AM del timezone del negocio".
2. **Consultar freshness real** — Usa `information_schema.tables.last_altered` o `system.access.table_lineage` para medir cuándo se actualizó por última vez.
3. **Crear alert de freshness** — SQL alert que dispara si `last_altered` está por detrás del SLA.
4. **Dashboard de salud** — Combina: p95 de duración por pipeline, tasa de fallo (últimos 7d), data delay (tiempo entre evento y disponibilidad en gold).
5. **Escalation path** — Documenta: alerta → Slack channel → on-call → escalate si >2h sin resolución.

## Ejemplo: SLA de freshness matutino

```sql
-- Alert query: dispara si gold_orders no se actualizó antes de 6AM
SELECT
  full_name,
  last_altered,
  CASE WHEN last_altered < CURRENT_DATE() + INTERVAL 6 HOURS
       THEN 'OK' ELSE 'SLA BREACH' END AS status
FROM system.information_schema.tables
WHERE table_catalog = 'production'
  AND table_schema = 'gold'
  AND table_name = 'orders'
  AND last_altered < CURRENT_DATE() + INTERVAL 6 HOURS
```

```sql
-- Dashboard: pipeline health últimos 7 días
SELECT
  pipeline_name,
  COUNT(*) AS total_runs,
  COUNT_IF(state = 'COMPLETED') AS successful,
  COUNT_IF(state = 'FAILED') AS failed,
  ROUND(COUNT_IF(state = 'FAILED') * 100.0 / COUNT(*), 1) AS failure_rate_pct,
  PERCENTILE(duration_seconds, 0.95) AS p95_duration_sec
FROM system.lakeflow.pipeline_events
WHERE event_date >= CURRENT_DATE() - 7
GROUP BY pipeline_name
ORDER BY failure_rate_pct DESC
```

## Gotchas

* `information_schema.tables.last_altered` refleja DDL/DML pero tiene lag de ~5 minutos — no es real-time.
* El SLA se mide en la tabla DESTINO (end-to-end), no en el pipeline source. Un pipeline exitoso pero lento puede romper el SLA.
* Las alertas de Databricks SQL solo evalúan resultados de queries SQL (no métricas arbitrarias). Si necesitas métrica custom, materialízala en una tabla primero.
* `system.lakeflow.pipeline_events` requiere que el workspace tenga system tables habilitadas. Verifica con `SELECT * FROM system.lakeflow.pipeline_events LIMIT 1`.
* Para pipelines con múltiples tablas destino, mide freshness de la ÚLTIMA tabla en el DAG (la más downstream).
* Los dashboards de health deben tener refresh automático ≥ 1h (no más frecuente, por policy del workspace).
* Considera incluir data delay (evento_timestamp vs ingestion_timestamp) además de freshness — un pipeline puede correr a tiempo pero con datos de hace 2 horas.
