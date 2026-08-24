---
name: reproducibility-environment-pinning
description: Hace reproducibles y auditables experimentos de ML registrando código, datos, features, dependencias, runtime, random seeds, hardware, parámetros y modelos mediante MLflow 3 y Unity Catalog. Úsala cuando un experimento deba recrearse, auditarse, compararse, depurarse o convertirse en un pipeline productivo.
---

# ML Reproducibility & Environment Pinning

"Reproducible" debe tener una definición explícita.

# Reproducibility levels

## Semantic reproducibility

Mismo código/datos/configuración produce comportamiento funcional equivalente.

## Statistical reproducibility

Las métricas permanecen dentro de una tolerancia definida.

## Bitwise/deterministic reproducibility

Se espera output numéricamente idéntico.

No prometer bitwise reproducibility en GPU/distributed systems sin demostrarlo.

---

# Reproducibility record

Todo experimento importante debe poder responder:

```text
¿Qué código?
¿Qué datos?
¿Qué features?
¿Qué environment?
¿Qué model/library?
¿Qué parámetros?
¿Qué seed?
¿Qué hardware?
¿Qué resultado?
```

---

## 1. Pin code

Registrar:

```text
Git repository
commit SHA
branch/tag cuando aplica
dirty/uncommitted state
```

No utilizar sólo el nombre del notebook.

---

## 2. Pin data

Preferir una referencia inmutable o versionada.

Para Delta puede utilizarse:

```text
table
version/timestamp
```

Ejemplo:

```python
data_version = (
    spark.sql(
        "DESCRIBE HISTORY production.ml.features LIMIT 1"
    )
    .select("version")
    .first()[0]
)

df = (
    spark.read
    .option("versionAsOf", data_version)
    .table("production.ml.features")
)
```

Registrar la versión en MLflow.

---

## 3. Confirm retention feasibility

Time Travel sólo es una referencia reproducible mientras los archivos necesarios estén disponibles.

Antes de prometer reproducción de largo plazo:

revisar:

```text
VACUUM policy
deleted-file retention
log retention
table lifecycle
compliance retention
```

No modificar retention automáticamente.

---

## 4. Durable training snapshots

Si la política de la tabla no garantiza la ventana requerida:

crear un artefacto de training gobernado.

Opciones:

```text
dedicated immutable Delta dataset
approved snapshot
versioned feature table
UC volume artifact
```

Elegir según volumen y governance.

No hacer DEEP CLONE automáticamente para cualquier run.

---

## 5. Record dataset identity

Registrar:

```text
table
version
query/filter
features
label definition
date window
dataset digest cuando corresponda
```

La versión de una tabla no es suficiente si el training aplica filtros dinámicos.

---

## 6. Avoid dynamic queries

No registrar únicamente:

```sql
WHERE event_date >= CURRENT_DATE() - 30
```

porque su resultado cambia.

Resolver fechas concretas y registrarlas.

---

## 7. Pin dependencies

Preferir:

```text
requirements
environment spec
lockfile
AI Runtime environment version
Databricks Runtime version
```

`pip freeze` puede utilizarse como evidencia, pero no debe ser el único mecanismo de environment management.

---

## 8. AI Runtime

Para training sobre AI Runtime registrar:

```text
environment type
environment version
accelerator
number of GPUs
distributed strategy
```

---

## 9. Record hardware

Para resultados sensibles al hardware registrar cuando corresponda:

```text
CPU/GPU
accelerator
GPU count
distributed topology
precision
```

---

## 10. Seeds

Fijar seeds de las librerías realmente utilizadas.

Ejemplos:

```text
Python random
NumPy
PyTorch
TensorFlow
framework-specific
```

No agregar seeds de librerías inexistentes sólo para completar checklist.

---

## 11. Deterministic algorithms

Cuando se necesite determinismo fuerte:

evaluar flags específicos del framework.

Documentar tradeoff:

```text
determinism
vs
performance
```

No activarlos automáticamente para exploración corriente.

---

## 12. Spark ordering

No depender del orden implícito de filas.

Para operaciones cuyo resultado depende del orden:

definir explícitamente:

```text
ORDER BY
stable key
```

Para train/test split, preferir una asignación estable por ID/hash o un split registrado.

---

## 13. Pin feature logic

Registrar:

```text
feature definitions
source tables
feature code commit
lookback windows
point-in-time semantics
```

Evitar training-serving skew.

---

## 14. MLflow 3

Registrar:

```text
params
metrics
datasets
artifacts
model
code
environment
```

Utilizar Logged Models para asociar la evidencia del lifecycle cuando corresponda.

---

## 15. Model signature

Todo model candidate destinado a UC debe tener signature.

Registrar input example cuando sea apropiado.

---

## 16. Reproduction command

Cada experimento crítico debería tener una forma clara de recrearse.

Ejemplo conceptual:

```text
git checkout <sha>
load environment
load dataset version
run training config
run evaluation
compare tolerance
```

---

## 17. Verify reproducibility

No marcar:

```text
reproducible=true
```

sin haber reproducido.

Ejecutar una segunda vez cuando la criticidad lo requiera.

Comparar según el nivel definido:

```text
exact
tolerance
statistical
```

---

## 18. GenAI applications

Para agentes registrar además:

```text
model service
prompt version
tools
MCPs
retrieval configuration
evaluation dataset
```

Invocar `agent-evaluation-workflow`.

---

## 19. Unity AI Gateway

Si la aplicación utiliza model/provider services:

registrar la identidad lógica del servicio.

Evitar basar reproducibilidad en un nombre de provider/model que puede cambiar silenciosamente.

También considerar model lifecycle/deprecation.

---

## 20. Documentation

Crear un reproducibility manifest.

Ejemplo:

```yaml
experiment:
  code:
    git_sha: ...

  data:
    table: production.ml.features
    version: ...

  environment:
    type: ai-runtime
    version: ...

  training:
    seed: ...
    parameters: ...

  model:
    mlflow_model_id: ...

  evaluation:
    dataset: ...
```

Comentarios y documentación en español.

---

# Output

```text
Experiment:

Reproducibility level:
- semantic
- statistical
- deterministic

Code:
- repo:
- commit:

Data:
- table:
- version:
- filters:
- snapshot:

Features:
- ...

Environment:
- ...

Hardware:
- ...

Seeds:
- ...

MLflow:
- run:
- model:

Reproduction procedure:
- ...

Verification:
- ...

Known nondeterminism:
- ...
```

# Definition of Done

- [ ] Se definió el nivel de reproducibilidad.
- [ ] Código tiene commit identificable.
- [ ] Data tiene versión/snapshot.
- [ ] Queries dinámicas fueron resueltas.
- [ ] Retention fue revisado.
- [ ] Dependencias están registradas.
- [ ] Runtime está registrado.
- [ ] Hardware relevante está registrado.
- [ ] Seeds relevantes están definidos.
- [ ] Feature logic está versionada.
- [ ] MLflow contiene evidencia.
- [ ] Model signature existe para candidates.
- [ ] Se documentó procedimiento de reproducción.
- [ ] Se verificó realmente cuando el riesgo lo requiere.
- [ ] Limitaciones están documentadas en español.

# Gotchas

- Seed fijo no garantiza GPU determinism.
- Delta version no sirve si VACUUM eliminó los archivos necesarios.
- `pip freeze` no captura hardware.
- Código idéntico con datos distintos no es reproducción.
- Datos idénticos con feature logic distinta tampoco lo es.
- “Reproducible” sin tolerancia definida es ambiguo.
