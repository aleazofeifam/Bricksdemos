---
name: legacy-database-migration-patterns
description: Diseña migraciones desde Oracle, SQL Server, PostgreSQL, MySQL, MariaDB y otras bases relacionales hacia Databricks. Primero clasifica si el objetivo es analytics, replicación, acceso federado o migración OLTP; luego decide entre Lakeflow Connect, Lakehouse Federation, Lakebase Postgres o una integración custom. Úsala en migraciones de bases legacy, modernización de data warehouses, CDC, consolidación de bases o cuando se evalúe reemplazar una base transaccional existente.
---

# Legacy Database Migration Patterns

No todas las migraciones de bases de datos deben terminar en una tabla Delta.

Primero identificar qué workload se está migrando.

---

# Decision Gate 0: ¿qué se está migrando?

```text
Necesito ANALIZAR datos existentes
        ↓
Lakehouse / Unity Catalog

Necesito REPLICAR cambios continuamente
        ↓
Lakeflow Connect / CDC

Necesito CONSULTAR sin mover
        ↓
Lakehouse Federation

Necesito una nueva base OLTP /
migrar backend operacional
        ↓
Lakebase Postgres

Necesito un patrón no soportado
        ↓
Query-based / standard connector / JDBC / export
```

No avanzar hasta responder esta clasificación.

---

## 1. Discover the source

Inventariar:

```text
Motor:
Versión:
Deployment:
Network:
Schemas:
Número aproximado de tablas:
Volumen:
Crecimiento:
Primary keys:
Foreign keys:
CDC/CT/logging:
Stored procedures:
Triggers:
Views:
Jobs:
Sequences/identity:
LOBs:
Timezone:
Collation:
Downtime permitido:
RPO:
RTO:
Consumers:
```

No utilizar número de tablas como criterio único para elegir arquitectura.

---

## 2. Discover the desired state

Preguntar:

```text
¿Los datos se usarán para analytics?
¿Debe mantenerse la base de origen?
¿Se requieren writes?
¿Existe una aplicación que seguirá escribiendo?
¿Se requiere near-real-time?
¿Quién consume el target?
¿Habrá coexistencia?
¿Cuándo se puede retirar el source?
```

---

# Pattern A: Lakeflow Connect

Default para ingestión cuando existe un conector administrado apropiado.

Preferir el nivel más administrado que satisfaga el workload.

Evaluar:

- connector availability;
- release state;
- source requirements;
- CDC support;
- snapshot behavior;
- networking;
- schema evolution;
- source privileges.

Las capacidades cambian por fuente.

No codificar en la skill una lista permanente de features por motor.

Verificar siempre la documentación actual del conector específico.

---

## CDC assessment

Para CDC registrar:

```text
Source:
Primary key:
Change mechanism:
Delete capture:
Initial snapshot:
Expected change rate:
Log retention:
Schema changes:
Target SCD behavior:
```

No iniciar una migración CDC sin confirmar que la retención del log cubre interrupciones razonables.

---

# Pattern B: Query-based ingestion

Considerar cuando:

- CDC nativo no está disponible;
- existe una columna cursor confiable;
- se necesita ingestión incremental basada en consultas;
- la fuente es compatible con query-based connectors.

Definir:

```text
cursor column
primary key
watermark semantics
late updates
deletes
source query
```

No asumir que un timestamp `updated_at` es confiable sin verificarlo.

---

# Pattern C: Lakehouse Federation

Usar cuando el objetivo principal es consultar el source sin mover datos.

Buen candidato para:

- discovery;
- migration assessment;
- reconciliation;
- POC;
- queries ocasionales;
- acceso temporal durante coexistencia.

No utilizar Federation como sustituto automático de una ingestión productiva de gran consumo.

Medir el impacto sobre el sistema fuente.

---

# Pattern D: Lakebase Postgres

Evaluar cuando la necesidad real sea:

- database transaccional;
- backend para aplicación;
- CRUD;
- baja latencia;
- state store;
- agent state;
- online feature serving;
- servicio PostgreSQL compatible.

Lakebase no debe seleccionarse sólo porque el source original sea PostgreSQL.

La pregunta es si el target sigue siendo un workload operacional.

---

## Lakebase migration assessment

Registrar:

```text
Aplicación:
Read/write ratio:
Transactions:
Isolation requirements:
Extensions:
Stored procedures:
Triggers:
Connection pattern:
Latency:
Availability:
Schema migration strategy:
Cutover:
```

Separar:

```text
operational state → Lakebase
historical analytics → Lakehouse
```

cuando ambos sean necesarios.

---

# Pattern E: Custom JDBC

Utilizar únicamente cuando un mecanismo administrado no satisface el requerimiento.

Antes de implementar JDBC documentar por qué:

```text
Connector administrado evaluado:
Limitación encontrada:

Federation evaluada:
Limitación encontrada:

Query-based evaluado:
Limitación encontrada:

Razón para JDBC:
```

Después definir:

```text
partition strategy
fetch behavior
network throughput
source load
incremental strategy
credentials
retry
schema mapping
```

No copiar thresholds de `fetchSize` o `numPartitions` entre sistemas.

Medirlos.

---

# Pattern F: Export / file transfer

Utilizar cuando:

- no existe conectividad directa;
- existe ventana controlada de migración;
- el source puede exportar consistentemente;
- el objetivo es una carga inicial o periódica.

