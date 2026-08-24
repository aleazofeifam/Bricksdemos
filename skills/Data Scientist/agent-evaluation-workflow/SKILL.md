---
name: agent-evaluation-workflow
description: Evalúa sistemáticamente aplicaciones GenAI, agentes, RAG, tool-calling y sistemas multiagente mediante MLflow 3, traces, evaluation datasets, scorers, human feedback y regression gates. Úsala al comparar versiones de un agente, validar cambios de prompts/modelos/tools/retrieval, investigar fallos de calidad, preparar un deployment o establecer monitoring continuo en producción.
---

# Agent Evaluation Workflow

Evalúa agentes como sistemas, no solamente como generadores de texto.

Un agente puede producir una respuesta aparentemente correcta utilizando:

- la herramienta equivocada;
- datos incorrectos;
- una secuencia innecesariamente costosa;
- permisos incorrectos;
- demasiados pasos;
- una respuesta no grounded;
- un MCP incorrecto;
- un modelo innecesariamente caro.

Por eso la evaluación debe observar tanto el resultado final como el trace.

# Core lifecycle

**Define → Trace → Curate → Score → Compare → Diagnose → Improve → Monitor**

---

## 1. Classify the application first

Antes de crear un evaluation dataset clasificar qué se está evaluando.

```text
Structured analytics Q&A
→ evaluar primero si Genie Agent es el producto correcto

Document/knowledge Q&A
→ RAG / Knowledge Assistant / custom agent

Single LLM workflow
→ prompt/model application

Tool-calling agent
→ agent + tools

Multi-agent
→ supervisor + specialized agents

MCP-based system
→ agent + MCP services/tools
```

No construir un custom agent para resolver una necesidad de structured analytics que un Genie Agent puede resolver de forma nativa.

---

## 2. Genie Agent decision gate

Si la necesidad principal es:

```text
"preguntar sobre tablas"
"consultar KPIs"
"analizar ventas"
"explorar datos estructurados"
```

evaluar primero:

- calidad de metadata;
- Metric Views;
- sample questions;
- benchmark de Genie;
- dominio del Genie Agent.

Hacer handoff a:

- `self-service-analytics-enablement`
- `semantic-layer-strategy`

Esta skill puede seguir utilizándose si Genie forma parte de un sistema mayor, por ejemplo:

```text
Supervisor Agent
       ↓
Genie Agent
       ↓
SQL
```

En ese caso evaluar también si el supervisor seleccionó correctamente Genie.

---

## 3. Define success before collecting examples

Identificar:

```text
User:
Goal:
Business outcome:
Critical failures:
Expected behavior:
Forbidden behavior:
Latency requirement:
Cost sensitivity:
Security requirement:
```

Después definir dimensiones de evaluación.

---

# Evaluation dimensions

No todas las aplicaciones necesitan todos los scorers.

## Response quality

Ejemplos:

```text
correctness
relevance
completeness
style
instruction adherence
```

## Retrieval quality

```text
retrieval relevance
retrieval sufficiency
groundedness
citation correctness
```

## Tool quality

```text
tool selection
tool arguments
tool result usage
unnecessary tool calls
failed tool handling
```

## Agent behavior

```text
planning quality
number of steps
loop detection
handoff correctness
termination
```

## Safety/governance

```text
unsafe output
PII exposure
permission bypass
prompt injection
forbidden tool invocation
```

## Operational

```text
latency
token usage
cost
error rate
tool latency
```

No crear una única métrica compuesta que esconda fallos críticos.

---

## 4. Instrument tracing first

Utilizar MLflow Tracing para capturar:

```text
input
output
LLM calls
retrieval
tool calls
MCP calls
agent handoffs
latency
errors
```

El trace debe permitir responder:

```text
¿Qué hizo el agente?
¿Por qué llegó a esa respuesta?
¿Qué tool utilizó?
¿Qué modelo utilizó?
¿Dónde falló?
```

No depender únicamente de logs manuales.

---

## 5. Build the evaluation dataset

Preferir MLflow Evaluation Datasets gobernados cuando el proyecto lo permita.

Fuentes posibles:

