---
name: data-ownership-stewardship-model
description: Diseña e implementa ownership y stewardship federado para datos y AI en Unity Catalog, separando responsabilidad de negocio, administración técnica, ejecución productiva y stewardship. Úsala cuando no esté claro quién responde por un dataset, KPI, model, Genie Agent o AI service; cuando permisos dependan de individuos; o cuando se quiera escalar self-service governance sin crear un cuello de botella central.
---

# Data Ownership & Stewardship Model

Ownership responde:

```text
¿Quién tiene autoridad para tomar decisiones sobre este activo?
```

Stewardship responde:

```text
¿Quién mantiene activamente su calidad, semántica y gobernanza?
```

No son necesariamente la misma persona o grupo.

---

# Roles

## Business/Data Owner

Responsable de:

```text
business purpose
acceptable use
criticality
semantic decisions
retention requirements
access policy intent
```

No necesita administrar directamente GRANTs.

---

## Data Product Owner

Responsable del lifecycle del producto:

```text
roadmap
consumers
SLOs
breaking changes
adoption
```

---

## Data Steward

Responsable de:

```text
metadata
classification
quality follow-up
business glossary
ownership records
policy review
```

No otorgarle automáticamente `MODIFY` sobre production data.

---

## Technical Owner / Engineering Team

Responsable de:

```text
pipeline
schema implementation
availability
performance
deployment
incident response
```

---

## Semantic Owner

Para KPIs y Metric Views:

```text
metric definitions
dimensions
business rules
semantic changes
```

Puede coincidir con business owner.

---

## AI Service Owner

Para:

```text
model service
agent
MCP service
AI Gateway configuration
```

Responsable de:

```text
access
behavior policy
cost
monitoring
risk
lifecycle
```

---

## Platform Governance

Responsable de:

```text
global standards
catalog architecture
governed tags
ABAC
central policies
platform controls
```

No debe aprobar manualmente toda solicitud de datos.

---

# 1. Define governance model

Elegir conscientemente:

```text
CENTRALIZED
FEDERATED
HYBRID
```

En la mayoría de organizaciones grandes:

```text
central policy
+
domain ownership
```

es un buen punto de partida.

No imponerlo sin evaluar organización y regulación.

---

# 2. UC ownership

Para production securables:

preferir ownership por **account-level groups**.

Ejemplo:

```sql
ALTER CATALOG production OWNER TO `data-governance-admins`;

ALTER SCHEMA production.finance OWNER TO `finance-data-owners`;
```

No utilizar usuarios individuales como owners de producción salvo una razón explícita.

---

# 3. Ownership vs MANAGE

Separar:

```text
OWNER
→ control total sobre el objeto

MANAGE
→ puede administrar privileges,
   ownership y ciertas operaciones,
   pero no recibe automáticamente
   todos los privilegios de lectura/escritura
```

Utilizar `MANAGE` para delegar administración sin transferir ownership cuando sea apropiado.

No conceder `ALL PRIVILEGES` como sustituto de un modelo de ownership.

---

# 4. Service principals

Utilizar service principals para:

```text
production pipelines
jobs
automation
deployments
```

No convertirlos en business owner.

Ejemplo:

```text
finance-data-owners
→ schema ownership

finance-pipeline-sp
→ run-as / MODIFY requerido para pipeline
```

---

# 5. Group provisioning

Preferir:

```text
IdP
→ account-level groups
→ Unity Catalog privileges
```

Evitar direct grants a usuarios cuando sea posible.

No crear manualmente grupos locales de workspace como modelo principal para UC.

---

# 6. Ownership registry

Mantener para cada producto crítico:

```text
Business owner
Technical owner/team
Steward
Semantic owner
Support contact
Escalation path
```

No almacenar emails individuales como governed tags si contienen información que no debería replicarse como tag metadata.

Puede utilizarse:

```text
group identifier
team identifier
domain identifier
```

y mantener people mapping en el sistema apropiado.

---

# 7. Ownership hierarchy

No intentar asignar diferente owner a cada columna.

Preferir ownership por:

```text
domain
catalog
schema
data product
Metric View
model
AI service
```

Subdividir sólo cuando la responsabilidad realmente cambia.

---

# 8. Access decision rights

Definir quién decide:

```text
SELECT
MODIFY
CREATE
EXECUTE
MANAGE
sensitive-data access
cross-domain access
```

Ejemplo:

```text
Data owner
→ define policy intent

Governance/platform
→ implement central ABAC

Domain admin
→ manages domain-level grants

Security/compliance
→ reviews exceptional sensitive access
```

---

# 9. Self-service access requests

