---
name: agent-evaluation-workflow
description: Evalúa agentes de IA (chatbots, RAG, tool-calling) de forma sistemática — crea evaluation datasets, define scorers custom, ejecuta mlflow.genai.evaluate(), y compara versiones con gates de calidad. Úsala cuando necesites medir la calidad de un agente antes de desplegarlo o después de cambios.
---

# Agent Evaluation Workflow

Proceso sistemático para evaluar agentes antes de deployment o después de cambios.

## Paso 1: Crear evaluation dataset

```python
import pandas as pd

eval_data = pd.DataFrame([
    {"input": "¿Cuál es la política de devoluciones?",
     "expected_response": "Las devoluciones se aceptan hasta 30 días después de la compra con recibo original.",
     "context": "Artículo 5.2 de la política de la tienda..."},
    {"input": "¿Tienen envío gratis?",
     "expected_response": "Envío gratis en compras superiores a $500 MXN.",
     "context": "Sección de envíos del FAQ..."},
    # Mínimo 20-30 ejemplos para significancia estadística
])
```

## Paso 2: Definir scorers

```python
import mlflow
from mlflow.genai.scorers import Correctness, Safety, RetrievalGroundedness

# Built-in scorers
builtin_scorers = [Correctness(), Safety(), RetrievalGroundedness()]

# Custom scorer
@mlflow.genai.scorer
def domain_accuracy(input, output, expected_response):
    """Verifica que la respuesta contenga los datos clave esperados."""
    key_facts = expected_response.lower().split(". ")
    matches = sum(1 for fact in key_facts if fact in output.lower())
    return matches / len(key_facts) if key_facts else 0.0
```

## Paso 3: Ejecutar evaluación

```python
results = mlflow.genai.evaluate(
    model="endpoints:/support-agent-v2",
    data=eval_data,
    scorers=builtin_scorers + [domain_accuracy]
)

print(f"Correctness: {results.metrics['correctness/mean']:.2%}")
print(f"Safety: {results.metrics['safety/mean']:.2%}")
print(f"Groundedness: {results.metrics['retrieval_groundedness/mean']:.2%}")
```

## Paso 4: Quality gate

```python
GATES = {
    "correctness/mean": 0.80,
    "safety/mean": 0.95,
    "retrieval_groundedness/mean": 0.75
}

passed = all(results.metrics[k] >= v for k, v in GATES.items())
if passed:
    print("✅ PASSED - Ready for deployment")
else:
    failed = {k: results.metrics[k] for k, v in GATES.items() if results.metrics[k] < v}
    print(f"❌ FAILED gates: {failed}")
```

## Gotchas

* Correctness necesita `expected_response` en el dataset. Sin él, el scorer no puede evaluar.
* Safety NO necesita expected — evalúa la respuesta sola contra políticas de seguridad.
* RetrievalGroundedness requiere que el agente tenga trace con retrieval spans. Sin retrieval, retorna N/A.
* LLM-as-judge tiene varianza (~5% entre runs). Correr 3 veces y promediar para decisiones críticas.
* Datasets <20 ejemplos tienen error estadístico MUY alto. Para gates de producción: mínimo 30-50.
* Regression testing: nueva versión debe ser ≥ anterior en TODOS los scorers, no solo promedio global.
* Para agentes con tools: evaluar también tool selection accuracy (¿llamó la herramienta correcta?).
