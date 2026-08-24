---
name: lineage-impact-change-management
description: Realiza análisis de impacto y change management sobre datos y AI usando Unity Catalog lineage, ownership, usage, contratos y consumer inventory antes de cambios estructurales, semánticos, operacionales o de seguridad. Úsala antes de renames, drops, schema changes, cambios de grain/KPI, migraciones, deprecaciones, security-policy changes o reemplazo de datasets y modelos.
---

# Lineage-Based Impact & Change Management

Un cambio puede romper consumers aunque el schema siga siendo válido.

Por eso evaluar:

```text
STRUCTURAL
SEMANTIC
OPERATIONAL
SECURITY
BEHAVIORAL
```

---

# 1. Describe the change

Registrar:

```text
Asset:
Current state:
Proposed state:
Reason:
Owner:
Target date:
Rollback possible:
```

No analizar impacto hasta que el cambio sea concreto.

---

# 2. Classify change

## Additive structural

```text
new optional column
new table
new measure
```

## Breaking structural

```text
drop
rename
type change
nullability change
key change
```

## Semantic

```text
definition changes
grain changes
currency changes
timezone changes
KPI formula changes
status meaning changes
```

## Operational

```text
freshness
schedule
source
availability
```

## Security

```text
grant
ABAC
mask
row filter
classification
workspace binding
```

## AI behavior

```text
model service
MCP tools
service policy
agent data source
```

Semantic change puede ser más peligroso que schema change.

---

# 3. Inspect upstream lineage

Preguntar:

```text
¿de dónde viene el asset?
```

Identificar:

```text
tables
files
jobs
pipelines
notebooks
queries
```

Esto ayuda a determinar si el cambio debe hacerse upstream.

---

# 4. Inspect downstream lineage

Identificar:

```text
tables
views
materialized views
jobs
notebooks
dashboards
```

Utilizar Unity Catalog Lineage UI/system tables según el análisis requerido.

No asumir que una única query manual refleja todo el graph.

---

# 5. Column lineage

Cuando cambia una columna:

inspeccionar column-level lineage.

Preguntar:

```text
¿Qué campos downstream se derivan de esta columna?
```

No limitarse a encontrar tablas que leen el source.

---

# 6. AI/model lineage

Si el dato alimenta:

```text
model
model API
model provider workflow
agent
```

revisar lineage disponible para esos assets.

AI dependencies también pueden romperse ante cambios de data.

---

# 7. Metric Views

Revisar explícitamente:

```text
Metric Views using the asset
measures
dimensions
filters
joins
```

Un cambio de columna puede no romper SQL inmediatamente pero alterar un KPI.

Incluir semantic owner en la evaluación.

---

# 8. Genie Agents

Lineage técnico por sí solo puede no representar toda la configuración semántica de un Genie Agent.

Revisar adicionalmente:

```text
Genie Agents containing the table
agent-local metadata
sample questions
trusted queries/functions
knowledge-store expressions
benchmarks
```

Preguntar:

```text
¿el cambio altera una pregunta que hoy responde Genie?
```

---

# 9. Usage evidence

Complementar lineage con usage.

Registrar:

```text
last known use
frequency
active consumers
critical consumers
```

Pero no usar:

```text
no usage observed
```

como prueba definitiva de que el activo puede borrarse.

Podrían existir:

```text
external consumers
seasonal jobs
manual exports
shared assets
```

---

# 10. Consumer criticality

Clasificar:

```text
critical regulatory
financial close
operational
executive BI
Genie
ML
ad hoc
unknown
```

Una dependencia utilizada una vez al mes puede ser más importante que una usada 1,000 veces al día.

---

# 11. Identify owners

Para cada consumer crítico identificar:

```text
owner
steward
technical contact
semantic owner
```

No enviar notificaciones masivas sin responsable.

---

# 12. Data contracts

Verificar:

```text
schema guarantees
grain
freshness
change policy
deprecation
```

Si existe data contract, respetarlo.

Handoff:

`data-quality-contract-producer`

cuando el producer necesita actualizar contrato.

---

# 13. Compatibility strategy

Evaluar:

```text
additive change
compatibility view
dual-write
new version/table
alias
deprecation period
consumer migration
```

No hacer rename/drop cuando una compatibilidad temporal reduce significativamente el riesgo.

---

# 14. Parallel version

Para cambios semánticos grandes:

preferir:

```text
v1
  +
v2
      ↓
compare
      ↓
consumer migration
      ↓
deprecate v1
```

cuando costo/riesgo lo justifican.

---

# 15. Communication window

No imponer:

```text
7 days
30 days
```

Derivar de:

```text
data contract
consumer criticality
deployment cadence
regulation
complexity
```

---

# 16. Pre-change validation

Crear baseline:

```text
schema
row counts
critical metrics
quality
freshness
permissions
Genie benchmarks
```

No medir únicamente errors después.

---

# 17. Execute

Registrar:

```text
who
when
change ID
deployment version
data version
```

Utilizar CI/CD donde corresponda.

---

# 18. Post-change validation

Comprobar:

```text
pipelines
jobs
queries
dashboards
Metric Views
Genie benchmarks
models
access
quality
```

No considerar el cambio completo sólo porque DDL ejecutó.

---

# 19. Security policy changes

Para ABAC/mask changes:

hacer negative tests.

Ejemplos:

```text
previously authorized user
previously masked user
unauthorized user
Genie consumer
service principal
```

La ausencia de query errors no demuestra seguridad correcta.

---

# 20. AI Gateway change impact

Para cambios de:

```text
model service
MCP service
tool allowlist
service policy
connection
budget/rate limit
```

identificar agents/clients afectados.

AI change management necesita runtime dependencies además de data lineage.

---

# 21. Rollback

Definir:

```text
code rollback
schema rollback
data rollback
security rollback
semantic rollback
AI service rollback
```

No asumir que Git revert revierte data.

---

# Output

```text
Change:

Classification:
- structural
- semantic
- operational
- security
- AI

Upstream:
- ...

Downstream:
- ...

Metric Views:
- ...

Genie:
- ...

Models/AI:
- ...

Critical consumers:
- ...

Owners:
- ...

Compatibility:
- ...

Communication:
- ...

Baseline:
- ...

Validation:
- ...

Rollback:
- ...

Decision:
- safe
- conditional
- blocked
```

# Definition of Done

- [ ] Cambio está descrito.
- [ ] Tipo de cambio está clasificado.
- [ ] Upstream lineage fue revisado.
- [ ] Downstream lineage fue revisado.
- [ ] Column lineage fue revisado cuando aplica.
- [ ] Usage fue considerado.
- [ ] Consumers críticos fueron identificados.
- [ ] Owners fueron identificados.
- [ ] Data contracts fueron revisados.
- [ ] Metric Views fueron revisadas.
- [ ] Genie Agents fueron revisados cuando aplica.
- [ ] Models/AI dependencies fueron revisados.
- [ ] Compatibility strategy existe.
- [ ] Communication window está basada en riesgo.
- [ ] Existe baseline.
- [ ] Existe post-change validation.
- [ ] Existe rollback.
- [ ] Documentación está en español.

# Gotchas

- Schema-compatible no significa semantically compatible.
- No usage observed no significa unused.
- Data lineage no reemplaza consumer communication.
- Metric Views pueden amplificar un semantic change.
- Genie puede seguir ejecutando SQL válido y dar una respuesta conceptualmente diferente.
- Git rollback no revierte data.
- AI service changes también requieren impact analysis.
