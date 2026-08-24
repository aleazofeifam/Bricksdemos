---
name: data-catalog-documentation-standards
description: Define y audita estándares de metadata, documentación, descubrimiento y clasificación para activos de datos y AI en Unity Catalog. Úsala cuando tablas, vistas, Metric Views, modelos u otros assets carezcan de descripciones, ownership, tags o contexto de negocio; cuando se quiera mejorar discovery; o cuando se necesite preparar datasets gobernados para Genie Agents y otros consumidores.
---

# Data Catalog Documentation Standards

Un catálogo documentado debe permitir que una persona o agente pueda responder:

1. ¿Qué es este activo?
2. ¿Para qué sirve?
3. ¿Cuál es su granularidad?
4. ¿De dónde viene?
5. ¿Qué tan fresco está?
6. ¿Quién lo administra?
7. ¿Qué restricciones tiene?
8. ¿Qué conceptos de negocio representa?
9. ¿Quién debería consumirlo?
10. ¿Qué otros activos dependen de él?

La documentación es una interfaz del producto de datos.

---

# Metadata layers

Separar conscientemente:

```text
UNITY CATALOG METADATA
→ contexto corporativo reutilizable

GENIE KNOWLEDGE STORE
→ contexto específico del agente

GOVERNED TAGS
→ atributos utilizados por políticas

DATA CLASSIFICATION TAGS
→ sensibilidad detectada

DATA CONTRACT
→ garantías productor-consumidor
```

No utilizar un único mecanismo para todos los propósitos.

---

# 1. Scope

Antes de documentar determinar:

```text
Catalog:
Schemas:
Asset types:
Consumers:
Business domains:
Critical products:
Genie Agents:
Compliance scope:
```

No intentar documentar indiscriminadamente todo el catálogo con el mismo nivel de profundidad.

Priorizar por:

```text
business criticality
usage
downstream dependencies
sensitivity
AI/Genie consumption
lack of metadata
```

---

# 2. Asset identity

Para cada activo crítico capturar:

```text
Name:
Type:
Domain:
Purpose:
Owner:
Steward:
Consumers:
Lifecycle status:
```

Asset types pueden incluir:

```text
table
view
materialized view
streaming table
metric view
volume
function
model
connection
```

---

# 3. Table documentation standard

Una tabla consumible debe describir al menos:

```text
propósito
granularidad
source
freshness expectation
owner/domain
important limitations
```

Ejemplo:

```sql
COMMENT ON TABLE production.commerce.orders IS
  'Pedidos consolidados del canal digital.
   Granularidad: una fila por pedido.
   Fuente principal: plataforma de comercio electrónico.
   Diseñada para análisis comercial y financiero.';
```

No incluir información que cambia diariamente dentro del COMMENT.

---

# 4. Column documentation standard

Priorizar columnas que afectan interpretación:

```text
business identifiers
dates/timestamps
measures
amounts
currency
status
dimensions
codes
foreign keys
sensitive fields
```

Ejemplo:

```sql
COMMENT ON COLUMN production.commerce.orders.order_date IS
  'Fecha y hora de creación del pedido en UTC.
   No representa la fecha de facturación ni la fecha de envío.';
```

Una descripción debe aclarar ambigüedad.

Evitar:

```text
order_date = "Fecha del pedido"
```

si no agrega información.

---

# 5. Technical metadata

No ocultar automáticamente metadata técnica.

Clasificar:

```text
BUSINESS RELEVANT
→ documentar y exponer

OPERATIONS RELEVANT
→ documentar para técnicos

INTERNAL IMPLEMENTATION
→ documentar cuando sea necesario,
   pero no necesariamente exponer a consumidores
```

Por ejemplo:

```text
_ingested_at
_source_file
_rescued_data
```

pueden ser irrelevantes para Genie pero muy importantes para observabilidad o debugging.

El problema no es documentarlas.

El problema es incluirlas innecesariamente en interfaces de negocio.

---

# 6. Naming

No imponer universalmente:

```text
bronze_
silver_
gold_
```

en el nombre del objeto.

Separar:

```text
logical domain
lifecycle/layer
entity
purpose
```

Unity Catalog ya ofrece:

```text
catalog.schema.object
```

como namespace.

La organización debe definir una convención consistente que refleje su arquitectura.

Ejemplo:

```text
production.commerce.orders
production.finance.general_ledger
```

puede ser superior a:

```text
gold_commerce_orders
```

si el catálogo/schema ya expresan environment y layer.

---

# 7. Controlled vocabulary

Definir vocabularios para conceptos gobernados.

Ejemplos:

```text
domain
lifecycle
criticality
classification
data_product
retention_class
```

Cuando un tag determine una política de seguridad:

utilizar **governed tags**.

No utilizar tags libres para controles críticos.

---

# 8. Governed tags

Los governed tags son atributos de gobierno con permisos propios.

Diseñar:

```text
tag key
allowed values
owner
who can assign
who can manage
policy dependency
```

Ejemplo conceptual:

```text
classification:
  public
  internal
  confidential
  restricted
```

No colocar PII ni secretos dentro del nombre o valor de un tag.

Los tags pueden ser replicados y son metadata visible según permisos.

---

# 9. Data Classification

Para identificación de información sensible:

evaluar primero **Databricks Data Classification**.

No construir un scanner custom como mecanismo principal cuando Data Classification satisface el caso.

Data Classification puede:

```text
scan data automatically
classify columns
apply system governed class.* tags
scan incrementally
surface coverage
feed ABAC policies
```

Ejemplos conceptuales:

```text
class.name
class.email_address
class.phone_number
class.date_of_birth
```

---

# 10. Custom classifications

Cuando la organización tenga conceptos propios:

