---
name: sensitive-data-discovery-remediation
description: Descubre, clasifica, valida y protege información sensible en Unity Catalog mediante Data Classification, governed tags, Custom Classifiers, ABAC, row filters y column masks. Úsala para inventarios de PII/PHI/PCI, clasificación continua, secure-by-default, remediación de datos sensibles, revisión de exposiciones o incorporación de nuevos dominios al modelo de protección.
---

# Sensitive Data Discovery & Remediation

El objetivo no es encontrar columnas que "parecen sensibles".

El objetivo es crear un ciclo gobernado:

**Discover → Classify → Review → Protect → Validate → Monitor**

---

# 1. Define sensitivity taxonomy

Antes del scan identificar:

```text
Regulatory categories:
- PII
- PHI
- PCI
- financial
- credentials

Organizational categories:
- confidential
- restricted
- internal
- public

Custom identifiers:
- employee_id
- customer_account_id
- partner_reference
```

No mezclar:

```text
regulatory classification
```

con:

```text
business confidentiality tier
```

---

# 2. Define scope

Registrar:

```text
Catalog:
Schemas:
Countries:
Data domains:
Known sensitive systems:
Compliance requirements:
Consumers:
```

Country/context importa porque algunas categorías son regionales.

---

# 3. Use Data Classification first

Cuando esté disponible:

habilitar Databricks Data Classification para los catalogs correspondientes.

La capacidad debe ser el default para:

```text
automatic discovery
sensitive-column classification
incremental scanning
system governed tags
coverage monitoring
```

No construir inicialmente una solución basada en SQL regex + LLM.

---

# 4. Review classification output

Clasificación automática no equivale a decisión final de gobierno.

Revisar:

```text
detected class
confidence/context
sample values when authorized
false positives
false negatives
business context
```

No exponer sample values a usuarios que no necesitan acceso al contenido.

---

# 5. Understand system classification tags

Data Classification puede aplicar governed tags del tipo:

```text
class.name
class.email_address
class.phone_number
class.date_of_birth
...
```

Utilizar estas tags como inputs para políticas.

No duplicar automáticamente:

```text
class.email_address
```

con:

```text
sensitivity=email
pii=email
contains_email=true
```

sin una necesidad organizacional distinta.

---

# 6. Custom Classifiers

Si un tipo de dato sensible específico no está cubierto:

evaluar Custom Classifiers.

Ejemplos:

```text
internal_employee_number
insurance_policy_number
customer_contract_code
local proprietary identifier
```

Definir:

```text
governed tag
description
representative examples
validation samples
owner
```

Revisar falsos positivos antes de activar a escala.

---

# 7. AI Functions fallback

AI Functions pueden complementar discovery cuando:

- Data Classification no está disponible;
- se realiza un POC;
- existe una clasificación semántica muy específica;
- se necesita enriquecer datos posteriormente.

Evaluar, por ejemplo:

```text
ai_classify
ai_extract
ai_mask
```

según el problema.

No usar `ai_classify` sobre todas las filas para descubrir PII.

Eso:

```text
aumenta costo
aumenta exposición
puede ser innecesario
```

---

# 8. Regex fallback

Regex sigue siendo útil para:

```text
highly deterministic formats
pre-screening
validation
known identifiers
```

Ejemplos:

```text
UUID-like identifiers
country-specific fixed formats
email syntax
```

Pero regex:

```text
nombre de columna
```

no demuestra contenido sensible.

Combinar signals cuando corresponda.

---

# 9. Protect by policy, not manual repetition

Para protección repetible a escala:

preferir ABAC.

Modelo:

```text
Data Classification
       ↓
governed class.* tags
       ↓
ABAC policy
       ↓
mask/filter
```

Esto evita configurar manualmente cada nueva columna.

---

# 10. Column masking

Definir la política según:

```text
classification
consumer identity
purpose
region
consent
clearance
```

La mask debe conservar un tipo compatible con la columna.

No utilizar una única máscara parcial para todos los tipos de PII.

Ejemplo:

```text
email
→ masked email

national ID
→ redact

DOB
→ generalized/year only

payment details
→ strong redaction
```

según política organizacional.

---

# 11. Row filtering

Utilizar cuando sensibilidad depende del registro.

Ejemplos:

```text
country
region
tenant
consent
business unit
```

Preferir ABAC para políticas repetidas a escala.

Utilizar table-level row filters para lógica verdaderamente local o cuando ABAC no corresponda.

---

# 12. Secure-by-default

