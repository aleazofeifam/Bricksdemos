---
name: compliance-framework-uc-mapping
description: Mapea requisitos y controles de frameworks regulatorios o de seguridad a capacidades, configuraciones y evidencias de Databricks sin afirmar automáticamente cumplimiento. Úsala cuando Security, Risk, Legal o auditoría necesiten identificar qué controles pueden implementarse o evidenciarse con Unity Catalog, Compliance Security Profile, audit logs, ABAC, Data Classification, Unity AI Gateway u otras capacidades.
---

# Compliance Framework → Databricks Control Mapping

Esta skill NO certifica compliance.

Su función es construir un mapa:

```text
Requirement
   ↓
Control objective
   ↓
Databricks capability
   ↓
Customer configuration
   ↓
Evidence
   ↓
Gap / external control
```

---

# Core rule

Nunca concluir:

```text
"Databricks tiene X,
por tanto la empresa cumple Y."
```

En su lugar:

```text
"Esta capacidad puede contribuir a implementar o evidenciar este control.
La organización debe validar el diseño, operación y alcance con sus equipos
de Security, Risk, Privacy, Legal y/o auditoría."
```

---

# 1. Identify framework precisely

Registrar:

```text
Framework/law:
Version:
Jurisdiction:
Control/article:
Data type:
Workspace:
Region:
Cloud:
Regulated workload:
```

No tratar:

```text
GDPR
LGPD
Ley 19.628
LFPDPPP
HIPAA
SOC 2
ISO 27001
PCI DSS
```

como equivalentes.

---

# 2. Distinguish frameworks

## Certification/assurance standards

Ejemplos:

```text
SOC 2
ISO 27001
PCI DSS
HITRUST
```

## Laws/regulations

Ejemplos:

```text
GDPR
LGPD
local privacy legislation
HIPAA
```

## Internal controls

```text
data classification policy
retention policy
least privilege
AI-use policy
```

El evidence model cambia según el tipo.

---

# 3. Determine shared responsibility

Para cada control separar:

```text
Databricks responsibility
Customer responsibility
Cloud provider responsibility
Third-party responsibility
```

No atribuir a Unity Catalog controles organizacionales que requieren:

```text
training
policy
HR process
legal review
incident governance
vendor management
```

---

# 4. Check Compliance Security Profile

Antes de procesar información sujeta a un standard que requiera CSP:

verificar:

```text
Compliance Security Profile enabled?
Correct compliance standard selected?
Correct workspace?
Supported region?
Feature supported?
```

No asumir que una cuenta Databricks es automáticamente apta para cualquier regulated workload.

---

# 5. Feature eligibility

Algunas preview/Beta capabilities pueden tener restricciones bajo Compliance Security Profile.

Antes de diseñar un control sobre una feature:

revisar su support status para:

```text
standard
region
compute
release status
```

No basar un compliance control crítico en una feature no admitida para ese compliance configuration.

---

# 6. Control mapping template

Para cada requisito:

```yaml
requirement:
  framework: PCI DSS
  reference: "<control>"

control_objective:
  description: ...

databricks:
  capability:
    - Unity Catalog privileges
    - ABAC
    - audit logs

customer_configuration:
  - ...

evidence:
  - ...

external_dependencies:
  - ...

gap:
  - ...

status:
  - mapped
  - partial
  - not addressed
```

---

# 7. Identity & access controls

Capabilities a evaluar:

```text
account identities
SSO/MFA
groups
Unity Catalog privileges
MANAGE
ABAC
row filters
column masks
workspace bindings
access requests
```

Evidence puede incluir:

```text
configuration
grants
audit logs
policy definitions
group mappings
review records
```

No confundir existence of grant configuration con periodic access review.

---

# 8. Data classification controls

Evaluar:

```text
Data Classification
system governed class.* tags
Custom Classifiers
Governance Hub
```

Evidence:

```text
classification results
coverage
review history
governed-tag configuration
```

---

# 9. Data protection controls

Evaluar:

```text
ABAC
column masks
row filters
workspace bindings
Unity Catalog storage credentials
managed/external asset controls
```

No afirmar que masking satisface automáticamente una requirement de encryption, deletion o anonymization.

---

# 10. Auditability

Evaluar:

```text
system.access.audit
table/column lineage
job lineage
configuration/change logs
access request events
AI Gateway usage/audit
```

Documentar retention y limitations actuales.

No decir simplemente:

```text
"logs = compliance"
```

---

# 11. Data lineage

Lineage puede aportar evidencia de:

```text
source
transformation
downstream use
sensitive-data propagation
```

Pero lineage no demuestra:

```text
legal basis
consent
purpose limitation
```

por sí mismo.

---

# 12. Data quality

Para controles relacionados con data integrity evaluar:

```text
pipeline expectations
data contracts
Data Quality Monitoring
reconciliation
```

Quality metrics no sustituyen controles de acceso.