```text
employee_internal_id
client_account_reference
partner_identifier
proprietary_product_code
```

evaluar Custom Classifiers cuando estén disponibles y aprobados para el entorno.

No reutilizar una clasificación regulatoria para representar un concepto distinto.

---

# 11. Discovery

El catálogo debe permitir:

```text
search
browse
lineage
ownership discovery
access request
```

Evaluar `BROWSE` como mecanismo para permitir descubrimiento de metadata sin conceder acceso a los datos.

No confundir:

```text
discoverability
```

con:

```text
data access
```

---

# 12. Access requests

Para un modelo self-service:

configurar access request destinations.

Pueden dirigir solicitudes hacia:

```text
email
Slack
Microsoft Teams
webhook
external request system
```

No obligar al usuario a localizar manualmente al propietario del dato.

---

# 13. Genie-readiness

Para activos destinados a Genie Agent, revisar obligatoriamente:

```text
table description
column descriptions
grain
business terminology
ambiguous columns
relationships
critical dimensions
Metric Views
```

Preguntar además:

```text
¿Qué preguntas espera hacer el usuario?
¿Qué intenta encontrar?
¿Qué palabras utiliza?
```

No inventar las preguntas únicamente desde IT.

---

# 14. Canonical vs Genie-local metadata

Unity Catalog debe contener significado corporativo reusable.

Genie Agent puede contener contexto adicional específico del dominio:

```text
local descriptions
synonyms
join relationships
SQL expressions
prompt matching settings
```

No poner instrucciones específicas de un Genie Agent en el COMMENT corporativo de una tabla.

Ejemplo incorrecto:

```text
"Cuando el usuario pregunte ventas, filtra status='A'."
```

como COMMENT de tabla.

Eso pertenece a semántica o configuración apropiada del agente.

---

# 15. Metric View governance

Cuando un activo representa KPIs oficiales:

verificar si existe Metric View.

Metadata relevante:

```text
measure definition
dimensions
display names
synonyms
comments
owner
```

No duplicar una definición corporativa en:

```text
dashboard SQL
Genie SQL
notebook
COMMENT
```

Hacer handoff a:

`semantic-layer-strategy`

cuando haya que crear/modificar la capa semántica.

---

# 16. Genie benchmark readiness

Governance debe comprobar que existe:

```text
owner
approved data
approved semantics
metadata
```

pero el benchmark funcional pertenece principalmente al Data Analyst.

Handoff:

`self-service-analytics-enablement`

para:

```text
sample questions
expected SQL
benchmarks
accuracy validation
```

---

# 17. Documentation quality metrics

No utilizar únicamente:

```text
% con COMMENT
```

Una tabla con un COMMENT inútil no está documentada.

Medir por dimensiones:

```text
coverage
completeness
quality
ownership
classification
usage
```

Ejemplo:

```text
% assets críticos con owner
% assets críticos con propósito
% columnas críticas documentadas
% assets sensibles clasificados
% Genie source assets preparados
```

Definir targets según madurez y riesgo de la organización.

No imponer 85%, 90% o cualquier otro porcentaje universal.

---

# 18. Staleness

Metadata también envejece.

Detectar:

```text
schema changed
owner changed
source changed
freshness changed
business definition changed
```

Revisar metadata cuando cambia el activo.

No asumir que documentación creada una vez permanece correcta.

---

# 19. AI-assisted documentation

Genie Code u otras capacidades AI pueden ayudar a generar borradores.

Tratar cualquier descripción generada automáticamente como:

```text
draft
```

hasta validarla cuando el significado sea crítico.

Un LLM puede inferir incorrectamente la semántica a partir del nombre de una columna.

---

# 20. Language standard

Todo COMMENT, explicación, docstring y documentación generado por esta skill debe estar en español salvo solicitud explícita contraria.

No traducir:

```text
physical table names
column identifiers
API names
standard protocol names
```

si hacerlo rompe contratos existentes.

---

# Output

```text
Scope:

Assets analyzed:
- ...

Documentation coverage:
- ...

Critical gaps:
- ...

Ownership:
- ...

Classification:
- ...

Governed tags:
- ...

Genie-ready assets:
- ...

Metric Views:
- ...

Access request configuration:
- ...

Actions:
P0:
P1:
P2:
```

# Definition of Done

- [ ] Se identificó el scope.
- [ ] Assets críticos tienen propósito.
- [ ] Grain está documentado donde aplica.
- [ ] Columnas críticas tienen significado claro.
- [ ] Ownership está disponible.
- [ ] Se diferenciaron governed y descriptive tags.
- [ ] Se evaluó Data Classification.
- [ ] Sensitive assets tienen clasificación.
- [ ] Se revisó BROWSE/discovery.
- [ ] Se revisaron access request destinations.
- [ ] Se evaluó Genie-readiness.
- [ ] Se identificaron Metric Views cuando existen KPIs.
- [ ] Metadata corporativa y Genie-local están separadas.
- [ ] No se utilizaron coverage thresholds arbitrarios.
- [ ] Metadata generada está en español.

# Gotchas

- COMMENT presente no significa documentación útil.
- Tags libres no deben controlar políticas críticas cuando governed tags son apropiados.
- Data Classification debe preceder scanners custom cuando cubre el caso.
- Metadata de Genie y metadata corporativa tienen scopes diferentes.
- Una descripción incorrecta puede perjudicar tanto a usuarios como a Genie.
- Naming convention no debe duplicar innecesariamente catalog/schema hierarchy.

Databricks actualmente utiliza Data Classification agentic para clasificar y etiquetar automáticamente datos sensibles, incluyendo escaneo incremental; además recomienda utilizar esas clasificaciones con ABAC.
