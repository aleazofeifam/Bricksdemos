---
name: file-format-conversion-optimization
description: Migra datasets basados en CSV, JSON, Parquet, Iceberg y otros archivos hacia una representación gobernada y eficiente en Databricks, diferenciando cargas one-time de ingestión recurrente y utilizando optimización administrada cuando sea posible. Úsala para modernizar data lakes legacy, convertir archivos a Delta, corregir small-file problems o diseñar ingestión de archivos recurrente.
---

# File Format Conversion & Optimization

No convertir formatos sólo porque Delta sea el default.

Primero entender el objetivo de la migración.

## Workflow

**Discover → Decide → Convert/Ingest → Validate → Optimize → Document**

---

## 1. Discover

Registrar:

```text
Format:
Location:
Managed/external:
File count:
Approx volume:
Partition layout:
Compression:
Schema stability:
New files arriving:
Update frequency:
Consumers:
External engines:
Retention:
```

Preguntar especialmente:

```text
¿Es una migración one-time
o los archivos seguirán llegando?
```

---

# Decision framework

## Existing Parquet/Iceberg, one-time conversion

Evaluar:

```text
CONVERT TO DELTA
CLONE
CTAS → UC managed table
```

Elegir según:

- source continuará cambiando;
- external vs managed;
- necesidad de copiar data;
- target ownership;
- interoperability.

---

## CSV/JSON recurring ingestion

Default:

```text
Lakeflow pipeline
+ Auto Loader/read_files
+ streaming table
```

cuando exista ingestión recurrente.

No crear una sucesión de `COPY INTO` manuales si el workload es realmente un pipeline continuo.

---

## One-time CSV/JSON load

`COPY INTO`, CTAS u otro mecanismo simple puede ser suficiente.

No desplegar un pipeline permanente para una única carga pequeña sin necesidad operacional.

---

## Existing external table needed by other engines

No cambiar formato in-place sin confirmar:

```text
quién escribe
quién lee
qué protocolo espera
```

Una conversión in-place puede romper writers externos que continúen escribiendo Parquet sin protocolo Delta.

---

## 2. Prefer UC managed tables for new curated assets

Para nuevos datasets curados, preferir Unity Catalog managed tables salvo que exista un requisito real de external ownership.

Beneficios esperados incluyen:

- managed lifecycle;
- optimization;
- governance;
- easier maintenance.

No migrar una external table sólo para cumplir una regla si existe una necesidad legítima de external management.

---

## 3. Recurring file ingestion with SDP

Ejemplo:

```python
from pyspark import pipelines as dp

@dp.table(
    name="events_bronze",
    comment="Eventos ingeridos incrementalmente desde el área de landing."
)
def events_bronze():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/Volumes/production/landing/events/")
    )
```

Agregar schema strategy de forma consciente.

No depender indefinidamente de schema inference en un contrato crítico.

---

## 4. Conversion validation

Antes y después comparar:

```text
file/data count
row count
schema
partition values
NULL rates
min/max
critical aggregates
timestamps
```

Para formato semiestructurado:

revisar también:

```text
rescued/unparsed records
unexpected fields
nested structures
```

---

## 5. Optimize managed tables using managed features first

Para Unity Catalog managed tables:

verificar:

```text
Predictive Optimization
Automatic Liquid Clustering
```

antes de crear maintenance jobs manuales.

Cuando corresponda:

```sql
ALTER TABLE production.gold.orders CLUSTER BY AUTO;
```

No asumir que una tabla necesita clustering.

Automatic clustering puede decidir que no existe beneficio suficiente.

---

## 6. Do not schedule redundant maintenance

Si Predictive Optimization administra:

- `OPTIMIZE`;
- `VACUUM`;

no crear otro schedule que duplique el trabajo.

Sólo añadir mantenimiento manual cuando exista una razón verificable.

---

## 7. Manual clustering

Si automatic clustering no aplica o existe una necesidad demostrada:

elegir keys observando:

- query workload;
- filters;
- cardinality;
- data distribution.

No mantener una regla universal de "máximo cuatro" como decision framework del skill.

Seguir las restricciones actuales de la plataforma.

---

## 8. Detect small-file problems with evidence

No asumir que todo archivo debajo de un tamaño arbitrario representa un problema.

Medir:

- file count;
- average file size;
- scan behavior;
- query profile;
- write frequency.

Resolver con la capacidad administrada apropiada.

---

## 9. AI Functions gate

Format conversion es determinística.

No usar IA para convertir CSV → Delta.

AI Functions sí pueden aplicarse posteriormente si los registros contienen:

- texto libre;
- documentos;
- descripciones;
- información que necesita extracción/clasificación.

Mantener ese enriquecimiento separado de la conversión básica cuando sea posible.

---

## 10. Metadata

Después de convertir publicar:

```text
source format
source system
grain
freshness
owner
schema semantics
```

Comentarios en español.

---

## 11. Genie readiness

Si la tabla será expuesta a Genie:

No entregar sólo:

```text
col_1
col_2
value
```

Documentar campos de negocio.

Identificar con el consumidor:

- preguntas previstas;
- dimensiones;
- KPIs.

Hacer handoff a Data Analyst para Metric Views cuando corresponda.

---

## 12. Retire legacy data consciously

No borrar source files inmediatamente después de convertir.

Definir:

```text
validation period
consumer cutover
retention
rollback requirement
compliance
```

---

## Output

```text
Source:
Format:

Workload:
- one-time
- recurring

Target:
- managed/external
- Delta/other

Method:
- convert
- clone
- CTAS
- COPY INTO
- Lakeflow pipeline

Validation:
- ...

Optimization:
- predictive:
- clustering:

Metadata:
- ...

Legacy retirement:
- ...
```

---

# Definition of Done

- [ ] Se determinó one-time vs recurring.
- [ ] Se identificaron consumidores externos.
- [ ] Se eligió managed/external conscientemente.
- [ ] Se utilizó SDP para recurring ingestion cuando corresponde.
- [ ] Se validó row/schema/content.
- [ ] Se revisó Predictive Optimization.
- [ ] Se revisó automatic liquid clustering.
- [ ] No se crearon maintenance jobs redundantes.
- [ ] Metadata está publicada.
- [ ] Se evaluó Genie-readiness.
- [ ] Existe estrategia de retiro del source.
- [ ] Comentarios/documentación están en español.

# Gotchas

- `CONVERT TO DELTA` cambia la semántica del directorio para futuros writers.
- Conversion one-time e ingestion recurrente son problemas diferentes.
- `OPTIMIZE` manual puede duplicar trabajo administrado.
- Small files deben diagnosticarse, no asumirse.
- External no significa peor; depende de ownership.
- No eliminar el source antes de reconciliar consumidores.
