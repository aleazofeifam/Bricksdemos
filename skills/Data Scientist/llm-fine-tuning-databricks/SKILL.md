---
name: llm-fine-tuning-databricks
description: Decide si un caso GenAI realmente necesita fine-tuning y, sólo cuando existe evidencia de que prompting, Genie, AI Functions, retrieval o mejores modelos no resuelven el gap, diseña y ejecuta fine-tuning sobre Databricks AI Runtime con MLflow 3 y Unity Catalog. Úsala para adaptación conductual o de dominio de modelos, SFT, LoRA/PEFT o training custom sobre GPU.
---

# LLM Fine-Tuning on Databricks

Fine-tuning es una estrategia de optimización, no el punto de partida.

## Platform rule

No generar nuevos workflows basados en:

```text
Foundation Model Fine-tuning API
databricks_genai fine-tuning
Foundation Model Fine-tuning UI
```

Ese producto está deprecated.

Para nuevos workloads utilizar Databricks AI Runtime y frameworks modernos de entrenamiento.

---

# Decision funnel

Antes de fine-tuning ejecutar:

```text
Problema
   ↓
¿Genie Agent?
   ↓ no
¿AI Function?
   ↓ no
¿better foundation model?
   ↓ no
¿prompt / few-shot?
   ↓ no
¿retrieval / tools?
   ↓ no
¿fine-tuning?
```

No saltar pasos sin justificación.

---

## 1. Genie Agent gate

Si el problema es:

```text
preguntar datos estructurados
consultar KPIs
generar SQL sobre tablas
analytics conversacional
```

no fine-tunear un LLM.

Evaluar:

- metadata;
- Metric Views;
- Genie Agent;
- sample questions;
- benchmark.

Handoff:

- `self-service-analytics-enablement`

---

## 2. AI Functions gate

Si la tarea es:

```text
clasificar texto
extraer entidades
resumir
traducir
masking
sentiment
similarity
document parsing/enrichment
```

evaluar primero las Databricks AI Functions correspondientes.

Ejemplos:

```text
ai_classify
ai_extract
ai_summarize
ai_translate
ai_mask
ai_similarity
ai_query
```

No entrenar un modelo custom para resolver una transformación que una función gestionada ya resuelve con calidad/costo aceptables.

---

## 3. Foundation model gate

Antes de entrenar:

establecer baseline utilizando modelos disponibles mediante Databricks model APIs / Unity AI Gateway.

Comparar al menos candidatos razonables considerando:

```text
quality
latency
cost
context
language
tool capability
reasoning
licensing
```

Fine-tuning de un modelo débil puede ser peor que cambiar al modelo base correcto.

---

## 4. Prompt/few-shot gate

Evaluar:

```text
system instructions
output schema
few-shot examples
structured outputs
tool constraints
```

Crear benchmark antes y después.

No declarar fracaso porque tres prompts manuales no funcionaron.

---

## 5. Retrieval gate

Si el problema es conocimiento privado, actualizado o documental:

evaluar retrieval antes de fine-tuning.

Ejemplos:

```text
AI Search
Knowledge Assistant
RAG
tools
MCP
```

Fine-tuning no es una base de conocimiento actualizable.

---

# Good reasons to fine-tune

Fine-tuning puede justificarse cuando se requiere:

```text
consistent specialized behavior
domain-specific style/format
specialized classification beyond managed alternative
adaptation to domain patterns
lower-cost smaller model reaching required quality
custom task behavior
model research
```

y existe evidencia cuantitativa de un gap.

---

# Bad reasons

No fine-tunear sólo porque:

```text
"tenemos datos propios"
"queremos nuestro propio modelo"
"RAG es complicado"
"el modelo no conoce documentos nuevos"
"queremos evitar escribir un prompt"
```

---

## 6. Define the baseline

Antes de training:

```text
Base model:
Prompt:
Tools:
Retrieval:
Evaluation dataset:
Scorers:
Latency:
Cost:
Quality:
```

Guardar baseline mediante MLflow.

Sin baseline no puede demostrarse que el fine-tuning agregó valor.

---

## 7. Define training objective

Especificar:

```text
Task:
Expected behavior:
Failure modes:
Primary metrics:
Critical slices:
Target improvement:
```

No utilizar “que responda mejor” como objetivo.

---

## 8. Data governance

Antes de entrenar revisar:

```text
data owner
license
PII
sensitive content
retention
consent
copyright
training rights
```

Todo acceso debe estar gobernado mediante Unity Catalog cuando corresponda.

AI Runtime accede a datos mediante Unity Catalog.

---

## 9. Build datasets

Separar al menos conceptualmente:

```text
training
validation
evaluation
```

El evaluation dataset utilizado para release no debe convertirse accidentalmente en training data.

Detectar:

```text
duplicates
near duplicates
leakage
template repetition
label inconsistencies
```

---

## 10. Curate for quality, not volume

La cantidad correcta depende de:

```text
task complexity
model
diversity
label quality
training method
```

No imponer mínimos universales de 100/1000 ejemplos.

Medir learning curves cuando sea viable.

---

## 11. Choose tuning strategy

### LoRA / PEFT

Preferir como primera alternativa cuando:

- reduce memoria;
- reduce parámetros entrenados;
- permite iteración más barata;
- satisface el objetivo.

### Full fine-tuning

Considerar cuando:

- PEFT no alcanza calidad requerida;
- el modelo/workload lo justifica;
- existe compute adecuado;
- el beneficio ha sido demostrado.

