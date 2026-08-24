---
name: multi-tenant-data-isolation
description: Diseña aislamiento multi-tenant para datos analíticos y operacionales en Databricks utilizando boundaries de Unity Catalog, permisos, ABAC, row filters, column masks y, cuando el workload lo requiere, Lakebase Postgres. Úsala para plataformas SaaS, múltiples clientes, business units, regiones o dominios que comparten infraestructura pero requieren aislamiento y políticas de acceso diferentes.
---

# Multi-Tenant Data Isolation

Multi-tenancy no es una elección entre:

```text
catalog
schema
row filter
```

Es una decisión de threat model, ownership, scale operacional y workload.

---

# Step 1: Define the tenant

Identificar:

```text
Tenant:
- customer
- company
- business unit
- region
- legal entity
- environment
```

No diseñar hasta que "tenant" tenga significado preciso.

---

# Step 2: Define isolation requirements

Registrar:

```text
Data isolation:
Identity isolation:
Compute isolation:
Network isolation:
Storage isolation:
Encryption requirements:
Regulatory boundary:
Administrative boundary:
Cross-tenant analytics:
Operational writes:
```

---

# Step 3: Threat model

Responder:

```text
¿Quién podría intentar acceder a otro tenant?
¿Qué identidad ejecuta pipelines?
¿Qué identities administran datos?
¿Administradores pueden ver cross-tenant?
¿Debe existir cross-tenant reporting?
¿Qué ocurre si falta un tag?
```

Diseñar para fail-safe behavior.

---

# Architectural patterns

## Pattern A: Catalog boundary

Considerar cuando se necesita:

- fuerte boundary administrativa;
- lifecycle independiente;
- workspace bindings;
- ownership claramente separado;
- regulaciones o contracts que requieran boundaries mayores.

No elegirlo únicamente porque "es más seguro".

Tiene costo de administración.

---

## Pattern B: Schema boundary

Considerar cuando:

- tenants comparten catalog governance;
- necesitan objetos separados;
- lifecycle/ownership puede separarse a nivel schema.

No utilizar schema-per-tenant automáticamente para cualquier SaaS.

---

## Pattern C: Shared tables + tenant key

Considerar cuando:

- modelo es homogéneo;
- cross-tenant analytics es importante;
- gestión centralizada es deseable;
- aislamiento puede aplicarse mediante políticas.

Requisito básico:

```text
tenant_id confiable
```

No aceptar tenant IDs derivados del input del usuario sin control.

---

# Step 4: Access control

Base access primero:

```text
GRANT / REVOKE
```

Después aplicar fine-grained restrictions.

Recordar:

ABAC/row filters no conceden SELECT por sí mismos.

---

# Step 5: Prefer ABAC for broad reusable policy

Cuando muchas tablas deben implementar la misma política:

preferir:

```text
governed tags
      +
ABAC policy
```

sobre repetir:

```text
ALTER TABLE ... SET ROW FILTER
```

en cientos de objetos.

---

## Conceptual ABAC model

```text
Governed tag:
tenant_controlled

Governed tag:
tenant_id_column

Policy:
si el objeto está tenant-controlled
aplicar row policy usando su tenant column
```

Mantener policy UDF lo más simple posible.

---

# Step 6: Table-level row filters

Utilizar cuando:

- la política es específica de una tabla;
- ABAC no está adoptado;
- el caso requiere custom behavior local.

Ejemplo conceptual:

```sql
CREATE FUNCTION production.security.can_access_tenant(
    row_tenant STRING
)
RETURNS BOOLEAN
RETURN
    is_account_group_member(CONCAT('tenant_', row_tenant))
    OR is_account_group_member('platform_admins');
```

Después:

```sql
ALTER TABLE production.shared.transactions
SET ROW FILTER production.security.can_access_tenant
ON (tenant_id);
```

No convertir este patrón en default universal.

---

# Step 7: Column security

Si un tenant puede ver una fila pero no todas sus columnas:

evaluar:

- column masks;
- ABAC column-mask policies;
- curated dynamic views.

Ejemplos:

```text
PII
bank account
email
internal margin
cross-tenant identifiers
```

---

# Step 8: Governing tags

Definir taxonomy antes de políticas.

Ejemplo:

```text
classification = pii
tenant_scope = isolated
domain = commerce
```

No permitir tags libres con nombres inconsistentes cuando las policies dependen de ellos.

---

# Step 9: Service principals

Pipelines productivos no deben usar usuarios finales.

Definir:

```text
shared platform SP
tenant-specific SP
domain SP
```

según threat model.

No crear un SP por tenant automáticamente.

---

# Step 10: Test with non-admin identities