Para áreas donde tablas nuevas pueden contener información sensible:

evaluar patrón:

```text
schema:
review_status = pending

new table
      ↓
restricted/masked by default
      ↓
Data Classification
      ↓
steward review
      ↓
review_status = reviewed
      ↓
normal ABAC classification policies
```

Esto reduce la ventana donde una tabla nueva puede quedar expuesta antes de ser clasificada.

---

# 13. Control tag permissions

Los tags que activan seguridad son parte del security boundary.

Definir:

```text
who can create governed tags
who can assign
who can remove
who can manage policies
```

No dar `APPLY TAG` indiscriminadamente sobre tags que controlan masking.

Un usuario capaz de quitar el tag puede modificar qué políticas se aplican.

---

# 14. Validate policy with identities

Probar como mínimo roles representativos:

```text
authorized sensitive-data reader
standard analyst
data steward
service principal
Genie consumer
```

No validar sólo como admin.

---

# 15. Negative tests

Probar explícitamente:

```text
SELECT sensitive column
query through view
query through dashboard
query through Genie
join against sensitive table
access from unauthorized group
```

Esperar fallos o masks apropiados.

---

# 16. Genie

La seguridad de Genie debe venir de Unity Catalog.

Nunca utilizar una instrucción:

```text
"No le muestres información sensible a usuarios no autorizados"
```

como sustituto de access control.

Si un usuario no puede acceder al dato, el control debe aplicarse en la capa de gobierno.

---

# 17. AI Gateway sensitive-content gate

Cuando datos sensibles puedan entrar en:

```text
LLM requests
agents
MCP calls
external tools
```

la clasificación de tablas no es suficiente.

Evaluar Unity AI Gateway y service policies para gobernar el runtime de AI.

Casos:

```text
PII in prompts
prompt injection
unsafe content
unauthorized tools
external provider routing
```

---

# 18. Inference tables

Si se habilitan AI Gateway inference tables:

tratar request/response payloads como un dataset potencialmente sensible.

Definir:

```text
access
classification
retention
monitoring
purpose
```

No habilitar logging completo por compliance sin considerar que el propio log puede contener PII.

---

# 19. Remediation modes

Una detección puede producir:

```text
TAG
MASK
ROW FILTER
REVOKE
RELOCATE
DELETE
PSEUDONYMIZE
INVESTIGATE
```

No asumir que toda PII debe borrarse.

La acción depende de:

```text
purpose
legal basis
policy
consumer
retention
```

---

# 20. Continuous classification

Discovery no es un proyecto one-time.

Monitorizar:

```text
new tables
new columns
classification changes
unreviewed detections
new sensitive domains
custom classifier quality
```

Data Classification ya incorpora scanning incremental; aprovecharlo.

---

# Output

```text
Scope:

Taxonomy:
- ...

Data Classification:
- status:
- coverage:

Detections:
- class:
  assets:

Custom classifiers:
- ...

False positives:
- ...

False negatives:
- ...

ABAC:
- policies:

Secure-by-default:
- ...

AI runtime exposure:
- ...

Remediation:
P0:
P1:
P2:
```

# Definition of Done

- [ ] Scope está definido.
- [ ] Taxonomy está definida.
- [ ] Se evaluó Data Classification antes de custom scanning.
- [ ] Detections críticas fueron revisadas.
- [ ] Custom Classifiers se evaluaron para categorías propias.
- [ ] Governed tags son utilizados para security policy cuando corresponde.
- [ ] Se evaluó ABAC.
- [ ] Tag permissions están restringidos.
- [ ] Se realizaron tests con identidades no-admin.
- [ ] Se realizaron negative tests.
- [ ] Genie depende de UC security.
- [ ] Se evaluó AI Gateway para sensitive AI traffic.
- [ ] Inference tables tienen policy de sensibilidad si se usan.
- [ ] Existe continuous classification.
- [ ] Documentación está en español.

# Gotchas

- Column name no demuestra sensitivity.
- Classification automática necesita review para casos críticos.
- Tag security depende de quién puede modificar el tag.
- Masking no es lo mismo que erasure.
- Genie instructions no son un security boundary.
- Los logs de AI pueden ser tan sensibles como los datos originales.
- No escanear todo el dataset con un LLM cuando existe clasificación administrada.

Databricks incluso documenta un patrón secure-by-default: nuevas tablas heredan un estado pendiente, se protegen mientras Data Classification las analiza y sólo después del steward review pasan al estado revisado.