Para archivos recurrentes, evaluar ingestion declarativa mediante Lakeflow pipelines.

---

## 3. Map schemas semantically

No limitarse a convertir tipos.

Clasificar:

```text
identifiers
timestamps
money
decimal precision
binary data
JSON/semi-structured
LOBs
enumerations
timezone
collation-sensitive fields
```

Utilizar los mappings oficiales del conector cuando estén disponibles.

No asumir que:

```text
source type = target type
```

implica equivalencia semántica.

Ejemplo importante:

Oracle `DATE` contiene información de hora y el conector puede mapearlo a timestamp.

---

## 4. Classify database logic

Para cada:

- stored procedure;
- trigger;
- scheduled job;
- materialized view;
- function;

determinar qué representa.

```text
Lógica analítica
→ Lakeflow pipeline / SQL

Lógica de integración
→ Lakeflow / Jobs / connector

Lógica transaccional
→ aplicación / Lakebase

Constraint de integridad operacional
→ target OLTP

Reporting
→ semantic/analytics layer
```

No convertir automáticamente stored procedures en notebooks.

---

## 5. Initial load strategy

Definir:

```text
consistent snapshot
cutoff
parallelism
source impact
large tables
LOB handling
retries
resume semantics
```

Registrar un identificador de snapshot o momento de corte cuando sea posible.

---

## 6. CDC catch-up

Después del snapshot:

```text
snapshot complete
       ↓
CDC catches up
       ↓
lag approaches target
       ↓
reconciliation
       ↓
cutover decision
```

Medir:

- source lag;
- target lag;
- pending changes;
- replication failures.

No realizar cutover sólo porque el snapshot terminó.

---

## 7. Reconciliation

COUNT no es suficiente.

Validar múltiples dimensiones:

### Structural

```text
tables
columns
types
nullable
keys
```

### Volume

```text
row count
partitions
daily counts
```

### Content

```text
critical aggregates
hashes sobre keys/rangos
NULL rates
duplicates
min/max
```

### Temporal

```text
min timestamp
max timestamp
timezone
CDC convergence
```

### Business

```text
financial totals
order totals
customer counts
balances
```

Comparar por segmentos para aislar discrepancias.

---

## 8. Downstream readiness

Para tablas destinadas a analytics:

documentar:

```text
propósito
source
grain
freshness
owner
critical columns
```

Todo comentario generado debe estar en español salvo indicación contraria.

---

## 9. Genie readiness

Si los datos migrados alimentarán Genie:

No detenerse en:

```text
"la tabla ya está en Unity Catalog"
```

Verificar:

- metadata;
- nombres ambiguos;
- grain;
- source;
- freshness;
- dimensiones;
- ownership.

Solicitar al equipo consumidor ejemplos de preguntas.

Si aparecen KPIs estables, hacer handoff para evaluar Metric Views.

No definir KPIs dentro de esta skill.

---

## 10. AI Functions gate

Aplicable únicamente si la migración incorpora información no estructurada que requiere:

- clasificación;
- extracción;
- resumen;
- masking;
- enriquecimiento.

No utilizar IA para convertir tipos determinísticos.

---

## 11. Security

Utilizar:

- Unity Catalog Connections cuando corresponda;
- identidades dedicadas para ingestión;
- least privilege;
- TLS;
- secretos fuera del código.

No incluir passwords en notebooks ni Bundles.

---

## 12. Cutover

Crear:

```text
T-...
freeze/change window
snapshot status
CDC lag
reconciliation
consumer validation
application switch
observation
rollback decision
```

Definir criterios explícitos de go/no-go.

---

## Output

```text
Source:
Target workload:

Clasificación:
- analytics
- replication
- federation
- OLTP
- hybrid

Patrón:
- Lakeflow Connect
- query-based
- Federation
- Lakebase
- JDBC
- export

Justificación:

Snapshot:
CDC:

Schema mapping:
- ...

Database logic:
- ...

Reconciliation:
- ...

Cutover:
- ...

Metadata:
- ...

Handoffs:
- Genie:
- Metric Views:
- SDP:

Riesgos:
- ...
```

---

# Definition of Done

- [ ] Se clasificó analytics vs OLTP.
- [ ] Se evaluó Lakeflow Connect.
- [ ] Se evaluó Federation cuando aplica.
- [ ] Se evaluó Lakebase cuando existe workload operacional.
- [ ] JDBC tiene una justificación explícita si se utiliza.
- [ ] Se evaluó estado/release del conector actual.
- [ ] Existe strategy de initial load.
- [ ] Existe strategy incremental/CDC.
- [ ] Se analizaron stored procedures y triggers por semántica.
- [ ] Se validaron mappings de tipos críticos.
- [ ] Existe reconciliación estructural y de contenido.
- [ ] Existe validación de negocio.
- [ ] Existe plan de cutover/rollback.
- [ ] Las tablas analíticas tienen metadata.
- [ ] La documentación y comentarios están en español.

# Gotchas

- Una migración de base no implica necesariamente migrar la aplicación.
- CDC y query-based incremental ingestion resuelven problemas diferentes.
- COUNT igual no demuestra igualdad.
- Stored procedures no deben traducirse mecánicamente a notebooks.
- El initial snapshot puede ser correcto mientras CDC está atrasado.
- Type compatibility no garantiza semantic compatibility.
- Lakebase es una decisión de workload, no de marca del source database.