Nunca validar aislamiento sólo con un admin.

Crear matriz de pruebas:

```text
user tenant A
user tenant B
cross-tenant analyst
pipeline SP
admin
```

Validar para cada uno:

```text
allowed rows
blocked rows
masked columns
denied objects
```

---

# Step 11: Negative tests

Intentar explícitamente:

```text
query another tenant
join across tenants
query via view
query through dashboard
query through Genie
use service identity
filter bypass attempt
```

Security validation debe incluir casos que deberían fallar.

---

# Step 12: Genie Agent tenant isolation

Si tenant users acceden mediante Genie:

la seguridad debe venir de Unity Catalog, no sólo de instrucciones al agente.

No utilizar:

```text
"No muestres datos de otro cliente"
```

como control de seguridad.

Probar el Genie Agent con identidades de tenant reales/test.

Preguntas de seguridad:

```text
Muéstrame todos los clientes.
¿Cuánto vendió tenant B?
Compara mi tenant contra el resto.
```

Confirmar que UC impide acceso no autorizado.

---

# Step 13: Metric Views

Cuando métricas multi-tenant sean reutilizables:

- mantener definición semántica común;
- aplicar seguridad en el data access layer;
- evitar fórmulas diferentes por tenant salvo razón empresarial.

El metric layer no debe convertirse en bypass de security.

---

# Step 14: Physical optimization

No hacer automáticamente:

```text
CLUSTER BY tenant_id
```

Sólo porque exista multi-tenancy.

Evaluar:

- workload;
- query profile;
- automatic liquid clustering;
- data distribution.

Preferir automatic optimization cuando corresponda.

---

# Step 15: Lakebase decision gate

Si multi-tenancy pertenece a una aplicación operacional con:

- transactional writes;
- sessions;
- CRUD;
- low-latency state;
- agent state;

evaluar Lakebase Postgres.

Después definir conscientemente:

```text
shared database + tenant_id
database/schema separation
separate projects/branches
```

según aislamiento requerido.

No intentar convertir Delta tables en un OLTP backend sólo porque ya existen.

---

# Step 16: Lakehouse ↔ Lakebase

En arquitectura híbrida considerar:

```text
Lakebase
operational state
      ↓
Lakehouse
analytics/audit

Lakehouse
curated data
      ↓
Lakebase
low-latency serving
```

Definir ownership de cada copia.

---

# Step 17: Unity AI Gateway gate

Si cada tenant utiliza:

- agents;
- MCP services;
- model services;
- external AI tools;

evaluar Unity AI Gateway para gobernar:

```text
who can invoke
what tools are exposed
model access
spend
rate limits
usage
```

Las policies de datos y las policies de AI traffic son capas distintas.

---

# Step 18: Metadata

Toda tabla shared debe dejar claro:

```text
tenant column
grain
classification
owner
cross-tenant restrictions
```

Comentarios en español.

No publicar security-sensitive implementation details innecesarios a consumidores sin privilegios.

---

## Output

```text
Tenant definition:

Threat model:
- ...

Isolation requirements:
- data:
- administrative:
- compute:
- regulatory:

Architecture:
- catalog:
- schema:
- shared table:

Identity model:
- ...

Policies:
- object access:
- ABAC:
- row:
- column:

Negative tests:
- ...

Genie security:
- ...

Lakebase:
- applicable/not applicable

AI Gateway:
- applicable/not applicable

Known limitations:
- ...
```

---

# Definition of Done

- [ ] Tenant está definido.
- [ ] Existe threat model.
- [ ] Se determinaron isolation requirements.
- [ ] Catalog/schema/shared decision está justificada.
- [ ] Base privileges están definidos.
- [ ] Se evaluó ABAC para policies repetibles.
- [ ] Los governed tags están definidos cuando aplica.
- [ ] Se revisaron column masks.
- [ ] Se identificaron service principals.
- [ ] Se hicieron tests con non-admin users.
- [ ] Existen negative security tests.
- [ ] Se probó Genie si tenant users lo consumen.
- [ ] Se evaluó automatic optimization.
- [ ] Se evaluó Lakebase para OLTP.
- [ ] Se evaluó AI Gateway para sistemas agénticos.
- [ ] La metadata está documentada en español.

# Gotchas

- Row-level security no concede acceso al objeto.
- Instrucciones a Genie no son un security boundary.
- Más catalogs no siempre significa mejor seguridad.
- Shared table no significa automáticamente menor seguridad.
- ABAC depende de una taxonomy de tags bien gobernada.
- Admin users no sirven para probar tenant isolation.
- Data isolation y AI-tool isolation son problemas distintos.