### Continued pretraining

Sólo cuando se requiere adaptación profunda de distribución/lenguaje y existe un corpus adecuado.

No confundir continued pretraining con instruction tuning.

---

## 12. Choose AI Runtime compute

Seleccionar GPU por:

```text
model memory
training method
precision
sequence length
batch size
parallelism
```

No elegir H100 simplemente porque es más potente.

Prototipos pequeños pueden utilizar aceleradores menores cuando satisfagan memoria y performance.

Para cargas distribuidas utilizar las capacidades de AI Runtime correspondientes.

---

## 13. Environment

Elegir:

```text
AI environment
```

cuando las librerías preinstaladas sean apropiadas.

Elegir:

```text
Standard environment
```

cuando se necesite control fino de dependencias.

Pinning de dependencias debe coordinarse con:

`reproducibility-environment-pinning`.

---

## 14. Training configuration

Registrar en MLflow:

```text
base model
model revision
dataset
dataset version
training method
learning rate
batch size
effective batch size
epochs/steps
sequence length
precision
seed
libraries
GPU
git commit
```

No colocar valores universales dentro del skill.

---

## 15. Checkpointing

Guardar checkpoints cuando:

- el entrenamiento es costoso;
- puede exceder una sesión;
- existe riesgo de interrupción;
- se necesita recuperación o análisis.

Utilizar Unity Catalog Volumes cuando corresponda.

---

## 16. MLflow tracking

El training debe quedar asociado a MLflow.

Registrar:

```text
metrics
parameters
artifacts
checkpoints
evaluation
model
```

Utilizar MLflow 3 Logged Models cuando el framework/workflow lo soporte.

---

## 17. Evaluate against baseline

Evaluar:

```text
BASE MODEL
vs
FINE-TUNED MODEL
```

sobre el mismo evaluation dataset.

Revisar:

- global performance;
- critical slices;
- regressions;
- safety;
- latency;
- serving cost.

No considerar éxito solamente porque training loss disminuyó.

---

## 18. Overfitting analysis

Buscar:

```text
train ↑
evaluation ↔/↓
```

y degradaciones por slice.

No aumentar epochs automáticamente.

---

## 19. Register in Unity Catalog

Cuando el candidate cumpla los gates:

registrar el modelo mediante MLflow / Models in Unity Catalog.

Incluir:

```text
description
owner
base model
training dataset lineage
evaluation summary
intended use
known limitations
```

Documentar en español.

---

## 20. Serving

Antes de deployment decidir:

```text
batch
real-time
embedded/offline
```

Batch inference puede utilizar `ai_query` cuando corresponda.

Real-time puede utilizar Model Serving.

---

## 21. Unity AI Gateway

Para modelos productivos, evaluar exposición mediante Unity AI Gateway para:

```text
access control
traffic management
usage
inference logging
rate/service policies
cost governance
```

El consumidor no debería conocer credenciales de providers externos.

---

## 22. Inference tables

Cuando exista necesidad de:

- debugging;
- compliance;
- monitoring;
- dataset generation;
- quality analysis;

evaluar Unity AI Gateway inference tables.

No habilitarlas automáticamente si el contenido contiene información que no debe persistirse sin governance adecuada.

---

## 23. Agent evaluation

Si el fine-tuned model forma parte de un agente:

volver a ejecutar `agent-evaluation-workflow`.

Un modelo puede mejorar individualmente y degradar el sistema agéntico.

---

# Output

```text
Use case:

Fine-tuning decision:
- required
- not required
- experiment only

Alternatives evaluated:
- Genie:
- AI Functions:
- model change:
- prompt:
- retrieval:

Baseline:
- ...

Training objective:
- ...

Data:
- source:
- governance:
- split:

Method:
- LoRA/PEFT
- full
- continued pretraining

AI Runtime:
- environment:
- accelerator:
- distribution:

MLflow:
- experiment:
- logged model:

Evaluation:
- baseline:
- candidate:
- slices:
- regressions:

UC registration:
- ...

Serving:
- ...

AI Gateway:
- ...

Known limitations:
- ...
```

# Definition of Done

- [ ] Se evaluó Genie si el problema era structured analytics.
- [ ] Se evaluaron AI Functions.
- [ ] Se evaluó un foundation model apropiado.
- [ ] Se evaluó prompting/few-shot.
- [ ] Se evaluó retrieval cuando existe conocimiento externo.
- [ ] Existe baseline.
- [ ] Existe evaluation dataset separado.
- [ ] Training data está gobernado.
- [ ] La estrategia PEFT/full está justificada.
- [ ] AI Runtime reemplaza Foundation Model Fine-tuning legacy.
- [ ] Dependencias y environment están registrados.
- [ ] Training quedó trazado con MLflow.
- [ ] Candidate fue comparado contra baseline.
- [ ] Se revisaron slices y regresiones.
- [ ] Se evaluó Unity AI Gateway.
- [ ] El modelo quedó documentado en español.

# Gotchas

- Fine-tuning no agrega conocimiento actualizado de forma confiable.
- Training loss no representa business quality.
- Más datos pueden empeorar un dataset mal etiquetado.
- Fine-tuning de un modelo grande puede ser menos eficiente que usar un modelo menor + LoRA.
- Nunca evaluar únicamente sobre training data.
- No utilizar la deprecated Foundation Model Fine-tuning API para nuevos workloads.
