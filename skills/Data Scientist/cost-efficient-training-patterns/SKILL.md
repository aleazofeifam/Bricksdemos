---
name: cost-efficient-training-patterns
description: Reduce costo y tiempo de experimentación y entrenamiento ML/AI seleccionando primero la solución de menor complejidad que alcanza el objetivo, y después optimizando datos, modelo, precision, hardware, parallelism, early stopping y checkpointing. Úsala cuando training sea lento, caro, GPU-intensive o exista necesidad de optimizar price/performance.
---

# Cost-Efficient Training Patterns

La mayor optimización de training muchas veces es no entrenar.

# Optimization hierarchy

```text
1. Do we need a model?
2. Do we need a custom model?
3. Do we need fine-tuning?
4. Do we need all the data?
5. Do we need GPU?
6. Do we need multiple GPUs?
7. Then optimize training.
```

---

## 1. Define the economic objective

Registrar:

```text
Current quality:
Target quality:
Current training duration:
Current cost:
Iteration frequency:
Deployment value:
```

No optimizar GPU utilization sin conocer qué resultado importa.

---

## 2. Managed capability gate

Antes de custom training evaluar:

### Structured analytics

```text
Genie Agent
```

### Data AI transformations

```text
AI Functions
```

### General LLM inference

```text
Databricks model APIs
```

### Forecasting

```text
ai_forecast
```

### Existing foundation models

evaluar model APIs antes de fine-tuning.

---

## 3. AI Functions gate

Si el objetivo es:

```text
classify
extract
summarize
translate
mask
forecast
```

comparar:

```text
managed function cost
vs
custom model lifecycle cost
```

Costo de modelo custom incluye:

```text
training
serving
monitoring
retraining
engineering
governance
```

---

## 4. Establish baseline

Crear un baseline barato.

Ejemplos:

```text
heuristic
linear model
small tree model
small foundation model
few-shot prompt
```

No comenzar por el modelo más grande.

---

## 5. Data scaling experiment

Antes de entrenar sobre todo el dataset:

medir learning curve cuando el problema lo permita.

Ejemplo:

```text
10%
25%
50%
100%
```

son ejemplos de experiment design, no porcentajes obligatorios.

Seleccionar tamaños apropiados para el dataset.

---

## 6. Representative sampling

Sampling debe preservar las dimensiones que afectan model quality.

Revisar:

```text
class balance
time
regions
rare cases
long tail
```

No utilizar `.limit()` como sample estadístico.

---

## 7. Early stopping

Utilizar cuando el framework/model lo soporte y exista validation metric confiable.

Definir:

```text
metric
patience
minimum improvement
checkpoint behavior
```

No copiar una patience universal.

---

## 8. Hyperparameter search

No ejecutar grid search indiscriminado.

Preferir estrategias eficientes:

```text
random search
Bayesian optimization
ASHA/successive halving
Ray Tune
framework-specific HPO
```

cuando correspondan.

Parar trials claramente inferiores temprano.

---

## 9. Choose CPU vs GPU

GPU cuando:

```text
deep learning
large neural model
supported high-throughput training
```

CPU puede ser mejor cuando:

```text
small classic model
EDA
preprocessing
low-volume experiment
model does not benefit materially from GPU
```

No mantener una GPU activa para tareas de preparación que pueden ejecutarse en CPU.

---

## 10. AI Runtime accelerator selection

Elegir accelerator por:

```text
model memory
batch
sequence length
precision
training method
parallelism
```

### Smaller accelerator

si el workload cabe y cumple tiempo.

### H100

cuando memory/throughput lo justifique.

### Multi-GPU

sólo cuando una sola GPU no satisface:

```text
memory
time-to-train
model size
```

No distribuir un workload pequeño por defecto.

---

## 11. PEFT before full fine-tuning

Para LLMs evaluar:

```text
LoRA / PEFT
```

antes de full-parameter tuning cuando la calidad esperada pueda alcanzarse.

Beneficios potenciales:

```text
less trainable parameters
less memory
faster iteration
smaller checkpoints
```

Validar contra baseline.

---

## 12. Mixed precision

Evaluar:

```text
BF16
FP16
other supported precision
```

según hardware/model.

Monitorizar:

```text
NaN
overflow
loss instability
quality regression
```

