---
name: backfill-reprocessing-patterns
description: Planifica y ejecuta backfills, replay y reprocessing histórico de pipelines sin introducir duplicados, pérdida de datos o cambios downstream inesperados. Úsala después de bugs de transformación, lógica nueva, datos faltantes, cambios de schema, correcciones históricas, necesidad de replay o recuperación de streaming state.
---

# Backfill & Reprocessing Patterns

Un backfill es una operación de migración sobre datos existentes.

Tratarlo como operación potencialmente destructiva.

## Core workflow

**Diagnose → Scope → Protect → Plan → Validate → Execute → Reconcile → Observe**

Nunca empezar ejecutando `MERGE`, full refresh o reset de checkpoint.

---

## 1. Diagnose the reason

Clasificar:

```text
A. Missing historical data
B. Transformation bug
C. New business logic
D. Schema correction
E. Source correction
F. CDC correction
G. Invalid/corrupted streaming checkpoint
H. Late-arriving data
```

La causa determina la estrategia.

---

## 2. Identify affected layer

```text
Bronze
Silver
Gold
Semantic layer
Multiple layers
```

Preguntar:

**¿El dato original todavía existe?**

Esto es crítico antes de cualquier full refresh.

---

## 3. Define the scope

Registrar:

```text
Target:
Date/key range:
Expected records:
Source:
Current downstream consumers:
Streaming readers:
Business criticality:
Allowed downtime:
```

Evitar términos ambiguos como:

```text
"reprocesar los datos recientes"
```

Definir rangos concretos.

---

## 4. Inspect source durability

Para streaming verificar:

```text
Kafka/event retention
source files retention
CDC log retention
bronze history
Delta history
```

No realizar full refresh cuando el source ya no contiene los datos requeridos para reconstruir el target.

---

## 5. Protect current state

Antes de operaciones de riesgo registrar:

```text
Delta table version
pipeline update ID
row counts
critical aggregates
timestamp
```

Cuando criticidad lo requiera, crear una estrategia de backup compatible con el workload.

No copiar terabytes automáticamente sólo por precaución.

---

# Decision framework

## Pattern A: ONE-TIME append backfill

Preferir cuando se necesita agregar datos históricos a una streaming table sin reconstruirla.

Ejemplo:

```python
from pyspark import pipelines as dp

@dp.table(
    name="events",
    comment="Eventos consolidados del sistema."
)
def events():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/Volumes/production/events/current/")
    )

@dp.append_flow(
    target="events",
    name="historical_backfill",
    once=True
)
def historical_backfill():
    return (
        spark.read
        .format("json")
        .load("/Volumes/production/events/backfill/")
    )
```

El `once=True` vuelve a ejecutarse después de un full refresh.

Tenerlo en cuenta.

---

## Pattern B: Recompute a Materialized View

Para una materialized view cuya lógica cambió:

considerar primero refresh normal.

Lakeflow puede determinar incrementalización cuando sea apropiado.

Utilizar full refresh sólo cuando se necesite explícitamente recalcular todo.

---

## Pattern C: Full refresh

Aplicar únicamente cuando:

- el source conserva todo lo necesario;
- el costo es aceptable;
- reconstruir target es semánticamente correcto.

Para streaming table, full refresh:

- elimina datos actuales del target;
- elimina checkpoints;
- reprocesa el source.

Esto puede perder historia si el source ya expiró.

---

## Pattern D: Selective checkpoint reset

Utilizar para recuperación/replay de streaming cuando:

- es necesario preservar los datos actuales;
- existe una posición confiable para reanudar/replay;
- el sink es idempotente;
- se ha comprendido el efecto del replay.

Utilizar mecanismos soportados por Lakeflow pipelines.

No modificar manualmente archivos internos del checkpoint.

---

## Pattern E: New table + validation + cutover

Preferir cuando:

- cambia fuertemente la semántica;
- se modifica grain;
- hay alto riesgo downstream;
- se necesita comparar old/new;
- el backfill es muy grande.

