---
name: environment-promotion-workflow
description: Diseña promoción reproducible de proyectos Databricks entre development, staging y production mediante Declarative Automation Bundles, source control, testing, approvals y rollback seguro. Úsala para CI/CD de Lakeflow pipelines, Lakeflow Jobs, notebooks, SQL assets y otros recursos Databricks administrados como código.
---

# Environment Promotion Workflow

La unidad promovida debe ser una versión del proyecto, no cambios manuales dispersos.

## Default lifecycle

```text
feature branch
     ↓
dev
     ↓
pull request
     ↓
automated tests
     ↓
staging
     ↓
integration validation
     ↓
approval
     ↓
production
     ↓
post-deploy validation
```

---

## 1. Inventory deployable resources

Registrar:

```text
pipelines
jobs
source files
libraries
SQL assets
alerts
dashboards
Genie Agents cuando formen parte del proyecto
Lakebase resources cuando formen parte del proyecto
```

No intentar promover recursos desconocidos manualmente fuera del deployment definition.

---

## 2. Use Declarative Automation Bundles

Estructura sugerida:

```text
project/
├── databricks.yml
├── resources/
│   ├── pipelines.yml
│   └── jobs.yml
├── src/
│   ├── pipelines/
│   └── transformations/
├── tests/
│   ├── unit/
│   └── integration/
└── README.md
```

Adaptar al proyecto.

No crear carpetas vacías únicamente para cumplir una plantilla.

---

## 3. Define environment targets

Ejemplo conceptual:

```yaml
bundle:
  name: commerce-data-platform

variables:
  catalog:
    description: Catálogo utilizado por el ambiente.

targets:

  dev:
    mode: development
    default: true
    variables:
      catalog: dev_commerce

  staging:
    variables:
      catalog: staging_commerce

  prod:
    mode: production
    variables:
      catalog: production
```

Mantener diferencias de ambiente en configuración.

No hardcodearlas en transformación.

---

## 4. Identity

Producción debe ejecutarse mediante una identidad apropiada y estable.

Preferir:

- service principal;
- workload identity;
- least privilege.

No depender de las credenciales personales de un desarrollador.

---

## 5. Secrets

Nunca almacenar en Git:

```text
passwords
PATs
API keys
database credentials
model provider keys
```

Utilizar mecanismos administrados:

- Unity Catalog Connections;
- secret management;
- identity federation;
- environment configuration apropiada.

---

## 6. Unit tests

Para Lakeflow pipelines:

mantener lógica de transformación separada de decorators cuando sea posible.

Ejemplo:

```text
pure PySpark function
      ↓
pytest/local test
      ↓
pipeline wrapper
```

Validar:

- transformations;
- edge cases;
- schema expectations.

---

## 7. Static/deployment validation

Antes de deploy:

```bash
databricks bundle validate --target dev
```

Resolver errores antes de continuar.

No utilizar production como entorno de validación sintáctica.

---

## 8. Development deployment

```bash
databricks bundle deploy --target dev
```

Ejecutar pruebas necesarias.

Validar:

- DAG;
- schemas;
- quality;
- permissions;
- metadata.

---

## 9. Pull-request gate

El PR debe revisar:

```text
code
data contract changes
schema changes
permissions
environment changes
breaking changes
dependencies
```

Para cambios sensibles documentar impacto downstream.

---

## 10. Staging

Staging debe parecerse lo suficiente a production para encontrar incompatibilidades.

Pero no copiar información sensible indiscriminadamente.

Datos de staging pueden ser:

- synthetic;
- masked;
- governed sample;
- representative generated data;
- approved subset.

La decisión depende del tipo de test.

---

## 11. Integration tests

Validar:

```text
pipeline execution
expected tables
schema
quality
row-level logic
critical aggregates
permissions
external dependencies
```

No utilizar únicamente "job completed successfully".

---

## 12. Metadata validation

Antes de production:

verificar que nuevos assets tengan:

```text
comments
owners
domain information
critical column documentation
```

El código y comentarios generados deben estar en español.

---

## 13. Production approval

Para cambios de riesgo alto requerir un plan explícito:

```text
deployment
expected impact
validation
rollback
communication
```

No exigir approval humano para cada cambio trivial si el modelo operacional ya permite automated delivery segura.

---

## 14. Deploy production

```bash
databricks bundle deploy --target prod
```

Después ejecutar solamente la operación necesaria.

No asumir que deploy implica que los datos ya fueron recalculados correctamente.

---

## 15. Post-deploy validation

Verificar:

```text
resource state
pipeline update
quality
freshness
critical business aggregates
consumer access
```

---

# Rollback

## Code/config rollback

Preferir:

```text
known good commit/tag
     ↓
deploy previous definition
     ↓
validate
```

## Data rollback

Un redeploy de código no necesariamente revierte:

- schema changes;
- mutated data;
- backfills;
- permissions already changed.

Diseñar recuperación separadamente.

No utilizar:

```bash
databricks bundle destroy --target prod
```

como mecanismo normal de rollback.

`destroy` es una operación destructiva de lifecycle, no un undo universal.

---

## 16. Database migration gate

Si el bundle administra Lakebase:

tratar database schema migration como una operación stateful separada.

No asumir que rollback del Bundle revierte transacciones o schema.

---

## 17. Genie dependency gate

Si un proyecto incluye un Genie Agent:

promover primero sus dependencias:

```text
tables
metadata
Metric Views
permissions
```

y después validar sus benchmark questions.

No publicar el agente contra assets incompletos.

---

## 18. Production evidence

Registrar:

```text
git commit
release/tag
bundle target
deployment timestamp
identity
tests
approval cuando aplica
validation results
```

---

## Output

```text
Project:

Resources:
- ...

Targets:
- dev
- staging
- prod

Identity:
- ...

Testing:
- unit:
- integration:

Promotion gates:
- ...

Breaking changes:
- ...

Deployment:
- ...

Post-deploy validation:
- ...

Rollback:
- code:
- data:

Evidence:
- ...
```

---

# Definition of Done

- [ ] Los assets están versionados.
- [ ] Se utilizan Declarative Automation Bundles.
- [ ] Las diferencias de ambiente están parametrizadas.
- [ ] Producción usa identidad apropiada.
- [ ] No existen secretos hardcoded.
- [ ] Existen unit tests donde aportan valor.
- [ ] Bundle validation pasa.
- [ ] Staging usa datos gobernados.
- [ ] Existen integration tests.
- [ ] Se revisaron breaking changes.
- [ ] Production tiene post-deploy validation.
- [ ] Rollback de código y datos están diferenciados.
- [ ] Existe evidencia de deployment.
- [ ] Documentación está en español.

# Gotchas

- Deploy exitoso no significa pipeline correcto.
- Rollback de código no deshace datos.
- `bundle destroy` no es rollback.
- Staging no justifica copiar PII de producción.
- Un cambio declarativo puede ser destructivo si modifica estado.
- No utilizar identidad personal para recursos productivos.
