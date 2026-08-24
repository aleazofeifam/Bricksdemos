---
name: pipeline-error-handling-retry
description: Patrones de manejo de errores en pipelines — dead-letter queues, retry con backoff exponencial, cuarentena de registros inválidos, alertas por umbral de errores. Úsala cuando un pipeline deba ser resiliente a datos corruptos, timeouts de API, o fuentes intermitentes sin perder datos.
---

# Pipeline Error Handling & Retry Patterns

Cómo hacer pipelines resilientes: separar happy path de error path, cuarentena, retry, y alertas.

## Patrón 1: Dead Letter Table (DLT/Delta)

```python
import dlt
from pyspark.sql.functions import current_timestamp, lit

@dlt.table(name="silver_orders")
@dlt.expect_or_drop("valid_amount", "amount > 0")
@dlt.expect_or_drop("valid_id", "order_id IS NOT NULL")
def silver_orders():
    return dlt.read_stream("bronze_orders")

# Tabla de cuarentena: filas que fallaron validación
@dlt.table(name="quarantine_orders")
def quarantine_orders():
    return (
        dlt.read_stream("bronze_orders")
        .filter("amount <= 0 OR order_id IS NULL")
        .withColumn("quarantine_reason",
            lit("amount <= 0 OR order_id IS NULL"))
        .withColumn("quarantined_at", current_timestamp())
    )
```

## Patrón 2: Retry con Backoff para APIs externas

```python
import time
import requests
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType

def call_api_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:  # Rate limit
                wait = 2 ** attempt  # Exponential backoff
                time.sleep(wait)
            else:
                return None
        except requests.Timeout:
            time.sleep(2 ** attempt)
    return None  # Dead letter after max retries

# Usar con mapPartitions para control por partición
def enrich_partition(partition):
    for row in partition:
        result = call_api_with_retry(f"https://api.example.com/{row.id}")
        yield {**row.asDict(), "api_result": result}
```

## Patrón 3: Alerta por tasa de error

```sql
-- Alert: dispara si error rate > 5% en última hora
SELECT
  COUNT_IF(quarantine_reason IS NOT NULL) * 100.0 / COUNT(*) AS error_rate_pct
FROM production.silver.quarantine_orders
WHERE quarantined_at >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
HAVING error_rate_pct > 5.0
```

## Gotchas

* En DLT no hay try/except nativo — usar `expect_or_drop` como cuarentena + tabla paralela que captura los rechazados.
* En Structured Streaming, un error en un micro-batch puede parar TODO el stream. Usar `foreachBatch` con try/except interno.
* APIs con rate-limit: `time.sleep()` en UDF ejecuta POR EXECUTOR. Con 8 executors y 100 partitions, puedes generar 800 requests simultáneas. Usar `mapPartitions` con semaphore por partición.
* Los registros en cuarentena deben revisarse manualmente. Crear un job semanal que alerte si la quarantine table crece >1000 filas.
* NUNCA silenciar errores sin log. Toda fila descartada debe ir a quarantine con: razón, timestamp, source file/batch.
* Para retry de jobs completos: usar `max_retries` en task config del job (no reinventar retry en código).
* El backoff exponencial debe tener un CAP (ej: max 60s). Sin cap, el tercer retry espera 8s, el quinto 32s, el décimo >17 minutos.
