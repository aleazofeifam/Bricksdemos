---
name: uc-permissions-audit-compliance
description: Audita el modelo de acceso y privilegios de Unity Catalog para detectar sobreprivilegio real, direct grants innecesarios, ownership riesgoso, principals obsoletos, exposición de datos sensibles y configuraciones inconsistentes en datos y AI assets. Úsala para access reviews, least-privilege assessments, auditorías, recertificación, incidentes de seguridad o revisión de modelos de acceso existentes.
---

# Unity Catalog Permissions Audit & Compliance

Una auditoría de acceso debe responder:

```text
¿Quién puede hacer qué?
¿Por qué?
¿Sobre qué?
¿Cómo obtuvo ese acceso?
¿Sigue siendo necesario?
```

No determinar sobreprivilegio simplemente contando grants.

---

# 1. Define audit scope

Registrar:

```text
Accounts/workspaces:
Metastore:
Catalogs:
Schemas:
Data classification:
Regulatory scope:
AI services:
Review period:
```

Definir primero qué riesgo se evalúa.

---

# 2. Inventory principals

Clasificar:

```text
users
account groups
service principals
admins
```

Identificar:

```text
inactive identities
individual production grants
workspace-local groups
powerful groups
```

No asumir que un principal desconocido es huérfano hasta validar con identity management.

---

# 3. Review admin roles

Auditar:

```text
account admins
workspace admins
metastore admins
billing admins
```

Preguntar:

```text
¿Necesita realmente este principal ese rol?
```

Administración excesiva tiene mayor impacto que muchos SELECTs.

---

# 4. Review ownership

Buscar production objects owned por:

```text
individual user
inactive account
unexpected service principal
```

Preferir groups para ownership de production.

Revisar particularmente:

```text
catalogs
schemas
views
Metric Views
models
functions
connections
AI services
```

---

# 5. Review MANAGE

`MANAGE` es poderoso.

Puede permitir:

```text
manage privileges
transfer ownership
rename/drop depending on object
self-grant additional privileges
```

Auditarlo independientemente de `SELECT`.

No tratar `MANAGE` como un simple admin metadata privilege.

---

# 6. Review ALL PRIVILEGES

Identificar usos de:

```text
ALL PRIVILEGES
```

y determinar si existe una razón.

No asumir automáticamente que es una violación.

Buscar alternativas de least privilege.

---

# 7. Review direct user grants

Priorizar:

```text
production
sensitive
critical
```

Detectar privilegios otorgados directamente a personas cuando deberían provenir de account groups.

Direct grants:

```text
pueden ser válidos como excepción
```

pero deben tener justificación/lifecycle.

---

# 8. Privilege inheritance

Comprender jerarquía:

```text
catalog
  ↓
schema
  ↓
objects
```

Un grant en schema/catalog puede aplicar a objetos actuales y futuros.

Auditar tanto:

```text
direct grants
inherited grants
```

No mirar sólo `table_privileges`.

---

# 9. SHOW GRANTS vs information_schema

Para una auditoría completa:

usar mecanismos que puedan ver todos los grants con privilegios suficientes.

Recordar que existen limitaciones contextuales en lo que `INFORMATION_SCHEMA` muestra según el principal que ejecuta la consulta.

No declarar auditoría completa si el auditor no puede observar todo el scope.

---

# 10. BROWSE

Revisar BROWSE separadamente.

`BROWSE` permite discovery metadata pero no reading data.

No marcarlo como equivalente a `SELECT`.

---

# 11. Access requests

Auditar:

```text
RFA enabled
destinations configured
owners reachable
external workflows working
approval evidence
```

Un modelo self-service necesita una ruta válida para solicitar acceso.

---

# 12. Workspace bindings

Para assets que necesitan isolation por workspace:

revisar workspace bindings de:

```text
catalogs
external locations
storage credentials
```

No asumir que UC grants son la única boundary.

---

# 13. Sensitive-data access

Combinar:

```text
Data Classification
+
governed tags
+
privileges
+
ABAC
```

para responder:

```text
¿quién puede consultar datos PII?
¿quién los ve sin masking?
```

No inferir sensibilidad sólo del nombre de la tabla.

---

# 14. ABAC audit

Revisar:

```text
policy scope
governed tag taxonomy
tag assignment permissions
mask UDFs
row filter UDFs
policy conflicts
exceptions
```

Security puede fallar no sólo por grants incorrectos, sino por tags incorrectos.

---

# 15. Tag governance audit

Auditar quién tiene:

```text
ASSIGN
APPLY TAG
MANAGE on governed tags
```

