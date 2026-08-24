# Data Governance Skills

## Propósito

Esta carpeta contiene las skills de la persona **Data Governance**. Su objetivo es gobernar el lifecycle completo de datos y activos de AI: descubrirlos, clasificarlos, documentarlos, asignar ownership, controlar acceso, analizar lineage, gestionar cambios, definir retention, producir evidencia de compliance y atribuir costos.

El modelo final extiende la gobernanza tradicional:

```text
DATA AT REST
+
AI AT RUNTIME
```

Unity Catalog gobierna activos y permisos; Unity AI Gateway se evalúa cuando modelos, agentes, MCPs o tools necesitan control en ejecución.

## Lifecycle

```text
Discover
   ↓
Classify
   ↓
Own
   ↓
Document
   ↓
Protect
   ↓
Control Access
   ↓
Monitor / Audit
   ↓
Change
   ↓
Retain / Delete
   ↓
Evidence / Compliance
   ↓
Cost / FinOps
```

## Estado final del sistema

| Skill | Para qué sirve | Cuándo usarla |
|---|---|---|
| `data-catalog-documentation-standards` | Define metadata, discovery, tags y readiness para Genie | Cuando el catálogo no es comprensible o consumible |
| `sensitive-data-discovery-remediation` | Descubre y protege PII/PHI/PCI usando Data Classification, governed tags y ABAC | Para sensitive-data programs o secure-by-default |
| `data-ownership-stewardship-model` | Define owner, steward, technical owner, semantic owner y AI owner | Cuando nadie sabe quién decide o responde por un asset |
| `uc-permissions-audit-compliance` | Audita privileges, ownership, ABAC, RFA, sensitive access y AI access | Para least privilege, access reviews o auditorías |
| `compliance-framework-uc-mapping` | Mapea requisitos a capacidades/evidencia sin declarar compliance automático | Para SOC2, ISO, GDPR, PCI, políticas internas, etc. |
| `lineage-impact-change-management` | Analiza impacto estructural, semántico, security y AI antes de cambios | Antes de breaking changes, migrations o deprecations |
| `data-retention-purge-lifecycle` | Diseña retention, erasure, archive y physical purge | Para privacy, legal hold, minimization o lifecycle |
| `cost-attribution-chargeback` | Diseña attribution, showback, budgets, chargeback y AI FinOps | Cuando se necesita responder quién gasta qué y por qué |

## Cómo funciona el sistema

### Ciclo de onboarding de un nuevo dominio

```text
Nuevo dominio
    ↓
data-ownership-stewardship-model
    ↓
data-catalog-documentation-standards
    ↓
sensitive-data-discovery-remediation
    ↓
uc-permissions-audit-compliance
    ↓
operación continua
```

### Ciclo de cambio

```text
Cambio propuesto
    ↓
lineage-impact-change-management
    ↓
¿Afecta contrato/semántica?
    ├── Sí → Data Engineer / Data Analyst
    ↓
¿Afecta seguridad?
    ├── Sí → uc-permissions-audit-compliance
    ↓
Execute + validate
```

### Ciclo de privacidad

```text
Solicitud / policy
    ↓
data-retention-purge-lifecycle
    ↓
lineage
    ↓
todas las copias
    ↓
logical delete / archive / purge
    ↓
verification
    ↓
evidence
```

## Principios globales

1. **Capability no equivale a compliance.**
2. **Governance debe ser preventivo, no sólo auditoría posterior.**
3. **Data Classification es el default para sensitive-data discovery cuando cubre el caso.**
4. **Governed tags + ABAC son preferibles para políticas repetibles a escala.**
5. **Genie depende de Unity Catalog security; instrucciones del agente no son security boundary.**
6. **Metric Views también requieren semantic ownership y change management.**
7. **BROWSE/discovery y SELECT/data access son cosas distintas.**
8. **Groups son el default para ownership productivo cuando corresponde; service principals son identidades de ejecución.**
9. **Unity AI Gateway se evalúa para gobernar model services, agents, MCPs, tools, budgets y runtime policies.**
10. **Retention nunca se inventa desde una tabla genérica; proviene de policy/legal/business.**
11. **Todo código, comentarios, docstrings y documentación generados deben estar en español.**

## Ejemplos de uso

### Ejemplo 1 — Catálogo listo para Genie

**Skills**

```text
data-catalog-documentation-standards
        +
data-ownership-stewardship-model
```

**Prompt sugerido**

```text
Quiero preparar el dominio de ventas para Genie.

Audita:
- ownership;
- table descriptions;
- column descriptions;
- grain;
- sensitivity;
- critical dimensions;
- Metric Views existentes.

Separa metadata corporativa de metadata específica del Genie Agent.
No inventes KPIs.
```

---

### Ejemplo 2 — Detectar PII

**Skill**

