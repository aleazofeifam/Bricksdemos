---
name: etl-to-sdp-refactor
description: >
  Refactoriza código ETL tradicional (notebooks PySpark, scripts SQL, spark.read/write manuales)
  a Spark Declarative Pipelines (SDP/DLT). Lee el código fuente, hace preguntas de clarificación,
  genera el pipeline refactorizado, y orquesta otros skills (data-quality-expectations para
  expectations, databricks-spark-declarative-pipelines para sintaxis). Úsala cuando el usuario
  diga "migrar a DLT", "refactorizar a SDP", "convertir mi ETL", "modernizar pipeline",
  "pasar a streaming tables", o tenga código legacy con spark.read().write() que quiera
  convertir a declarativo.
---

# ETL-to-SDP Refactor

Este skill convierte código ETL imperativo en Spark Declarative Pipelines.
**No requiere LLM externo** — tú (Genie Code) ERES el motor de transcripción.

## Workflow Paso a Paso

### Paso 1: Leer el Código Fuente

1. Pide al usuario que indique el notebook/archivo a refactorizar
2. Usa `readAssetById` para leer el contenido completo
3. Identifica:
   - Fuentes de datos (tablas, archivos, APIs)
   - Transformaciones (joins, aggregations, filters)
   - Destinos (tablas Delta, archivos)
   - Orquestación (loops, condicionales, dependencias entre pasos)

### Paso 2: Preguntas de Clarificación (OBLIGATORIO)

Antes de generar código, SIEMPRE pregunta:

```
1. ¿Batch o Streaming? (¿Los datos llegan continuamente o se procesan por lotes?)
2. ¿Medallion architecture? (¿Quieres Bronze → Silver → Gold o flat?)
3. ¿Hay CDC/SCD? (¿Necesitas APPLY CHANGES para capturar cambios?)
4. ¿Catálogo destino? (¿En qué catalog.schema quieres las tablas?)
5. ¿Expectativas de calidad? (¿Qué reglas de validación aplican?)
6. ¿Frecuencia de ejecución? (Continuo, triggered, scheduled?)
```

Si el código fuente ya deja claro alguno de estos puntos, no preguntes — infiere.

### Paso 3: Mapeo de Patrones

Usa esta tabla de equivalencias:

| ETL Tradicional | SDP Equivalente |
| --- | --- |
| `spark.read.format("csv").load(path)` | `@dlt.table` + `spark.readStream.format("cloudFiles")` (Auto Loader) |
| `spark.read.table("source")` | `@dlt.table` + `spark.read.table("source")` o `dlt.read("bronze_table")` |
| `df.write.mode("overwrite").saveAsTable()` | `@dlt.table` (materialized view, auto-managed) |
| `df.write.mode("append").saveAsTable()` | `@dlt.table` con streaming (streaming table) |
| `MERGE INTO target USING source` | `dlt.apply_changes()` (CDC) |
| `INSERT OVERWRITE partition` | `@dlt.table` con partition pruning natural |
| Manual error handling (try/except) | `@dlt.expect*` decorators |
| Orchestration notebook (dbutils.notebook.run) | Dependencias implícitas via `dlt.read()` |
| `spark.sql("CREATE TABLE IF NOT EXISTS")` | Eliminado — SDP maneja DDL automáticamente |

### Paso 4: Generar Código SDP

Estructura del output:

```python
# Pipeline: {nombre_descriptivo}
# Refactorizado desde: {path_original}
# Fecha: {fecha}

import dlt
from pyspark.sql.functions import *

# ═══════════════════════════════════════
# BRONZE LAYER — Ingesta cruda
# ═══════════════════════════════════════

@dlt.table(
    comment="Ingesta cruda desde {fuente}",
    table_properties={"quality": "bronze"}
)
def bronze_{nombre}():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "{formato}")
        .option("cloudFiles.schemaLocation", "{checkpoint}")
        .load("{path}")
    )

# ═══════════════════════════════════════
# SILVER LAYER — Limpieza y tipado
# ═══════════════════════════════════════

@dlt.table(comment="Datos limpios y tipados")
@dlt.expect_or_drop("valid_id", "id IS NOT NULL")
def silver_{nombre}():
    return (
        dlt.read_stream("bronze_{nombre}")
        .select(
            col("id").cast("long"),
            # ... transformaciones del código original
        )
    )

# ═══════════════════════════════════════
# GOLD LAYER — Agregaciones de negocio
# ═══════════════════════════════════════

@dlt.table(comment="Métricas agregadas para reporting")
def gold_{nombre}():
    return (
        dlt.read("silver_{nombre}")
        .groupBy("dimension")
        .agg(sum("metric").alias("total_metric"))
    )
```

### Paso 5: Orquestar Otros Skills (CRÍTICO)