si esos tags determinan security.

Tag change puede cambiar effective policy.

---

# 16. Usage evidence

Correlacionar permisos con uso cuando sea útil.

Ejemplo conceptual:

```text
has privilege
+
no legitimate usage over relevant review period
→ candidate for review
```

No revocar automáticamente por inactivity sin revisar:

```text
seasonal workload
incident access
disaster recovery
rare compliance task
```

---

# 17. Audit logs

Utilizar `system.access.audit` para investigar:

```text
grant/revoke activity
access requests
policy changes
tag operations
security-relevant actions
AI service operations
```

Seleccionar `action_name` basándose en la audit-log reference actual.

No hardcodear una lista incompleta como regla eterna.

---

# 18. Behavioral anomalies

No asumir:

```text
night access = suspicious
```

Definir anomaly según contexto:

```text
unexpected principal
unexpected object
unexpected action
unexpected geography/network
unexpected volume
unauthorized escalation
```

Un job nocturno puede ser normal.

---

# 19. Genie

Para Genie revisar:

```text
agent permissions
underlying data permissions
warehouse access model
sensitive tables
access request behavior
```

No usar Genie configuration como mecanismo de autorización.

Unity Catalog sigue siendo source of truth.

---

# 20. Unity AI Gateway audit

Extender auditoría a:

```text
model services
model provider services
MCP services
functions/tools
HTTP connections
agents
```

Revisar:

```text
EXECUTE
MANAGE
owners
service policies
allowed MCP tools
credentials/connection ownership
rate limits
budgets
```

AI access es ahora parte de access governance.

---

# 21. MCP security audit

Para cada MCP Service:

```text
Who has EXECUTE?
Which tools are exposed?
Are destructive tools allowed?
Are service policies present?
What identity is propagated?
Which external system is reached?
```

No considerar:

```text
"puede ejecutar MCP service"
```

suficientemente granular si el servidor expone múltiples herramientas.

---

# 22. AI service policies

Revisar cuando correspondan:

```text
PII policy
prompt-injection policy
unsafe-content policy
custom allow/deny
approval-required actions
```

Service policy complementa privileges.

No reemplaza object access.

---

# 23. Remediation

Clasificar findings:

```text
CRITICAL
- immediate unauthorized exposure

HIGH
- powerful access without valid justification

MEDIUM
- governance weakness

LOW
- hygiene/improvement
```

No utilizar el número de grants para severity.

---

# 24. Evidence

Guardar:

```text
scope
timestamp
principal
object
privilege
reason
usage evidence
decision
reviewer
remediation
```

Distinguir:

```text
observed fact
```

de:

```text
auditor interpretation
```

---

# Output

```text
Audit scope:

Identity findings:
- ...

Ownership:
- ...

Powerful privileges:
- ...

Direct grants:
- ...

Sensitive access:
- ...

ABAC:
- ...

RFA:
- ...

Workspace isolation:
- ...

AI Gateway:
- ...

MCP:
- ...

Findings:
P0:
P1:
P2:

Evidence limitations:
- ...
```

# Definition of Done

- [ ] Audit scope está definido.
- [ ] Principals fueron inventariados.
- [ ] Admin roles fueron revisados.
- [ ] Ownership fue revisado.
- [ ] MANAGE fue revisado.
- [ ] ALL PRIVILEGES fue revisado.
- [ ] Direct grants fueron revisados.
- [ ] Inheritance está considerada.
- [ ] Auditor conoce las limitaciones de visibility.
- [ ] Sensitive access fue cruzado con classification.
- [ ] ABAC fue revisado.
- [ ] Governed tag permissions fueron revisados.
- [ ] RFA fue revisado.
- [ ] Workspace bindings fueron revisados cuando aplican.
- [ ] Genie data access fue revisado.
- [ ] AI Gateway/MCP access fue revisado.
- [ ] Findings tienen evidencia y severidad basada en impacto.
- [ ] Informe está documentado en español.

# Gotchas

- Muchos grants no equivalen automáticamente a overprivilege.
- Acceso nocturno no equivale automáticamente a anomalía.
- MANAGE no debe confundirse con SELECT.
- INFORMATION_SCHEMA puede no representar todo lo que el auditor espera ver según sus permisos.
- Tags pueden cambiar effective ABAC policies.
- Genie instructions no son access control.
- AI tools y MCPs también son parte de la superficie de permisos.

Unity Catalog recomienda explícitamente grupos, least privilege, group ownership, BROWSE para discovery y access requests para self-service.
