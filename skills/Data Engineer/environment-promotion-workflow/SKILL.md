---
name: environment-promotion-workflow
description: Workflow de promoción de pipelines entre ambientes (dev→staging→prod) usando Databricks Asset Bundles, parametrización por target, y validación pre-deploy. Úsala cuando necesites mover código de desarrollo a producción de forma segura, repetible, y con rollback.
---

# Environment Promotion Workflow (Dev → Staging → Prod)

Cómo estructurar y promover pipelines entre ambientes usando Declarative Automation Bundles (DABs).

## Estructura de Bundle recomendada

```
my-project/
├── databricks.yml          # Targets: dev, staging, prod
├── resources/
│   ├── pipeline.yml        # DLT pipeline config
│   └── job.yml             # Job orchestration
├── src/
│   ├── bronze.py
│   ├── silver.py
│   └── gold.py
└── tests/
    └── integration_test.py
```

## databricks.yml con targets

```yaml
bundle:
  name: etl-pipeline

variables:
  catalog:
    default: dev_catalog
  schema:
    default: etl

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: dev_catalog
    workspace:
      host: https://dev-workspace.cloud.databricks.com

  staging:
    variables:
      catalog: staging_catalog
    workspace:
      host: https://staging-workspace.cloud.databricks.com

  prod:
    mode: production
    variables:
      catalog: production
    workspace:
      host: https://prod-workspace.cloud.databricks.com
    run_as:
      service_principal_name: etl-prod-sp
```

## CI/CD Flow

```bash
# 1. Develop locally
databricks bundle validate --target dev
databricks bundle deploy --target dev
databricks bundle run --target dev etl_job

# 2. PR merge → staging (CI)
databricks bundle deploy --target staging
databricks bundle run --target staging integration_tests

# 3. Release → prod (CD, después de approval)
databricks bundle deploy --target prod
```

## Rollback

```bash
# Opción 1: Re-deploy versión anterior
git checkout <previous-tag>
databricks bundle deploy --target prod

# Opción 2: Destroy + redeploy (destructivo)
databricks bundle destroy --target prod  # CUIDADO: borra recursos
git checkout <previous-tag>
databricks bundle deploy --target prod
```

## Gotchas

* `bundle deploy` NO hace rollback automático si falla mid-deploy. Si un recurso se crea pero otro falla, queda en estado inconsistente.
* Los nombres de recursos DEBEN incluir `${bundle.target}` para evitar colisiones entre ambientes en el mismo workspace.
* El catálogo de UC en dev vs prod requiere que el Service Principal tenga grants en AMBOS. Crear SP separados por ambiente.
* Las pipelines DLT no soportan `bundle destroy` limpio — dejan tablas huérfanas en UC. Limpiar manualmente con `DROP TABLE`.
* `mode: development` agrega prefijo `[dev ${user}]` a los nombres. NO usar en prod.
* Para secrets: usar variables de entorno en CI o Databricks secret scopes. NUNCA hardcodear credenciales en el bundle YAML.
* Git tag cada release a prod para rollback fácil: `git tag -a v1.2.3 -m "Prod release"`. El rollback es `git checkout v1.2.2` + redeploy.
* Testing en staging debe usar datos REALES (subset) no synthetic. Copiar un sample de prod con `CREATE TABLE staging.test AS SELECT * FROM prod.table LIMIT 10000`.
