---
name: model-drift-monitoring-action
description: Monitorea modelos ML en producción separando data drift, prediction drift, performance degradation, concept drift y operational health, y define acciones basadas en impacto en vez de thresholds universales. Úsala para Model Serving, batch inference, detección de degradación, análisis de inference tables, retraining decisions y rollback.
---

# Model Drift Monitoring & Action

Drift es evidencia de cambio.

No es automáticamente evidencia de que un modelo debe ser reentrenado.

# Monitoring layers

```text
1. Endpoint health
2. Input/data drift
3. Prediction drift
4. Ground-truth performance
5. Business performance
6. Model/version behavior
```

---

## 1. Define the model contract

Registrar:

```text
Model:
Owner:
Prediction:
Consumers:
Business decision:
Features:
Serving pattern:
Latency SLO:
Quality metric:
Critical slices:
Ground truth availability:
```

No diseñar monitoring antes de entender cómo se utiliza la predicción.

---

## 2. Establish baseline

Baseline puede ser:

```text
training distribution
validation distribution
recent stable production window
business-defined reference
```

Elegir conscientemente.

No asumir siempre training data.

Training puede no representar producción inicial.

---

## 3. Operational health

Para real-time serving monitorizar:

```text
availability
request rate
error rate
latency
CPU/GPU/memory cuando corresponda
```

Operational health y model quality son dimensiones distintas.

---

## 4. Unity AI Gateway inference tables

Para model services compatibles, evaluar inference tables para capturar:

```text
request
response
latency
status
tags
serving context
```

Esto habilita:

- debugging;
- drift analysis;
- compliance;
- dataset generation.

Revisar privacy y costo antes de habilitar payload logging.

---

## 5. Data drift

Para cada feature crítica identificar tipo:

```text
continuous
categorical
binary
text-derived
embedding
```

Seleccionar estadística apropiada.

Ejemplos:

```text
PSI
KS
Jensen-Shannon
chi-square
population proportions
mean/std
missingness
```

No utilizar PSI para todas las features.

---

## 6. Avoid universal thresholds

No codificar:

```text
PSI > .2 = retrain
```

Calibrar thresholds mediante:

- historical variation;
- impact analysis;
- false-positive tolerance;
- business criticality.

Drift significativo estadísticamente puede ser irrelevante operationally.

---

## 7. Prediction drift

Monitorizar:

```text
prediction distribution
score distribution
class proportions
confidence
abstentions
```

Prediction drift puede aparecer aunque inputs individuales parezcan estables.

---

## 8. Ground-truth performance

Cuando labels llegan posteriormente:

calcular métricas reales.

Ejemplos:

```text
classification:
precision
recall
F1
ROC-AUC
PR-AUC
calibration

regression:
MAE
RMSE
bias

ranking:
NDCG
precision@k
```

La métrica correcta depende de la decisión del negocio.

---

## 9. Label delay

Registrar:

```text
prediction_time
label_available_time
```

No declarar model performance en tiempo real cuando ground truth tarda semanas.

Diseñar dos loops:

```text
fast loop → drift/proxy
slow loop → actual performance
```

---

## 10. Concept drift

Sospechar concept drift cuando:

```text
input distribution similar
+
actual performance degrades
```

No afirmar concept drift únicamente porque cambió PSI.

---

## 11. Data quality before model drift

Antes de culpar al modelo revisar:

```text
schema
NULL
feature pipeline
unit change
timezone
category mapping
source outage
feature freshness
```

Muchos "model drift incidents" son data incidents.

Handoff a Data Engineer cuando corresponda.

---

## 12. Data Quality Monitoring

Evaluar Data Quality Monitoring para tablas relevantes como:

```text
feature tables
input distributions
inference datasets
```

Utilizarlo como complemento a constraints determinísticos.

---

## 13. Slice monitoring

Revisar performance por:

```text
country
product
segment
channel
model route
```

cuando sea estadística y éticamente apropiado.

Un modelo puede mejorar globalmente y deteriorarse en una población crítica.

---

## 14. Action framework

```text
Signal
  ↓
Validate
  ↓
Find root cause
  ↓
Estimate impact
  ↓
Choose action
```

Posibles acciones:

```text
observe
alert
fix data
change threshold
recalibrate
retrain
rollback
disable model
change model
```

No reducir todo a retrain.

---

## 15. Automated retraining gate

Automatizar retraining sólo cuando:

- labels confiables están disponibles;
- pipeline de training es reproducible;
- validation gates existen;
- candidate nunca reemplaza champion sin evaluación;
- data issue fue descartado.

Retrain automático no significa deployment automático.

---

## 16. Rollback

Rollback cuando:

```text
known-good model
+
current version causes material degradation
+
rollback semantics are understood
```

Invocar `ml-cicd-model-promotion`.

---

## 17. GenAI distinction

Si el workload es un:

```text
agent
RAG
LLM application
```

no utilizar PSI como principal monitor de calidad.

Invocar:

`agent-evaluation-workflow`

y utilizar:

- MLflow traces;
- scorers;
- production monitoring;
- Unity AI Gateway.

---

## 18. Unity AI Gateway

Para model/AI services usar Gateway cuando corresponda para observar:

```text
traffic
errors
usage
cost
routing
payloads
```

El Gateway complementa, no sustituye, model-performance monitoring.

---

## 19. Runbook

Para cada alert importante definir:

```text
signal
query/dashboard
owner
diagnostic sequence
decision
recovery
validation
```

---

# Output

```text
Model:
Serving mode:

Baseline:
- ...

Operational health:
- ...

Input drift:
- ...

Prediction drift:
- ...

Ground truth:
- available:
- delay:
- metrics:

Slices:
- ...

Root cause:
- data
- model
- business
- unknown

Action:
- observe
- fix
- retrain
- rollback

AI Gateway:
- ...

Follow-up:
- ...
```

# Definition of Done

- [ ] Existe baseline.
- [ ] Operational health está separado de quality.
- [ ] Se evaluaron inference tables.
- [ ] Drift metrics son apropiadas al tipo de feature.
- [ ] No se usaron thresholds universales sin validación.
- [ ] Se monitorea prediction distribution.
- [ ] Se utiliza ground truth cuando está disponible.
- [ ] Label delay está considerado.
- [ ] Se revisó data quality.
- [ ] Se revisaron slices.
- [ ] Root cause fue investigado antes de retrain.
- [ ] Retraining y deployment están separados.
- [ ] GenAI workloads utilizan agent evaluation.
- [ ] Runbook está documentado en español.

# Gotchas

- Statistical drift no implica business degradation.
- No drift no garantiza buena performance.
- Accuracy sin labels reales es una estimación, no accuracy.
- Un data bug puede parecer concept drift.
- Reentrenar sobre datos corruptos empeora el modelo.
- Production baseline puede ser mejor referencia que training baseline.
