---
name: file-format-conversion-optimization
description: Patrones de conversión y optimización de formatos de archivo — Parquet/Iceberg a Delta, CSV/JSON legacy a Delta optimizado, COPY INTO patterns, liquid clustering strategy, y OPTIMIZE/VACUUM scheduling. Úsala cuando datos llegan en formato subóptimo y necesitas optimizarlos para queries analíticos.
---

# File Format Conversion & Delta Optimization

Estrategias para convertir datos legacy a Delta optimizado y mantener tablas performantes.

## Conversión por formato de origen

### Parquet existente → Delta (in-place)
```sql
-- Sin copia de datos, convierte metadatos
CONVERT TO DELTA parquet.`s3://bucket/legacy/parquet_table/`;
-- Registrar en UC
CREATE TABLE production.raw.legacy_table
USING DELTA LOCATION 's3://bucket/legacy/parquet_table/';
```

### CSV/JSON → Delta (con COPY INTO)
```sql
COPY INTO production.bronze.raw_events
FROM 's3://bucket/landing/events/'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true', 'mergeSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true');
```

### Iceberg → Delta
```sql
-- Leer tabla Iceberg y materializar como Delta
CREATE TABLE production.raw.from_iceberg AS
SELECT * FROM iceberg.`s3://bucket/iceberg_table/`;
```

## Optimización post-conversión

```sql
-- 1. Liquid clustering (reemplazo moderno de particiones + Z-ORDER)
ALTER TABLE production.gold.orders CLUSTER BY (order_date, region);

-- 2. Optimizar (compacta small files + aplica clustering)
OPTIMIZE production.gold.orders;

-- 3. Vacuum (elimina archivos obsoletos)
VACUUM production.gold.orders RETAIN 168 HOURS;  -- 7 días
```

## Scheduling recomendado

| Tabla | OPTIMIZE | VACUUM | Clustering |
|-------|----------|--------|------------|
| Bronze (append-heavy) | Diario | Semanal | (date) |
| Silver (merge) | Post-merge | Semanal | (id, date) |
| Gold (queries BI) | Diario 3AM | Semanal | (date, region) |

## Gotchas

* `CONVERT TO DELTA` es in-place SOLO para Parquet en external locations. CSV/JSON requiere COPY INTO (sí copia datos).
* Liquid clustering REEMPLAZA particiones tradicionales. NO uses `PARTITIONED BY` + `CLUSTER BY` juntos.
* Small file problem: archivos <128MB degradan performance. Síntoma: miles de archivos pequeños tras ingesta granular. Solución: OPTIMIZE o habilitar auto-compaction (`delta.autoOptimize.optimizeWrite = true`).
* VACUUM default retiene 7 días. NO bajar a <1h en producción si hay queries concurrentes (pueden fallar al leer archivos ya borrados).
* Liquid clustering columns: elegir las columnas más usadas en WHERE/JOIN (máximo 4). Cambiar clustering columns es barato (solo aplica en próximo OPTIMIZE).
* `OPTIMIZE` en tablas >1TB puede tardar horas. Usar `WHERE` clause para optimizar por partición: `OPTIMIZE table WHERE date >= '2026-08-01'`.
* Para migración masiva (500K+ archivos): usar Auto Loader con `cloudFiles.maxFilesPerTrigger` para procesar en batches y no saturar el cluster.