```text
known-good examples
historical user questions
production traces
support incidents
domain-expert examples
adversarial cases
synthetic cases
```

La mejor fuente para madurar un agente suele ser una mezcla.

---

## 6. Build a golden set

El golden set debe contener casos cuyo comportamiento esperado sea importante y relativamente estable.

Ejemplo conceptual:

```python
evaluation_examples = [
    {
        "inputs": {
            "question": "¿Cuál es nuestra política vigente de devoluciones?"
        },
        "expected": {
            "expected_response": "...",
            "expected_facts": [
                "...",
                "..."
            ]
        }
    }
]
```

No limitar el benchmark al happy path.

---

## 7. Add slices

Etiquetar casos por dimensiones relevantes:

```text
intent
language
country
customer type
complexity
tool required
retrieval required
sensitivity
adversarial
multi-turn
```

Ejemplo:

```text
slice = Spanish
slice = tool_required
slice = sensitive
```

El promedio global puede ocultar un fallo grave en una población importante.

---

## 8. Include production failures

Cuando aparezca un fallo real:

```text
production trace
      ↓
root cause
      ↓
add to evaluation dataset
      ↓
fix
      ↓
regression test forever
```

Los incidentes importantes deben convertirse en tests permanentes cuando sea razonable.

---

## 9. Select scorers consciously

Ejemplo:

```python
from mlflow.genai import evaluate
from mlflow.genai.scorers import (
    Correctness,
    Safety,
    RetrievalGroundedness,
    RetrievalRelevance,
    RetrievalSufficiency,
)

scorers = [
    Correctness(),
    Safety(),
    RetrievalGroundedness(),
    RetrievalRelevance(),
    RetrievalSufficiency(),
]
```

Usar únicamente scorers que correspondan a la arquitectura.

Por ejemplo:

```text
no retrieval
→ RetrievalGroundedness no aplica
```

---

## 10. Custom scorers

Crear scorer custom cuando exista un requisito verificable específico del dominio.

Ejemplos:

```text
incluye disclaimer regulatorio
usa solamente tool autorizada
devuelve JSON válido
respeta catálogo permitido
calcula campo obligatorio
```

Preferir código determinístico cuando la regla sea determinística.

Utilizar LLM judge cuando el criterio requiera interpretación semántica.

No usar un LLM judge para comprobar algo que puede verificarse con:

```python
assert
regex
schema
exact match
SQL
```

---

## 11. Human feedback

Para criterios donde un domain expert es la referencia:

crear labeling workflows.

Ejemplos:

```text
medical appropriateness
legal interpretation
brand tone
financial explanation
business correctness
```

Utilizar feedback humano para:

- encontrar errores;
- construir ground truth;
- calibrar judges;
- identificar dimensiones no contempladas.

---

## 12. Run evaluation

Ejemplo conceptual:

```python
from mlflow.genai import evaluate

result = evaluate(
    data=eval_dataset,
    predict_fn=agent,
    scorers=scorers,
)
```

Mantener el mismo evaluation dataset cuando se comparan versiones.

No cambiar simultáneamente benchmark y sistema y después afirmar que mejoró.

---

## 13. Compare candidate vs baseline

Comparar:

```text
candidate
vs
current production/baseline
```

Por:

- scorer;
- slice;
- critical cases;
- latency;
- cost;
- tool behavior.

No exigir que el candidate gane literalmente cada caso.

Decidir según:

```text
critical regressions
expected improvements
tradeoffs
business impact
```

---

## 14. Define release gates

Los gates deben derivarse de riesgo.

Ejemplo conceptual:

```yaml
release_gate:

  critical:
    safety_regressions: 0
    unauthorized_tool_calls: 0

  quality:
    correctness:
      must_not_regress_materially: true

  operations:
    latency:
      within_product_slo: true
```

No copiar thresholds universales entre agentes.

---

## 15. Diagnose failures from traces

Clasificar el root cause:

```text
MODEL
PROMPT
RETRIEVAL
CONTEXT
TOOL SELECTION
TOOL RESULT
MCP
SEMANTICS
PERMISSION
DATA
ORCHESTRATION
```

