---
name: ml-cicd-model-promotion
description: Diseña CI/CD y promoción gobernada de modelos ML usando MLflow 3, Logged Models, Models in Unity Catalog, aliases, deployment jobs, Model Serving y validation gates. Úsala para automatizar candidate validation, challenger/champion comparison, canary rollout, batch deployment, real-time serving, rollback y auditabilidad del lifecycle de modelos.
---

# ML CI/CD & Model Promotion

La unidad de promoción es un modelo validado y reproducible, no simplemente el último training run.

# Lifecycle

**Train → Evaluate → Register → Validate → Challenger → Deploy → Observe → Champion**

---

## 1. Identify deployment type

```text
Batch inference
Real-time serving
Streaming inference
Agent/model service
```

La promoción cambia según el serving pattern.

---

## 2. Separate environments

Cuando sea posible:

```text
development
staging
production
```

Expresar environment mediante:

- catalog/schema;
- CI/CD configuration;
- deployment workflow.

No utilizar stages legacy del Workspace Model Registry.

Models in Unity Catalog utiliza aliases.

---

## 3. Training output

El training pipeline debe producir:

```text
model
signature
input example
metrics
dataset lineage
git/code lineage
environment
```

Utilizar MLflow 3 Logged Models cuando corresponda.

No buscar “el run más reciente” y asumir que es candidate.

---

## 4. Candidate declaration

Un candidate debe identificarse explícitamente.

Ejemplo conceptual:

```text
Logged Model
      ↓
validation
      ↓
registered model version
      ↓
Challenger alias
```

No promover accidentalmente un experimento incompleto.

---

## 5. Validation dimensions

Antes de promotion validar:

### Model quality

```text
AUC
F1
RMSE
ranking metric
calibration
etc.
```

según el problema.

### Slice quality

```text
region
segment
product
demographic slice cuando legal/appropriate
edge cases
```

### Data

```text
schema
feature availability
missingness
```

### Operational

```text
model load
prediction schema
latency
memory
throughput
```

### Governance

```text
owner
permissions
lineage
documentation
```

---

## 6. Compare Challenger vs Champion

Comparar:

```text
challenger
vs
current champion
```

No utilizar únicamente un threshold estático.

También comparar contra business baseline cuando no existe champion.

---

## 7. Release gates

Definir por modelo.

Ejemplo:

```yaml
quality:
  primary_metric:
    regression_not_allowed_beyond: business_defined

critical_slices:
  no_material_regression: true

operational:
  latency_within_slo: true

governance:
  model_signature: required
  owner: required
```

No hardcodear `AUC > 0.82`.

---

## 8. Register in Unity Catalog

Usar Models in Unity Catalog como registry.

Mantener:

```text
model description
version description
intended use
limitations
owner
training lineage
evaluation
```

---

## 9. Use aliases for lifecycle state

Ejemplos:

```text
Champion
Challenger
Shadow
```

Los nombres son una convención organizacional.

No asumir que un alias despliega por sí mismo un real-time endpoint.

---

# Batch inference behavior

Puede cargar:

```python
model_uri = "models:/production.ml.churn@Champion"
```

En la siguiente ejecución, el alias se resuelve a la versión vigente.

Esto permite desacoplar batch inference de números de versión.

---

# Real-time serving behavior

Para Model Serving:

```text
resolve Champion alias
       ↓
obtain version
       ↓
update endpoint config
       ↓
wait until ready
       ↓
health validation
```

Cambiar el alias no debe considerarse por sí mismo como deployment del endpoint.

---

## 10. Canary / online comparison

Cuando el riesgo lo justifique:

```text
Champion  ── majority traffic
Challenger ─ smaller traffic
```

Usar traffic splitting del serving endpoint cuando corresponda.

Definir previamente:

```text
duration/decision rule
quality metrics
latency
error rate
business metric
rollback condition
```

No elegir 90/10 o una hora como regla universal.

---

## 11. Shadow evaluation

Cuando no se quiera afectar decisiones del usuario:

evaluar shadow prediction.

```text
production request
      ↓
Champion → user
      └→ Challenger → observation only
```

Implementar sólo si la arquitectura permite hacerlo de forma segura y económicamente razonable.

---

## 12. Unity AI Gateway

Para model services expuestos:

evaluar Unity AI Gateway para:

```text
EXECUTE access
traffic policies
usage
cost
rate limits
inference logging
provider abstraction
```

Para GenAI/model APIs, Gateway debe ser una consideración central del deployment.

---

## 13. Inference tables

Habilitar cuando exista un objetivo claro:

```text
debugging
quality monitoring
compliance
future evaluation datasets
```

Revisar privacidad antes de persistir payloads.

---

## 14. Rollback

### Batch

Reasignar alias puede ser suficiente para próximas ejecuciones.

### Real-time

```text
previous known-good version
       ↓
update endpoint config
       ↓
validate endpoint
```

No asumir rollback instantáneo.

---

## 15. Separate model rollback from data rollback

Promover un modelo puede estar acompañado de:

```text
feature changes
schema changes
preprocessing changes
```

Un rollback del artifact puede no ser suficiente.

Registrar dependencies.

---

## 16. Deployment job

Orquestar mediante Lakeflow Jobs / MLflow 3 deployment workflow cuando corresponda.

Stages posibles:

```text
validate artifact
evaluate
register
approval when required
deploy
verify
monitor
```

---

## 17. CI/CD source control

Versionar:

```text
training code
evaluation code
deployment code
environment
Bundle definitions
```

Utilizar Declarative Automation Bundles cuando formen parte del workflow de deployment.

---

## 18. Human approval

No forzar approval manual.

Añadirlo cuando el riesgo requiera:

- regulatory review;
- model risk management;
- financial impact;
- high-impact decision.

---

## 19. Audit evidence

Registrar:

```text
candidate
baseline
metrics
datasets
approval
deployment
endpoint config
timestamp
identity
rollback target
```

---

## 20. GenAI/agent gate

Si se promueve un agente y no un modelo tradicional:

invocar `agent-evaluation-workflow`.

No aplicar únicamente métricas de model artifact a un sistema agéntico.

---

# Output

```text
Model:

Deployment:
- batch
- real-time

Candidate:
- model ID/version:
- source run:

Champion:
- ...

Validation:
- quality:
- slices:
- operational:
- governance:

Decision:
- ...

Alias:
- ...

Endpoint:
- ...

Canary:
- ...

AI Gateway:
- ...

Monitoring:
- ...

Rollback:
- ...

Audit:
- ...
```

# Definition of Done

- [ ] Candidate fue identificado explícitamente.
- [ ] Existe baseline/champion.
- [ ] Model signature está disponible.
- [ ] Se validó performance global.
- [ ] Se validaron slices críticas.
- [ ] Se validó entorno operacional.
- [ ] Modelo está registrado en Unity Catalog.
- [ ] Alias refleja lifecycle.
- [ ] Batch vs real-time deployment está diferenciado.
- [ ] Endpoint se actualiza explícitamente cuando aplica.
- [ ] Existe rollback.
- [ ] Se evaluó Unity AI Gateway.
- [ ] Existe monitoring posterior.
- [ ] Deployment tiene audit trail.
- [ ] Documentación está en español.

# Gotchas

- Último run no significa mejor candidate.
- Un alias no actualiza mágicamente un serving endpoint.
- Champion puede cambiar mientras un endpoint continúa sirviendo una versión anterior.
- Offline improvement no garantiza online improvement.
- Rollback del modelo no necesariamente revierte features.
- Un único promedio puede esconder slice regressions.
