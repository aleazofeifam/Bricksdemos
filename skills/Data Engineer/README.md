# Data Engineer Skills

## Propósito

Esta carpeta contiene las skills de la persona **Data Engineer**. El objetivo es diseñar, modernizar y operar pipelines de datos confiables utilizando primero las capacidades administradas de Databricks cuando son apropiadas.

El sistema no busca simplemente generar PySpark. El Data Engineer debe decidir **cómo ingestar, transformar, validar, promover, recuperar y observar** datos, manteniendo contratos claros con consumidores downstream.

## Lifecycle

```text
Fuente
  ↓
Clasificar workload
  ├── Query in-place → Lakehouse Federation
  ├── Ingestión administrada → Lakeflow Connect
  ├── OLTP / aplicación → Lakebase
  └── Transformación de datos → Lakeflow pipelines / SDP
                                  ↓
                         Spark Declarative Pipelines
                                  ↓
                    Calidad / contratos / resiliencia
                                  ↓
                       Testing / CI-CD / promotion
                                  ↓
                       Observabilidad / SLAs
                                  ↓
                    Curated consumer-ready data
                                  ↓
                 Data Analyst / Data Scientist / AI
```

## Estado final del sistema

El bloque de Data Engineer contiene nueve skills:

| Skill | Para qué sirve | Cuándo usarla |
|---|---|---|
| `etl-to-sdp-refactor` | Moderniza ETL imperativo y DLT legacy hacia Spark Declarative Pipelines | Cuando existen notebooks, `spark.read/write`, DLT antiguo o pipelines difíciles de mantener |
| `legacy-database-migration-patterns` | Decide entre Lakeflow Connect, Federation, Lakebase o integración custom | Cuando se migra Oracle, SQL Server, PostgreSQL, MySQL u otra base |
| `data-quality-contract-producer` | Convierte expectativas productor-consumidor en contratos verificables | Al publicar datasets críticos o gestionar breaking changes |
| `backfill-reprocessing-patterns` | Ejecuta backfills/replays con idempotencia y reconciliación | Después de bugs, gaps históricos o correcciones de lógica |
| `pipeline-error-handling-retry` | Diseña resiliencia según tipo de fallo | Cuando existen errores intermitentes, quarantine, retry o side effects |
| `environment-promotion-workflow` | Promueve proyectos dev → staging → prod mediante Declarative Automation Bundles | Para CI/CD reproducible y rollback gobernado |
| `file-format-conversion-optimization` | Moderniza archivos legacy y decide one-time vs recurring ingestion | Para CSV/JSON/Parquet/Iceberg y data lakes legacy |
| `pipeline-observability-sla` | Define SLIs/SLOs y observabilidad end-to-end | Cuando importa freshness, lag, backlog, quality o consumer impact |
| `multi-tenant-data-isolation` | Diseña aislamiento de datos por tenant usando UC/ABAC y gates operacionales | Para SaaS, BUs, regiones o múltiples clientes |

## Cómo funciona el sistema

### Routing inicial

```text
¿El source ya existe fuera de Databricks?
        ↓
legacy-database-migration-patterns
        ↓
¿Sólo quiero consultar sin mover?
        ├── Sí → Federation
        ↓ No
¿Existe Lakeflow Connect?
        ├── Sí → managed ingestion
        ↓ No
¿Es un backend transaccional?
        ├── Sí → Lakebase
        ↓ No
Custom ingestion / SDP
```

### Routing de transformación

```text
ETL imperativo / DLT legacy
        ↓
etl-to-sdp-refactor
        ↓
data-quality-contract-producer
        ↓
pipeline-error-handling-retry
        ↓
pipeline-observability-sla
        ↓
environment-promotion-workflow
```

## Principios globales

1. **Preferir capacidades administradas antes de código custom.**
2. **Spark Declarative Pipelines es el default para nuevas transformaciones productivas cuando el patrón es compatible.**
3. **Código nuevo usa `from pyspark import pipelines as dp`; no generar DLT legacy por defecto.**
4. **Lakeflow Connect se evalúa antes de JDBC custom para ingestión soportada.**
5. **Federation sirve para consulta in-place; no sustituye automáticamente ingestión productiva.**
6. **Lakebase se evalúa cuando aparece un workload OLTP, transaccional o de baja latencia.**
7. **AI Functions se evalúan antes de integrar llamadas LLM custom para clasificación, extracción o enriquecimiento.**
8. **Unity AI Gateway se evalúa si un pipeline genera tráfico hacia modelos, agentes, MCPs o tools.**
9. **Quality, retry, backfill y observability son problemas distintos.**
10. **Todo código, comentarios, docstrings y documentación generados deben estar en español.**