Utilizar Unity Catalog Request for Access cuando corresponda.

Configurar destinos:

```text
catalog owner group workflow
Slack
Teams
email
webhook
external ITSM
```

Puede integrarse con:

```text
Jira
ServiceNow
custom approval
```

mediante redirect/webhook patterns.

No implementar un workflow custom si la capacidad nativa ya satisface el proceso.

---

# 10. BROWSE

Utilizar `BROWSE` para permitir discovery sin dar acceso al contenido.

Esto habilita:

```text
Catalog Explorer
search
metadata
lineage
request access
```

Separar:

```text
know that data exists
```

de:

```text
read the data
```

---

# 11. Least privilege

Revisar:

```text
USE CATALOG
USE SCHEMA
SELECT
MODIFY
EXECUTE
CREATE*
MANAGE
```

No asignar `MODIFY` a un Data Steward sólo por su rol organizacional.

Privilege debe corresponder al trabajo real.

---

# 12. Metric View ownership

Metric Views contienen semántica empresarial.

Por ello deben tener ownership explícito.

Para collaborative editing:

considerar group ownership.

Definir:

```text
semantic owner
technical editors
business approval
```

No permitir que una definición crítica dependa de una sola cuenta personal.

---

# 13. Genie Agent ownership

Para cada Genie Agent definir:

```text
business/domain owner
technical curator
semantic owner
warehouse/compute responsibility
benchmark owner
support channel
```

Preguntar:

```text
¿Quién aprueba nuevas tablas?
¿Quién aprueba nuevos KPIs?
¿Quién revisa feedback?
```

No tratar Genie como un dashboard que se publica y se abandona.

---

# 14. AI ownership

Para Unity AI Gateway assets incluir:

```text
model services
model provider services
MCP services
functions/tools
connections
agents
```

Asignar:

```text
owner
MANAGE group
EXECUTE consumers
service-policy owner
budget owner
```

---

# 15. MCP ownership

MCP Services pueden dar acceso a sistemas externos.

Definir específicamente:

```text
service owner
connection owner
credential owner
allowed tools
who gets EXECUTE
service policies
audit reviewer
```

No considerar MCP ownership como un detalle exclusivamente de ingeniería.

---

# 16. Recertification

Revisar periódicamente:

```text
owners still valid
stewards active
groups still correct
orphaned assets
access destinations
unused privileges
AI services still needed
```

La frecuencia depende de:

```text
risk
regulation
organizational change
```

No imponer "trimestral" universalmente.

---

# 17. Orphan detection

Detectar:

```text
individual owners who left
inactive groups
unused objects
missing domain owners
AI services without owners
Metric Views without semantic owner
```

Priorizar production y sensitive assets.

---

# 18. Change ownership safely

Antes de transferir:

```text
current grants
object dependencies
views
Metric Views
pipeline run-as
functions/models
```

Recordar que ownership de streaming tables/materialized views creados mediante Lakeflow pipelines puede depender del run-as de pipeline.

---

# 19. RACI only where useful

No crear un RACI gigante para cada tabla.

Utilizar RACI para decisiones transversales como:

```text
classification
breaking changes
retention
regulated data
Metric View definition
Genie publication
AI service exposure
```

---

# Output

```text
Governance model:
- centralized/federated/hybrid

Domains:
- ...

Ownership:
- catalog:
- schemas:
- data products:
- Metric Views:
- Genie:
- AI services:

Stewards:
- ...

Technical identities:
- ...

Access-request routing:
- ...

Orphans:
- ...

Recertification:
- ...

Actions:
P0:
P1:
P2:
```

# Definition of Done

- [ ] Governance model está definido.
- [ ] Production assets usan group ownership cuando corresponde.
- [ ] Business ownership y technical run-as están separados.
- [ ] Service principals son utilizados para automation.
- [ ] Direct user grants fueron minimizados.
- [ ] `MANAGE` está utilizado conscientemente.
- [ ] Data products tienen steward.
- [ ] Metric Views tienen semantic ownership.
- [ ] Genie Agents tienen owner/curator.
- [ ] AI services tienen owners.
- [ ] Access request destinations están definidos.
- [ ] Orphan detection existe.
- [ ] Recertification tiene cadence basada en riesgo.
- [ ] Documentación está en español.

# Gotchas

- Unity Catalog objects sí pueden tener grupos como owners.
- Service principal no debe sustituir business ownership.
- Data Steward no necesita automáticamente MODIFY.
- Ownership y MANAGE no son idénticos.
- Una tabla puede estar técnicamente owned pero organizacionalmente huérfana.
- Genie y AI services también requieren lifecycle ownership.
