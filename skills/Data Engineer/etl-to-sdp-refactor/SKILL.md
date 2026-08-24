---
name: etl-to-sdp-refactor
description: Refactoriza ETL imperativo, notebooks PySpark/SQL, pipelines DLT legacy y orquestación manual hacia Lakeflow pipelines basados en Spark Declarative Pipelines. Úsala cuando existan spark.read/write manuales, MERGE imperativos para CDC, dbutils.notebook.run, código DLT antiguo, pipelines difíciles de mantener o solicitudes de "modernizar ETL", "migrar DLT", "convertir a SDP" o "usar Spark Declarative Pipelines".
---

# ETL to Spark Declarative Pipelines Refactor

Convierte pipelines imperativos en pipelines declarativos, testeables, documentados y operables.

## Objetivo

El resultado debe:

- preservar la semántica del pipeline original;
- reducir orquestación manual;
- favorecer incrementalidad;
- utilizar APIs modernas de Lakeflow pipelines;
- aplicar calidad en el punto correcto;
- mantener lógica de transformación testeable;
- producir tablas documentadas para consumidores posteriores;
- evitar introducir productos Databricks que el workload no necesita.

## Regla de plataforma

Para código nuevo utilizar:

```python
from pyspark import pipelines as dp
```

No generar nuevo código basado en:

```python
import dlt
```

salvo que el usuario solicite explícitamente mantener sintaxis DLT legacy.

---

# Workflow

**Inspect → Model → Decide → Refactor → Test → Validate → Publish → Handoff**

---

## 1. Inspect: entender primero el pipeline existente

Leer todo el código relevante antes de escribir la nueva implementación.

Inventariar:

```text
Fuentes:
- archivos
- tablas
- Kafka/event streams
- bases de datos
- APIs

Destinos:
- tablas
- archivos
- sistemas externos

Transformaciones:
- filters
- joins
- aggregations
- deduplication
- CDC
- SCD
- enrichment

Estado:
- checkpoints
- watermarks
- incremental cursors

Orquestación:
- notebooks
- jobs
- dependencies
- loops
- retries

Calidad:
- validaciones
- asserts
- quarantine
- exception handling

Consumidores:
- dashboards
- Genie Agents
- ML
- aplicaciones
- exports
```

No empezar traduciendo línea por línea.

---

## 2. Model: reconstruir el DAG lógico

Transformar la implementación actual en un grafo conceptual:

```text
source
  ↓
ingestion
  ↓
cleaning
  ↓
conformance
  ↓
business transformation
  ↓
serving
```

Para cada nodo registrar:

```text
Nombre:
Fuente:
Tipo de procesamiento:
Grain:
Keys:
Incrementalidad:
Output:
Consumidores:
Quality rules:
```

Detectar lógica duplicada y side effects.

---

## 3. Decide: separar ingestión de transformación cuando corresponda

Por defecto, considerar:

```text
Pipeline A
INGESTION / BRONZE
        ↓
Pipeline B
TRANSFORMATION / SILVER + GOLD
```

Separarlos cuando:

- ingestion debe continuar aunque falle una transformación downstream;
- tienen schedules distintos;
- requieren ownership diferente;
- tienen SLAs diferentes;
- necesitan ciclos de despliegue independientes.

Mantenerlos juntos cuando la simplicidad operacional sea claramente superior y el DAG sea pequeño/cohesivo.

No imponer Medallion Architecture sólo por convención.

---

## 4. Choose the correct dataset type

### Streaming Table

Preferir cuando:

- la fuente es incremental o streaming;
- se deben procesar nuevos registros conforme llegan;
- existe checkpoint/state;
- se consume CDC;
- se necesita procesamiento incremental basado en offsets.

Ejemplo:

```python
from pyspark import pipelines as dp

@dp.table(
    name="orders_bronze",
    comment="Pedidos ingeridos incrementalmente desde archivos de origen."
)
def orders_bronze():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/Volumes/production/landing/orders/")
    )
```

### Materialized View

Preferir cuando:

- el resultado se define naturalmente como una consulta sobre el estado actual de sus fuentes;
- Databricks puede administrar su refresh;
- no existe necesidad semántica de tratar cada registro como evento incremental independiente.

Ejemplo:

```python
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    name="sales_by_region",
    comment="Ventas agregadas por región para consumo analítico."
)
def sales_by_region():
    return (
        spark.read.table("orders_silver")
        .groupBy("region")
        .agg(F.sum("amount").alias("total_sales"))
    )
```

### Temporary View

Usar para lógica intermedia que:

- mejora legibilidad;
- se reutiliza dentro del pipeline;
- no necesita publicarse como activo persistente.

### Append Flow

Evaluar para:

- múltiples fuentes escribiendo al mismo target;
- backfills puntuales;
- cargas `ONCE`.

---

## 5. CDC: usar AUTO CDC antes de MERGE imperativo