Patrón:

```text
target_v1
   ↓

build target_v2
   ↓
validate
   ↓
consumer validation
   ↓
cutover
   ↓
observe
   ↓
retire v1
```

No hacer rename/swap sin revisar dependencias y contratos.

---

## Pattern F: Targeted correction

Para corrections idempotentes sobre tablas Delta no administradas por un flujo que deba preservar su ownership:

evaluar:

- MERGE;
- replaceWhere;
- partition overwrite;
- transaction.

Seleccionar por semántica.

No usar MERGE sólo porque "es incremental".

---

## 6. Idempotency

Antes de ejecutar responder:

```text
¿Qué ocurre si el backfill corre dos veces?
```

La respuesta deseada suele ser:

```text
el resultado final no cambia
```

Validar:

- business keys;
- sequence;
- merge semantics;
- deduplication;
- AUTO CDC;
- append behavior.

---

## 7. Impact analysis

Revisar:

```text
downstream streaming
materialized views
Metric Views
dashboards
Genie Agents
models
exports
applications
```

Un backfill puede producir:

- cambios históricos visibles;
- nuevos registros;
- métricas diferentes;
- downstream spikes.

Notificar a owners relevantes antes de operaciones críticas.

---

## 8. Dry validation

Antes de escribir calcular:

```text
expected rows
affected keys
expected aggregates
date range
invalid records
duplicates
```

Ejemplo:

```sql
SELECT
    MIN(order_date) AS desde,
    MAX(order_date) AS hasta,
    COUNT(*) AS registros,
    COUNT(DISTINCT order_id) AS pedidos
FROM source
WHERE order_date BETWEEN :start_date AND :end_date;
```

---

## 9. Execute in bounded scope

Cuando sea posible:

- empezar por pequeño rango;
- validar;
- ampliar.

No convertir un backfill controlable en un full-table operation innecesario.

---

## 10. Reconcile

Después:

### Volume

```text
before
expected delta
after
```

### Keys

```text
missing
duplicates
unexpected
```

### Business

```text
balances
revenue
orders
customer counts
```

### Quality

```text
expectation violations
NULL
invalid domain
```

---

## 11. Compare historical versions

Cuando Delta history permita hacerlo, comparar estado anterior y posterior.

No utilizar Time Travel como único mecanismo de rollback si retención o policies pueden eliminar archivos.

---

## 12. Observe downstream

Después del backfill revisar:

- pipeline runs;
- backlog;
- errors;
- quality;
- BI results;
- Genie answers críticas;
- business reconciliation.

---

## Output

```text
Reason:
Target:
Scope:

Source durability:
- ...

Strategy:
- append once
- refresh
- full refresh
- reset checkpoint
- new table
- targeted correction

Idempotency:
- ...

Pre-state:
- ...

Expected impact:
- ...

Validation:
- ...

Execution:
- ...

Reconciliation:
- ...

Rollback/recovery:
- ...
```

---

# Definition of Done

- [ ] La causa está identificada.
- [ ] Existe un scope exacto.
- [ ] Se verificó disponibilidad histórica del source.
- [ ] Se registró estado previo.
- [ ] Se analizó downstream.
- [ ] Se verificó idempotencia.
- [ ] Se eligió la operación mínima necesaria.
- [ ] No se modificaron checkpoints manualmente.
- [ ] Se validó antes de ejecutar.
- [ ] Se reconciliaron resultados.
- [ ] Se observaron consumers downstream.
- [ ] La ejecución quedó documentada en español.

# Gotchas

- Full refresh de streaming puede destruir datos no recuperables.
- `once=True` vuelve a ejecutarse tras full refresh.
- Replay puede duplicar datos en sinks no idempotentes.
- El checkpoint no es un artefacto para editar manualmente.
- COUNT no valida un backfill.
- Una corrección histórica puede cambiar KPIs downstream aunque el pipeline esté healthy.