No corregir todos los fallos agregando instrucciones al system prompt.

---

# Corrective hierarchy

Preferir:

```text
1. arreglar source/data
2. arreglar semantic definition
3. arreglar retrieval/tool
4. arreglar orchestration
5. agregar structured instruction
6. cambiar prompt
7. cambiar model
8. fine-tune
```

Fine-tuning no debe ser el primer fix.

---

## 16. Unity AI Gateway

Para agentes productivos, evaluar Unity AI Gateway como capa de gobierno para:

```text
model services
model provider services
MCP servers
tools
agents
```

Utilizarlo cuando aplique para:

- access control;
- credential management;
- traffic routing;
- usage monitoring;
- spend controls;
- rate/service policies.

No colocar credenciales de proveedores directamente dentro del agente si Gateway puede administrarlas.

---

## 17. MCP evaluation

Cuando el agente utiliza MCP:

evaluar:

```text
¿seleccionó el MCP correcto?
¿seleccionó la tool correcta?
¿los argumentos eran correctos?
¿tenía permiso?
¿utilizó el output correctamente?
¿ejecutó tools innecesarias?
```

La respuesta final puede ser correcta mientras el comportamiento intermedio sea inseguro.

---

## 18. Production monitoring

Reutilizar los scorers validados en desarrollo para evaluar traces productivos cuando MLflow production monitoring aplique.

Definir:

```text
sampling
scorers
cost budget
alert conditions
review process
```

No evaluar 100% del tráfico automáticamente sin considerar costo y necesidad.

---

## 19. Feedback loop

```text
production
    ↓
traces
    ↓
scorers + human feedback
    ↓
failure clusters
    ↓
evaluation dataset
    ↓
fix
    ↓
release evaluation
```

La evaluación debe ser un producto vivo.

---

## 20. Documentation language

Todo:

- custom scorer;
- comentario;
- docstring;
- análisis;
- reporte;
- explicación del benchmark

debe quedar documentado en español salvo solicitud explícita contraria.

Los nombres técnicos de APIs y objetos no deben traducirse.

---

# Output

```text
Aplicación:

Tipo:
- Genie
- RAG
- custom agent
- tool-calling
- multi-agent

Business objective:

Architecture:
- models:
- retrieval:
- tools:
- MCPs:
- Genie:

Evaluation dimensions:
- ...

Evaluation dataset:
- sources:
- slices:
- golden cases:

Scorers:
- ...

Human feedback:
- ...

Baseline:

Candidate:

Results:
- aggregate:
- slices:
- critical failures:

Latency/cost:
- ...

Release decision:
- pass
- conditional
- fail

Root causes:
- ...

Recommended changes:
- ...

Production monitoring:
- ...
```

# Definition of Done

- [ ] Se clasificó el tipo de aplicación.
- [ ] Se evaluó Genie si el problema es structured analytics.
- [ ] Existe definición de éxito.
- [ ] El agente está traced.
- [ ] Existe evaluation dataset.
- [ ] El dataset incluye casos reales cuando están disponibles.
- [ ] Existen edge/adversarial cases.
- [ ] Se definieron slices.
- [ ] Los scorers corresponden a la arquitectura.
- [ ] Reglas determinísticas utilizan scorers determinísticos cuando corresponde.
- [ ] Se comparó candidate vs baseline.
- [ ] Se revisaron critical regressions.
- [ ] Se revisó tool/MCP behavior cuando aplica.
- [ ] Se evaluó Unity AI Gateway.
- [ ] Existe production feedback loop cuando aplica.
- [ ] Todo quedó documentado en español.

# Gotchas

- Una respuesta correcta no significa que el agente se comportó correctamente.
- Un promedio alto puede esconder un fallo regulatorio crítico.
- Más ejemplos no garantizan mejor cobertura.
- Synthetic evaluation no sustituye indefinitely a production traces.
- LLM judges no deben utilizarse para reglas que pueden verificarse determinísticamente.
- No arreglar problemas de datos mediante prompt engineering.
- Fine-tuning no es el primer mecanismo de remediación.