No activar un modo únicamente por velocidad.

---

## 13. Gradient accumulation

Utilizar cuando se necesita effective batch size mayor que el que cabe en memoria.

Entender el tradeoff:

```text
memory ↓
steps/time potentially ↑
```

No confundirlo con compute reduction automática.

---

## 14. Gradient checkpointing

Evaluar cuando memory es el bottleneck.

Tradeoff:

```text
memory ↓
compute ↑
```

Puede permitir modelo/batch mayor.

---

## 15. Distributed training

Elegir técnica según problema.

Conceptualmente:

```text
DDP
→ model fits in each GPU; increase throughput

FSDP
→ model memory needs sharding

DeepSpeed
→ advanced sharding/offload requirements
```

Utilizar ejemplos de AI Runtime compatibles con framework/model actual.

---

## 16. Checkpointing

Guardar con frecuencia suficiente para minimizar expected lost work.

No utilizar:

```text
checkpoint every N steps
```

como valor universal.

Derivar frecuencia de:

```text
run duration
checkpoint size
failure probability
recovery cost
storage cost
```

---

## 17. Track cost per experiment

Registrar:

```text
run
GPU type
GPU count
duration
dataset size
model
quality
```

Derivar:

```text
cost per validated experiment
cost per quality improvement
```

No comparar sólo duración.

---

## 18. MLflow 3

Usar MLflow para comparar:

```text
quality
training time
params
models
datasets
```

y evitar repetir configuraciones fallidas.

---

## 19. Reuse checkpoints

Cuando corresponda:

```text
resume
warm start
transfer learning
PEFT adapters
```

No reiniciar training completo sin necesidad.

---

## 20. Data caching

Para multiple epochs en AI Runtime:

evaluar caching local de datasets cuando la plataforma/documentación vigente lo recomiende y el volumen lo permita.

Mantener source of truth en Unity Catalog.

---

## 21. Serving cost matters too

Una arquitectura de training más barata puede producir un modelo más caro en serving.

Optimizar:

```text
training
+
serving
+
monitoring
+
retraining
```

como lifecycle completo.

---

## 22. Unity AI Gateway

Para foundation-model/API workloads comparar:

```text
build custom
vs
consume governed model service
```

Gateway permite administrar access/usage/cost policies cuando corresponde.

Esto puede evitar training innecesario.

---

## 23. Stop rule

Definir cuándo detener optimización.

Ejemplo:

```text
incremental quality gain
<
cost/complexity threshold
```

No continuar HPO porque todavía existe budget.

---

# Output

```text
Use case:

Baseline:
- model:
- quality:
- cost:
- duration:

Managed alternatives:
- Genie:
- AI Functions:
- model APIs:
- ai_forecast:

Training:
- model:
- data:
- method:

Compute:
- CPU/GPU:
- accelerator:
- GPUs:
- strategy:

Optimizations:
- sampling:
- early stopping:
- PEFT:
- precision:
- HPO:
- checkpoint:

Results:
- quality:
- cost:
- duration:

Cost per improvement:
- ...

Decision:
- ...
```

# Definition of Done

- [ ] Se definió el objetivo económico.
- [ ] Se evaluaron managed alternatives.
- [ ] Existe baseline.
- [ ] Dataset scaling fue evaluado cuando aporta valor.
- [ ] Sampling preserva poblaciones críticas.
- [ ] CPU/GPU está justificado.
- [ ] Accelerator está justificado.
- [ ] Multi-GPU está justificado.
- [ ] PEFT fue evaluado para LLM fine-tuning.
- [ ] Early stopping está vinculado a valid metric.
- [ ] HPO no utiliza brute force sin necesidad.
- [ ] Checkpoint policy está definida.
- [ ] MLflow registra experimentos.
- [ ] Se considera serving cost.
- [ ] Existe stop rule.
- [ ] Documentación está en español.

# Gotchas

- El GPU más rápido no necesariamente es el más barato.
- Training más barato puede producir serving más caro.
- Sample más pequeño puede eliminar rare cases críticos.
- Early stopping sobre una mala validation set optimiza el criterio equivocado.
- Distributed training tiene overhead.
- Mixed precision puede cambiar estabilidad numérica.
- No custom-train una capability que una función administrada resuelve suficientemente.