Cuando el pipeline procesa cambios de registros:

Identificar:

```text
Primary/business key:
Sequence column:
Delete semantics:
SCD Type 1 o 2:
Columns de historial:
Out-of-order events:
```

Preferir AUTO CDC.

Ejemplo conceptual:

```python
from pyspark import pipelines as dp

dp.create_streaming_table(
    name="customers_silver",
    comment="Estado gobernado de clientes derivado del flujo CDC."
)

dp.create_auto_cdc_flow(
    target="customers_silver",
    source="customers_cdc_bronze",
    keys=["customer_id"],
    sequence_by="sequence_timestamp",
    stored_as_scd_type=1
)
```

No traducir `MERGE` a AUTO CDC automáticamente.

Primero confirmar que el `MERGE` representa realmente change data capture.

---

## 6. Keep transformation logic testable

Separar lógica PySpark pura del wrapper declarativo.

Preferir:

```python
# transformations/orders.py

from pyspark.sql import functions as F

def clean_orders(df):
    """Limpia y normaliza los pedidos recibidos."""
    return (
        df
        .filter(F.col("order_id").isNotNull())
        .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
    )
```

Pipeline:

```python
from pyspark import pipelines as dp
from transformations.orders import clean_orders

@dp.table(
    name="orders_silver",
    comment="Pedidos limpios y normalizados."
)
def orders_silver():
    return clean_orders(
        spark.readStream.table("orders_bronze")
    )
```

Esto permite probar `clean_orders()` sin ejecutar un pipeline completo.

---

## 7. Convert data-quality logic deliberately

Clasificar cada validación existente:

```text
WARN
→ registrar violación pero conservar registro

DROP
→ registro inválido no debe llegar al target

FAIL
→ violación invalida el flujo
```

Ejemplo:

```python
from pyspark import pipelines as dp

@dp.table(
    name="orders_silver",
    comment="Pedidos validados y preparados para consumo."
)
@dp.expect("order_id_presente", "order_id IS NOT NULL")
@dp.expect_or_drop("amount_valido", "amount >= 0")
def orders_silver():
    return spark.readStream.table("orders_bronze")
```

No convertir todo `try/except` en una expectation.

Expectations validan datos.

No sustituyen:

- retry de red;
- manejo de credenciales;
- errores de código;
- recovery de checkpoint;
- errores de infraestructura.

---

## 8. Quarantine when invalid data must be retained

Cuando registros inválidos necesitan investigación o reparación:

```text
bronze
  ├── valid → silver
  └── invalid → quarantine
```

La cuarentena debe preservar al menos:

```text
registro original
regla fallida
source
ingestion timestamp
batch/flow context cuando esté disponible
```

No descartar datos silenciosamente.

---

## 9. Replace manual orchestration

Revisar patrones como:

```python
dbutils.notebook.run(...)
```

y determinar si representan dependencias de datos.

Cuando sí:

Modelar las dependencias mediante lecturas entre datasets.

No traducir simplemente una secuencia de notebooks en una secuencia idéntica de tasks.

Primero comprobar si el DAG declarativo puede resolver la dependencia automáticamente.

---

## 10. Remove side effects from dataset functions

Una función decorada por `@dp.table` o `@dp.materialized_view` debe definir un dataset.

No incluir dentro de ella:

- envío de emails;
- REST calls arbitrarias;
- escritura manual secundaria;
- creación manual de tablas;
- cambios de permisos;
- lógica de observabilidad custom;
- mutación de estado global.

Las funciones de definición pueden evaluarse múltiples veces durante planning.

---

## 11. Evaluate managed ingestion first

Si el pipeline imperativo existe sólo para copiar datos desde:

- una base de datos;
- una aplicación SaaS;
- una fuente compatible con Lakeflow Connect;

evaluar primero Lakeflow Connect.

No reconstruir en SDP una integración que ya puede resolverse mediante una capa administrada.

---

## 12. AI Functions decision gate

Cuando una transformación incluya:

- clasificación de texto;
- extracción de información;
- resumen;
- masking semántico;
- generación o enriquecimiento con un modelo;

evaluar primero Databricks AI Functions.

Ejemplos de funciones a considerar según el workload:

```text
ai_classify
ai_extract
ai_summarize
ai_mask
ai_query
```

Antes de incorporarlas en un pipeline productivo validar:

- calidad;
- costo;
- throughput;
- latencia;
- comportamiento ante NULL/error;
- privacidad;
- determinismo esperado.

No utilizar una llamada LLM por fila en un pipeline de gran volumen sin evaluar primero estos factores.

---

## 13. Unity AI Gateway decision gate

Si el pipeline llama directamente:

- modelos externos;
- model APIs;
- agentes;
- MCP servers;
- herramientas AI externas;

no almacenar credenciales del proveedor dentro del pipeline.

Evaluar enrutar esas interacciones mediante Unity AI Gateway para:

- control de acceso;
- credenciales;
- rate limits;
- budgets;
- observabilidad;
- service policies.

No activar este gate para un pipeline que sólo transforma datos.

---

## 14. Lakebase decision gate

Si al revisar el ETL se descubre que una tabla Gold está siendo utilizada como sustituto de una base operacional para:

- writes transaccionales;
- estado de una aplicación;
- sesiones;
- agent state;
- serving de baja latencia;
- CRUD operacional;

no seguir optimizando el pipeline como solución OLTP.

Escalar el diseño para evaluar Lakebase Postgres.

---

## 15. Metadata is mandatory

Toda tabla publicada para consumidores debe documentar:

```text
propósito
grain
source
freshness
owner/equipo
campos de negocio críticos
```

Ejemplo:

```sql
COMMENT ON TABLE production.silver.orders IS
  'Pedidos validados. Granularidad: una fila por pedido. Fuente: sistema de comercio electrónico.';

COMMENT ON COLUMN production.silver.orders.order_id IS
  'Identificador único del pedido en el sistema de origen.';
```

Los comentarios y documentación deben estar en español salvo solicitud explícita del usuario.

No renombrar objetos productivos sólo para traducirlos.

---

## 16. Genie-readiness handoff

Si el output alimenta consumo analítico:

Antes de cerrar identificar:

```text
¿Estas tablas serán usadas por Genie?
¿Tienen metadata suficiente?
¿Qué preguntas busca responder el consumidor?
¿Existen KPIs estables?
¿Existen Metric Views?
```

El Data Engineer no debe inventar KPIs.

Cuando existan necesidades de semántica o Genie:

hacer handoff a:

- `semantic-layer-strategy`
- `self-service-analytics-enablement`

---

## 17. Test

Realizar tres niveles cuando apliquen:

### Unit tests
Funciones PySpark puras.

### Pipeline validation
Validar código, dependencias y configuración.

### Integration/data tests
Comparar salida nueva vs pipeline anterior.

Verificar:

```text
row counts
keys
aggregates
duplicates
NULL behavior
CDC convergence
late data
schema
critical business totals
```

---

## 18. Migration strategy

No reemplazar directamente producción.

Preferir:

```text
legacy
   ↓
parallel run
   ↓
compare
   ↓
consumer validation
   ↓
cutover
   ↓
observation window
   ↓
retire legacy
```

La duración depende de criticidad y ciclo de datos.

---

## Output

Entregar:

```text
Pipeline analizado:

Arquitectura actual:
- ...

Arquitectura propuesta:
- ...

Datasets:
- source:
  target:
  type:
  incremental:
  grain:

CDC:
- ...

Expectations:
- ...

Quarantine:
- ...

Código modernizado:
- ...

Tests:
- ...

Metadata:
- ...

Handoffs:
- Genie:
- Metric Views:
- Lakebase:
- AI Gateway:

Riesgos:
- ...

Plan de cutover:
- ...
```

---

# Definition of Done

- [ ] Se inspeccionó todo el ETL relevante.
- [ ] Se reconstruyó el DAG.
- [ ] Se diferenciaron ingestion y transformation.
- [ ] Cada dataset tiene el tipo correcto.
- [ ] El código nuevo utiliza `pyspark.pipelines`.
- [ ] Se eliminaron APIs DLT legacy salvo requerimiento explícito.
- [ ] CDC utiliza AUTO CDC cuando corresponde.
- [ ] Se eliminaron writes imperativos innecesarios.
- [ ] Las transformaciones importantes son testeables.
- [ ] Las reglas de calidad tienen semántica warn/drop/fail consciente.
- [ ] Los registros que deben conservarse tienen quarantine.
- [ ] No existen side effects dentro de dataset definitions.
- [ ] Se evaluó Lakeflow Connect si existe un conector administrado.
- [ ] Se evaluaron AI Functions si existe enriquecimiento IA.
- [ ] Se evaluó Unity AI Gateway si existe tráfico AI externo.
- [ ] Se evaluó Lakebase si apareció una necesidad OLTP.
- [ ] Las tablas publicadas tienen metadata.
- [ ] Comentarios, docstrings y documentación están en español.
- [ ] Se realizó validación contra el pipeline anterior.
- [ ] Existe plan de cutover.

# Gotchas

- DLT legacy sigue funcionando, pero no debe ser el default para código nuevo.
- `@dp.table` y `@dp.materialized_view` tienen semánticas distintas.
- No transformar automáticamente cualquier batch en streaming.
- Expectations no sustituyen error handling de infraestructura.
- AUTO CDC no sustituye cualquier MERGE.
- Una migración técnicamente correcta puede cambiar grain o semántica.
- No asumir que Medallion es obligatoria para todos los DAGs.
- No mezclar código de monitoreo con dataset definitions.
- No introducir llamadas externas por fila sin evaluar costo y resiliencia.