---

# 13. Retention and erasure

Para privacy requirements separar:

```text
logical delete
physical deletion
source deletion
downstream copies
backup/history
legal hold
evidence
```

Utilizar `data-retention-purge-lifecycle`.

No ejecutar un DELETE directamente desde esta skill.

---

# 14. GDPR/CCPA-like deletion workflows

Cuando una requirement exige erasure:

identificar todas las copias.

En Delta con deletion vectors:

la secuencia física puede requerir:

```text
DELETE
→ REORG TABLE ... APPLY (PURGE)
→ VACUUM según policy/retention
```

pero la acción exacta debe validarse contra:

```text
retention
concurrent workloads
legal hold
upstream sources
other systems
```

No afirmar que un `REORG` aislado elimina todos los rastros físicos.

---

# 15. AI governance mapping

Para AI controls evaluar Unity AI Gateway:

```text
model access
external provider access
agent access
MCP access
tool filtering
rate limits
budgets
service policies
usage
audit
inference logging
```

Unity AI Gateway extiende governance a runtime AI interactions.

---

# 16. AI service policies

Para risk controls evaluar:

```text
PII
prompt injection
unsafe content
allow/deny
approval-required actions
```

cuando las service policies actuales soporten el escenario.

No afirmar que un guardrail elimina completamente un riesgo.

---

# 17. MCP governance

Para third-party tool access mapear:

```text
MCP Service
EXECUTE
tool allowlist
service policy
HTTP connection
managed credentials
audit/usage logs
```

Esto puede aportar control y evidencia sobre qué tools puede invocar un agent.

---

# 18. AI inference logging

Inference tables pueden aportar:

```text
request/response evidence
latency
requester
destination
tags
```

Pero tienen:

```text
cost
delivery limitations
payload limits
privacy implications
```

No habilitarlas automáticamente por razones de compliance.

---

# 19. Data residency / region

Verificar:

```text
region support
data location
service availability
cross-region behavior
```

No inferir data residency únicamente por Unity Catalog.

---

# 20. LATAM privacy frameworks

Para leyes latinoamericanas:

no reutilizar automáticamente el GDPR mapping.

Crear análisis separado para:

```text
jurisdiction
current law
article
controller/processor obligations
erasure/correction
consent
transfer restrictions
retention
```

Utilizar asesoría Legal/Privacy apropiada.

---

# 21. Evidence grading

Clasificar evidencia:

```text
DIRECT
- configuration/log directly demonstrates control operation

SUPPORTING
- supports audit but requires external evidence

INDIRECT
- indicates capability, not operation
```

Ejemplo:

```text
ABAC policy exists
→ supporting/direct configuration evidence

Quarterly access review happened
→ requires process evidence outside ABAC
```

---

# 22. Gap analysis

Cada mapping debe terminar con:

```text
covered by Databricks configuration
partially covered
customer process required
third-party control required
not supported
unknown/needs verification
```

Nunca esconder gaps.

---

# 23. Evidence package

Puede incluir:

```text
configuration snapshots
SQL evidence
system-table extracts
policy definitions
lineage screenshots/data
audit events
change history
owner/approval records
```

Preservar timestamp, scope y source.

---

# Output

```text
Framework:
Version:
Control:

Control objective:

Databricks capabilities:
- ...

Required configuration:
- ...

Evidence:
- direct:
- supporting:

Customer responsibilities:
- ...

Third-party responsibilities:
- ...

Gaps:
- ...

Feature eligibility:
- ...

Assessment:
- mapped
- partial
- gap

Disclaimer:
- no compliance conclusion is made by this mapping
```

# Definition of Done

- [ ] Framework/version están identificados.
- [ ] Control exacto está identificado.
- [ ] Shared responsibility está documentada.
- [ ] Compliance Security Profile fue verificado cuando aplica.
- [ ] Feature availability/compliance support fue revisado.
- [ ] Databricks capabilities fueron mapeadas.
- [ ] Customer configuration está explícita.
- [ ] Evidence fue clasificada.
- [ ] External controls están identificados.
- [ ] AI governance fue considerada cuando aplica.
- [ ] Gaps están explícitos.
- [ ] No se declaró compliance automáticamente.
- [ ] Resultado está documentado en español.

# Gotchas

- Capability no equivale a compliance.
- Certification del proveedor no certifica automáticamente al cliente.
- Compliance Security Profile requiere configuración consciente.
- Preview/Beta availability puede depender del standard.
- GDPR y leyes LATAM no deben tratarse como intercambiables.
- Audit logs no sustituyen procesos organizacionales.
- AI governance ahora forma parte del compliance scope cuando AI procesa datos regulados.

Databricks exige el Compliance Security Profile para una lista concreta de estándares —incluidos HIPAA y PCI-DSS— y advierte explícitamente que la responsabilidad final de cumplir sigue siendo del cliente.