```text
sensitive-data-discovery-remediation
```

**Prompt sugerido**

```text
Necesito clasificar información sensible en el catálogo de clientes.

Evalúa primero Databricks Data Classification.
Después define:
- governed tags;
- ABAC;
- masking;
- row filtering;
- secure-by-default;
- negative tests.

Usa AI Functions o regex sólo como complemento cuando la capacidad
administrada no cubra el caso.
```

---

### Ejemplo 3 — Auditoría de acceso

**Skill**

```text
uc-permissions-audit-compliance
```

**Prompt sugerido**

```text
Audita acceso a los catálogos de producción.

No clasifiques sobreprivilegio por número de grants ni por acceso nocturno.
Revisa:
- admin roles;
- ownership;
- MANAGE;
- ALL PRIVILEGES;
- direct grants;
- inherited grants;
- sensitive data;
- ABAC;
- tag permissions;
- RFA;
- AI Gateway/MCP access.

Prioriza findings por impacto real.
```

---

### Ejemplo 4 — Cambio de columna crítica

**Skill**

```text
lineage-impact-change-management
```

**Prompt sugerido**

```text
Queremos renombrar customer_status en producción.

Antes de cambiar:
- clasifica el cambio;
- revisa upstream/downstream lineage;
- revisa column lineage;
- identifica Metric Views;
- identifica Genie Agents;
- identifica modelos;
- identifica owners;
- propone estrategia de compatibilidad y rollback.
```

---

### Ejemplo 5 — Derecho de eliminación

**Skill**

```text
data-retention-purge-lifecycle
```

**Prompt sugerido**

```text
Tenemos una solicitud de eliminación de datos.

No ejecutes DELETE inmediatamente.

Primero:
- identifica policy authority;
- verifica legal hold;
- encuentra identifiers;
- inventaría source, Delta, archives, Lakebase, AI logs y ML artifacts;
- revisa riesgo de reingestión;
- diseña logical deletion, physical purge y verificación.
```

## Unity AI Gateway dentro de Governance

Cuando existen:

```text
models
agents
MCP servers
tools
external model providers
```

la gobernanza debe extenderse a runtime.

Evaluar:

```text
EXECUTE / MANAGE
owners
credentials
connections
tool allowlists
service policies
rate limits
budgets
inference tables
usage/audit
```

No todas las skills necesitan activar AI Gateway. Se utiliza cuando existe tráfico AI que debe ser gobernado.

## Handoffs a otras personas

| Señal | Handoff |
|---|---|
| Hace falta implementar pipeline/quality técnico | Data Engineer |
| Hace falta definir KPI o Metric View | Data Analyst |
| Hace falta evaluar/train/deploy modelo o agente | Data Scientist |
| El requerimiento es exclusivamente una aplicación OLTP | Arquitectura / Lakebase |

## Cargar estas skills dentro de Databricks

> **PLACEHOLDER — reemplazar esta sección con el procedimiento validado para su workspace.**

Esta sección debe mostrar cómo importar la carpeta `Data Governance` en Databricks, verificar la detección de las ocho skills y ejecutar una prueba de routing.

### Flujo que debería mostrar el GIF

1. Abrir el entorno de Databricks donde se administran/importan Agent Skills.
2. Seleccionar agregar/importar skills.
3. Cargar la carpeta `Data Governance`.
4. Confirmar que los ocho `SKILL.md` aparecen.
5. Abrir una skill, por ejemplo `sensitive-data-discovery-remediation`.
6. Ejecutar un prompt de clasificación de datos y mostrar el routing.

### Placeholder para el GIF

```markdown
![Cómo cargar las skills de Data Governance en Databricks](./assets/load-data-governance-skills-databricks.gif)
```

> Reemplazar la ruta con el GIF definitivo.

### Prueba mínima sugerida

```text
Necesito identificar datos sensibles en un catálogo y aplicar
políticas de masking a escala.
```

La skill esperada es:

```text
sensitive-data-discovery-remediation
```

## Qué NO debe hacer esta persona

- Declarar que una organización cumple SOC2/GDPR/PCI porque existe una feature.
- Crear scanners LLM custom antes de evaluar Data Classification.
- Usar instrucciones de Genie como access control.
- Inventar retention periods.
- Borrar datos sin revisar legal hold y copias downstream.
- Usar service principals como sustituto de business ownership.
- Tratar tags que controlan ABAC como metadata inocua.
- Hacer chargeback con falsa precisión cuando attribution es incompleta.

## Resultado esperado

```text
assets discovered
+
classification
+
ownership
+
metadata
+
policy
+
least privilege
+
lineage
+
controlled change
+
retention
+
audit evidence
+
FinOps
```

El objetivo final es que los datos y sistemas de AI sean utilizables, trazables y gobernables sin convertir Governance en un cuello de botella central.