Después de generar el código base:

1. **Carga `data-quality-expectations`** — Para agregar expectations estandarizadas:
   - Pregunta al usuario qué reglas de calidad aplican
   - Aplica el catálogo estándar de expectations del skill
   - Agrega `@dlt.expect`, `@dlt.expect_or_drop`, `@dlt.expect_or_fail`

2. **Referencia `databricks-spark-declarative-pipelines`** (built-in) — Para:
   - Sintaxis correcta de `apply_changes` (CDC/SCD Type 2)
   - Configuración de pipeline (channel, photon, serverless)
   - Patrones de Auto Loader avanzados

3. **Referencia `pipeline-error-handling-retry`** — Si el ETL original tenía:
   - Try/except blocks
   - Retry logic
   - Dead letter patterns

4. **Referencia `pipeline-observability-sla`** — Para agregar:
   - Tags de monitoreo
   - Integración con system tables para SLA tracking

### Paso 6: Crear el Pipeline Asset

Una vez aprobado el código:

```
1. Usa createAsset(assetType="pipeline", name="{nombre}") para crear el pipeline
2. Navega con openAsset + continueMessage describiendo la estructura
3. El pipeline editor agent completará la configuración (compute, catalog, channel)
```

## Decisiones Automáticas (no preguntar)

| Si el código fuente tiene... | Entonces usa... |
| --- | --- |
| `.readStream` o streaming source | Streaming Table |
| `.read` (batch) con aggregation | Materialized View |
| `.read` (batch) sin aggregation | Streaming Table con `triggered` |
| `MERGE INTO` con key columns | `apply_changes(keys=[...])` |
| Multiple notebooks con `dbutils.notebook.run` | Un solo archivo SDP con dependencias `dlt.read()` |
| Hardcoded paths `/mnt/...` | Volume paths `/Volumes/catalog/schema/volume/` |

## Gotchas y Anti-patterns

* **NO** conviertas `try/except` en código SDP — las expectations reemplazan error handling
* **NO** uses `spark.sql("CREATE TABLE")` — SDP maneja DDL
* **NO** mantengas `dbutils.widgets` — usa pipeline parameters en su lugar
* **NO** uses `display()` — SDP no es interactivo
* **CUIDADO** con UDFs — funcionan pero Photon no las optimiza, prefiere funciones built-in
* **CUIDADO** con `.coalesce(1)` — SDP optimiza archivos automáticamente
* Si el ETL original usa `foreachBatch`, evalúa si `apply_changes` o un simple streaming table lo reemplaza
* Variables globales y state entre celdas → refactorizar como funciones independientes por tabla

## Ejemplo Completo: De Imperativo a Declarativo

### ANTES (ETL tradicional):
```python
# Celda 1: Lectura
df_raw = spark.read.format("csv").option("header", True).load("/mnt/data/sales/")
df_raw.write.mode("overwrite").saveAsTable("default.raw_sales")

# Celda 2: Limpieza
df_clean = spark.table("default.raw_sales").filter("amount > 0").dropDuplicates(["order_id"])
df_clean.write.mode("overwrite").saveAsTable("default.clean_sales")

# Celda 3: Aggregation
df_agg = spark.table("default.clean_sales").groupBy("region").agg(sum("amount").alias("total"))
df_agg.write.mode("overwrite").saveAsTable("default.sales_by_region")
```

### DESPUÉS (SDP):
```python
import dlt
from pyspark.sql.functions import *

@dlt.table(comment="Ingesta incremental de ventas con Auto Loader")
def bronze_sales():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaHints", "amount DOUBLE, order_id STRING")
        .load("/Volumes/catalog/schema/landing/sales/")
    )

@dlt.table(comment="Ventas validadas y deduplicadas")
@dlt.expect_or_drop("positive_amount", "amount > 0")
@dlt.expect("has_order_id", "order_id IS NOT NULL")
def silver_sales():
    return (
        dlt.read_stream("bronze_sales")
        .dropDuplicates(["order_id"])
    )

@dlt.table(comment="Ventas agregadas por región para dashboards")
def gold_sales_by_region():
    return (
        dlt.read("silver_sales")
        .groupBy("region")
        .agg(sum("amount").alias("total_sales"))
    )
```

## Validación Post-Refactor

Después de generar, verifica:
- [ ] Todas las tablas destino del ETL original tienen equivalente SDP
- [ ] No hay `spark.sql("CREATE/DROP")` residual
- [ ] Auto Loader reemplaza lecturas batch de archivos
- [ ] Expectations cubren las validaciones del try/except original
- [ ] Paths usan `/Volumes/` en vez de `/mnt/` o `/dbfs/`
- [ ] El catálogo/schema destino está configurado a nivel pipeline (no hardcoded)
