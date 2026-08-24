---
name: backfill-reprocessing-patterns
description: Reprocesar datos históricos sin duplicar ni perder estado del streaming. Patrones de backfill para Delta, DLT, y Structured Streaming — full refresh selectivo, merge incremental, checkpoint reset seguro. Úsala cuando un pipeline requiera re-calcular datos pasados por bug fix, schema change, o nueva lógica de transformación.
---

# Backfill & Reprocessing Patterns

Cómo reprocesar datos históricos de forma segura sin duplicar, sin perder streaming state, y sin romper downstream.

## Decision Framework

| Escenario | Estrategia | Riesgo |
|-----------|-----------|--------|
| Bug en transformación (silver/gold) | MERGE overwrite parcial | Bajo |
| Schema change en source | Full refresh DLT + revalidar | Medio |
| Nueva lógica completa | Tabla nueva + swap | Bajo |
| Streaming con checkpoint corrupto | Clone checkpoint + reset offset | Alto |

## Patrón 1: MERGE Overwrite Parcial (recomendado)

```sql
-- Re-calcular últimos 30 días de silver desde bronze
MERGE INTO production.silver.orders AS target
USING (
  SELECT * FROM production.bronze.raw_orders
  WHERE order_date >= CURRENT_DATE() - INTERVAL 30 DAYS
) AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

## Patrón 2: Full Refresh selectivo en DLT

```python
# En el pipeline DLT, usar FULL REFRESH solo en la tabla afectada:
# UI: Pipeline > Select table > "Full refresh"
# CLI: databricks pipelines start-update --pipeline-id <ID> --full-refresh-selection "silver_orders"
```

## Patrón 3: Tabla nueva + swap (zero-downtime)

```sql
-- 1. Crear tabla nueva con lógica corregida
CREATE TABLE production.silver.orders_v2 AS
SELECT ... FROM production.bronze.raw_orders;

-- 2. Validar counts y checksums
SELECT 'v1' AS version, COUNT(*) FROM production.silver.orders
UNION ALL
SELECT 'v2', COUNT(*) FROM production.silver.orders_v2;

-- 3. Swap atómico
ALTER TABLE production.silver.orders RENAME TO production.silver.orders_deprecated;
ALTER TABLE production.silver.orders_v2 RENAME TO production.silver.orders;

-- 4. Limpiar después de validar downstream (7 días)
DROP TABLE production.silver.orders_deprecated;
```

## Gotchas

* En DLT, `FULL REFRESH` borra TODO el historial de la tabla (no es selectivo por partición). Para backfill parcial, usa MERGE externo al pipeline.
* Streaming checkpoints son BINARIOS — no editables a mano. Si necesitas reset: clonar el directorio de checkpoint y borrar el `offsets/` file para reiniciar desde cero.
* Después de un MERGE masivo, ejecutar `OPTIMIZE` para evitar small files.
* SIEMPRE validar count + checksum antes vs después del backfill. Fórmula: `SELECT COUNT(*), SUM(hash(order_id, amount)) FROM table`.
* Notificar downstream ANTES de un backfill grande — puede causar spikes de procesamiento en pipelines que leen la tabla.
* Delta Time Travel permite ver el estado pre-backfill: `SELECT * FROM table VERSION AS OF <pre_version>` — útil para debugging post-backfill.
* Para streaming: el backfill NO se propaga automáticamente por streaming readers (solo ven appends nuevos). Usar `FULL REFRESH` en DLT streaming table o re-crear el reader.
