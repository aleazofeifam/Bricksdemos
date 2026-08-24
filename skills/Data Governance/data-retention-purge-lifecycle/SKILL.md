---
name: data-retention-purge-lifecycle
description: Diseña y ejecuta lifecycle de retención, archivado y eliminación para datos y logs gobernados, distinguiendo política legal/empresarial de mecanismos técnicos Delta, upstream sources, AI logs y sistemas operacionales. Úsala para retention policies, right-to-erasure workflows, legal hold, data minimization, archival, storage lifecycle o eliminación física verificable.
---

# Data Retention & Purge Lifecycle

Retention es una decisión de política.

Purge es una implementación técnica.

Nunca inventar la primera a partir de la segunda.

---

# Core workflow

**Inventory → Policy → Dependencies → Protect/Hold → Delete/Archive → Physically Purge → Verify → Evidence**

---

# 1. Identify policy authority

Antes de eliminar registrar:

```text
Policy:
Legal/regulatory source:
Business owner:
Privacy/Legal approval if required:
Data category:
Jurisdiction:
Retention period:
Trigger:
Exceptions:
Legal hold:
```

No utilizar períodos universales.

---

# 2. Classify the requirement

```text
RETENTION
→ keep for defined period

MINIMIZATION
→ don't keep unnecessary data

ARCHIVE
→ preserve outside active workload

ERASURE
→ remove specified subject/data

LEGAL HOLD
→ suspend deletion

TECHNICAL CLEANUP
→ storage optimization
```

No confundir storage cleanup con compliance erasure.

---

# 3. Inventory every copy

Buscar:

```text
source systems
bronze
silver
gold
views/materializations
feature tables
training datasets
exports
volumes
Delta history
backups/archive
Lakebase
inference tables
MLflow traces/artifacts
other systems
```

No ejecutar erasure únicamente sobre Gold.

---

# 4. Lineage

Utilizar lineage para identificar downstream copies.

Complementar con:

```text
external systems
manual exports
shares
archives
application databases
```

Lineage no garantiza inventario absoluto de todo lo que salió de la plataforma.

---

# 5. Data subject identifier

Para subject erasure definir exactamente:

```text
canonical ID
alternate IDs
email/phone mappings
account IDs
cross-system mapping
```

No buscar únicamente por email si existen múltiples identifiers.

---

# 6. Legal hold gate

Antes de borrar verificar:

```text
legal hold?
investigation hold?
regulatory retention?
litigation?
financial record requirement?
```

Si existe conflicto:

escalar a Legal/Compliance.

No resolverlo automáticamente.

---

# 7. Logical deletion

Para Delta:

ejecutar únicamente después de delimitar scope.

Ejemplo conceptual:

```sql
DELETE FROM production.commerce.customers
WHERE customer_id = :customer_id;
```

Utilizar parámetros.

No insertar identificadores sensibles directamente en logs o comentarios.

---

# 8. Understand deletion vectors

Cuando deletion vectors u otras metadata-only deletes aplican:

el DELETE lógico puede no reescribir inmediatamente el archivo físico.

Para physical purge puede requerirse:

```text
DELETE
    ↓
REORG TABLE ... APPLY (PURGE)
    ↓
VACUUM
```

---

# 9. REORG APPLY PURGE

`REORG TABLE ... APPLY (PURGE)`:

```text
rewrites current data files
to apply soft deletes
```

Pero archivos históricos anteriores todavía pueden contener los datos.

No afirmar que REORG por sí solo completa physical erasure.

---

# 10. VACUUM

`VACUUM` elimina archivos que:

```text
are no longer referenced
+
meet retention eligibility
```

Antes de modificar retention revisar:

```text
long-running readers
streaming
Time Travel requirements
rollback requirements
concurrency
legal retention
```

No recomendar `VACUUM RETAIN 0 HOURS` como workflow estándar.

---

# 11. Managed vs external assets

Para managed tables:

Unity Catalog controla mayor parte del data-file lifecycle.

Para external tables:

storage lifecycle también depende del sistema/cloud owner.

No asumir que:

```text
DROP TABLE
```

borra physical data de una external table.

---

# 12. Archive decision

Archivar únicamente cuando policy exige conservar.

Opciones dependen de:

```text
queryability
cost
immutability
retention
security
future restoration
```

No utilizar DEEP CLONE como política universal de archival.

Puede crear otra copia que también deba gobernarse y eventualmente borrarse.

---

# 13. Archive governance

Todo archive necesita:

```text
owner
classification
retention
access
encryption
location
destruction date/condition
```

"No está en production" no significa "no está regulado".

---

# 14. Upstream deletion

Para privacy erasure revisar fuentes:

```text
Kafka
operational DB
files
SaaS
Lakebase
landing zone
```

Si se borra sólo en Databricks y el pipeline vuelve a ingerir desde source, el dato puede reaparecer.

---

# 15. Pipeline behavior

Antes de borrar comprobar:

```text
Will pipeline recreate the row?
Will CDC send it again?
Does source emit deletes?
Will a full refresh restore it?
```

El deletion workflow debe sobrevivir futuros refresh/backfills.

---

# 16. SDP implications

Si un dataset lo administra Spark Declarative Pipelines:

coordinar deletion/backfill con Data Engineer.

No mutar arbitrariamente una target table administrada por pipeline sin entender el siguiente refresh.

---

# 17. Lakebase gate

Si datos regulados están en Lakebase:

definir deletion mediante semántica PostgreSQL/aplicación correspondiente.

No asumir que:

```text
REORG/VACUUM
```

aplica a Lakebase.

Crear una única evidence chain para todos los stores involucrados.

---

# 18. AI Gateway inference tables

Si AI requests/responses contienen el subject data:

incluir inference tables en el inventario.

Estas tablas pueden contener:

```text
prompt
response
requester
request tags
destination
```

y requieren su propia retention policy.

---

# 19. MLflow and agent traces

Si GenAI traces almacenan contenido sensible:

evaluar también:

```text
MLflow traces
evaluation datasets
training datasets
artifacts
feedback
```

Erasure puede requerir revisar esos activos.

---

# 20. Model-training implications

Si información eliminada fue utilizada para entrenar un modelo:

no afirmar automáticamente que eliminar el training row equivale a eliminar su influencia del modelo.

Escalar a:

```text
Privacy
Legal
ML governance
```

según requirement.

---

# 21. Evidence

Para una deletion operation registrar:

```text
request/reference
scope
systems checked
objects modified
operations
timestamps
validation
operator
exceptions
```

Evitar almacenar en el evidence log más PII de la necesaria.

---

# 22. Verification

Verificar:

```text
active tables
historical availability where applicable
upstream source
archive
AI logs
operational store
reingestion behavior
```

No marcar completed sólo porque `DELETE` devolvió éxito.

---

# 23. Retention automation

Automatizar únicamente policies aprobadas.

Configurar:

```text
scope
schedule
owner
dry-run/report
failure handling
legal-hold exclusions
evidence
```

No hardcodear días en múltiples jobs.

Centralizar policy metadata cuando sea viable.

---

# Output

```text
Requirement:
- retention
- erasure
- archive
- legal hold

Authority:
- ...

Data subject/category:
- ...

Inventory:
- source:
- Delta:
- archives:
- Lakebase:
- AI logs:
- ML artifacts:

Policy:
- ...

Operations:
- ...

Physical purge:
- ...

Verification:
- ...

Exceptions:
- ...

Evidence:
- ...
```

# Definition of Done

- [ ] Policy authority está identificada.
- [ ] Retention no fue inventada por la skill.
- [ ] Legal hold fue revisado.
- [ ] Se identificaron todos los stores razonables.
- [ ] Upstream sources fueron revisados.
- [ ] Lineage fue utilizado.
- [ ] Managed/external lifecycle está entendido.
- [ ] REORG y VACUUM se utilizaron con semántica correcta cuando aplican.
- [ ] Pipeline reingestion fue revisado.
- [ ] Lakebase fue considerado cuando aplica.
- [ ] AI Gateway inference tables fueron consideradas.
- [ ] ML/agent artifacts fueron considerados cuando aplica.
- [ ] Erasure fue verificada.
- [ ] Evidence minimiza PII.
- [ ] Documentación está en español.

# Gotchas

- DELETE lógico no siempre implica physical erasure inmediato.
- REORG APPLY PURGE no elimina por sí solo todos los old files.
- VACUUM puede destruir Time Travel.
- DROP de external table no necesariamente borra storage.
- Archive crea otra copia gobernable.
- Full refresh puede volver a introducir datos borrados.
- Borrar training data no equivale automáticamente a "untraining" de un modelo.

La documentación oficial de Databricks confirma explícitamente el orden REORG TABLE ... APPLY (PURGE) y luego VACUUM cuando se necesita eliminar físicamente información registrada mediante soft deletes/deletion vectors.