## Ejemplos de uso

### Ejemplo 1 — Modernizar un notebook ETL

**Situación**

Existe un notebook con:

```text
spark.read
transformaciones
MERGE
spark.write
dbutils.notebook.run
```

**Skill principal**

```text
etl-to-sdp-refactor
```

**Prompt sugerido**

```text
Analiza este ETL completo y modernízalo a Spark Declarative Pipelines.

Primero reconstruye el DAG lógico y clasifica cada target como streaming table,
materialized view o dataset temporal.

Usa pyspark.pipelines para código nuevo.
No traduzcas MERGE a AUTO CDC hasta confirmar que realmente representa CDC.
Separa funciones PySpark puras de decorators para facilitar testing.
```

---

### Ejemplo 2 — Migrar Oracle

**Situación**

Se quiere mover una aplicación y sus datos desde Oracle.

**Skill**

```text
legacy-database-migration-patterns
```

**Prompt sugerido**

```text
Antes de proponer una migración, clasifica el workload:

- analytics;
- replicación CDC;
- consulta federada;
- OLTP/aplicación.

Evalúa Lakeflow Connect, Lakehouse Federation y Lakebase
antes de proponer JDBC custom.

Luego diseña snapshot, CDC, reconciliación, cutover y rollback.
```

---

### Ejemplo 3 — Pipeline falla por datos inválidos

**Skills**

```text
pipeline-error-handling-retry
        +
data-quality-contract-producer
```

**Prompt sugerido**

```text
Clasifica estos fallos entre:
data error, code error, transient platform error, source unavailable,
rate limit y checkpoint problem.

Para errores de datos, diseña expectations y quarantine.
No utilices retry para errores determinísticos.
No descartes registros silenciosamente.
```

---

### Ejemplo 4 — Corregir tres meses históricos

**Skill**

```text
backfill-reprocessing-patterns
```

**Prompt sugerido**

```text
Necesito corregir tres meses de datos históricos.

Antes de ejecutar:
- identifica el rango exacto;
- confirma que el source todavía conserva los datos;
- registra estado previo;
- analiza downstream;
- prueba idempotencia.

Selecciona la operación mínima necesaria y termina con reconciliación.
No modifiques manualmente archivos de checkpoints.
```

## Handoffs a otras personas

| Señal | Handoff |
|---|---|
| Aparece un KPI o semántica empresarial reusable | Data Analyst |
| Se necesita Genie Agent / dashboard / Metric View | Data Analyst |
| Se necesita entrenamiento, forecasting o model serving | Data Scientist |
| Se necesita classification, ABAC, retention, ownership o compliance | Data Governance |

## Cargar estas skills dentro de Databricks

> **PLACEHOLDER — reemplazar esta sección con el procedimiento validado para su workspace.**

Esta sección debe mostrar cómo cargar la carpeta `Data Engineer` en el entorno de Agent Skills de Databricks y confirmar que las nueve skills quedan disponibles para routing.

### Flujo que debería mostrar el GIF

1. Abrir el entorno de Databricks donde se administran/importan skills.
2. Agregar la carpeta `Data Engineer`.
3. Confirmar que Databricks detecta cada `SKILL.md`.
4. Mostrar la lista de skills disponibles.
5. Abrir `etl-to-sdp-refactor`.
6. Ejecutar un prompt que provoque el routing hacia esa skill.

### Placeholder para el GIF

```markdown
![Cómo cargar las skills de Data Engineer en Databricks](./assets/load-data-engineer-skills-databricks.gif)
```

> Reemplazar la ruta por el GIF final.

### Prueba mínima sugerida

```text
Tengo un notebook PySpark con spark.read, MERGE y spark.write
y quiero modernizarlo a la arquitectura recomendada de Databricks.
```

La skill principal esperada es:

```text
etl-to-sdp-refactor
```

## Qué NO debe hacer esta persona

- Inventar KPIs o definiciones financieras.
- Convertir cada workload externo en JDBC custom.
- Utilizar DLT legacy para código nuevo sin necesidad.
- Hacer retry de errores determinísticos.
- Manipular checkpoints manualmente.
- Usar Lakehouse como si fuera una base OLTP.
- Introducir AI Gateway en pipelines que no generan tráfico AI.
- Publicar tablas sin metadata básica.

## Resultado esperado

Una ejecución correcta produce:

```text
source correcto
+
arquitectura adecuada
+
ingestión/transformación declarativa
+
quality contract
+
resiliencia
+
CI/CD
+
observabilidad
+
datos listos para consumidores
```
