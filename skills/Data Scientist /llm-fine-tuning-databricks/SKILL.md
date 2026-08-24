---
name: llm-fine-tuning-databricks
description: Fine-tuning de LLMs en Databricks — preparación de datos en formato instrucción, Foundation Model Fine-tuning API, evaluación post-fine-tune, y serving del modelo adaptado. Úsala cuando el modelo base no sea suficiente para el dominio del cliente y necesite adaptación específica.
---

# LLM Fine-Tuning on Databricks

Workflow para adaptar un LLM a un dominio específico usando la Foundation Model Fine-tuning API.

## Paso 1: Preparar dataset

```python
import json

# Formato requerido: lista de conversaciones
training_data = [
    {"messages": [
        {"role": "system", "content": "Eres un clasificador de tickets de soporte."},
        {"role": "user", "content": "Mi tarjeta fue clonada y hay cargos que no reconozco"},
        {"role": "assistant", "content": "fraude"}
    ]},
    {"messages": [
        {"role": "system", "content": "Eres un clasificador de tickets de soporte."},
        {"role": "user", "content": "No puedo iniciar sesión en la app"},
        {"role": "assistant", "content": "acceso"}
    ]}
]

# Guardar como JSONL en UC Volume
with open("/Volumes/ml/training/tickets/train.jsonl", "w") as f:
    for item in training_data:
        f.write(json.dumps(item) + "\n")
```

## Paso 2: Lanzar fine-tuning

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

run = w.fine_tuning.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    train_data_path="dbfs:/Volumes/ml/training/tickets/train.jsonl",
    register_to="ml.models.ticket_classifier",
    training_duration="5ep",  # 5 epochs
    learning_rate="5e-5"
)
print(f"Fine-tuning run: {run.name}")
```

## Paso 3: Evaluar vs base model

```python
import mlflow

# Comparar fine-tuned vs base en test set
results = mlflow.genai.evaluate(
    model="endpoints:/ticket-classifier-ft",
    data=eval_dataset,  # DataFrame con input + expected_response
    scorers=[mlflow.genai.scorers.Correctness()]
)
print(f"Fine-tuned accuracy: {results.metrics['correctness/mean']:.2%}")
```

## Gotchas

* El dataset DEBE tener columna `messages` con formato OpenAI (lista de dicts con role/content). Otro formato falla silenciosamente.
* Mínimo ~100 ejemplos para mejora visible, ~1000 para dominio específico. Con <50, overfitting casi seguro.
* Fine-tuning NO cambia el tokenizer. Si necesitas vocabulario nuevo (ej: códigos internos), mejor usar RAG + few-shot en vez de fine-tune.
* Costo: puede ser >$100/epoch en modelos grandes. Empezar con 8B para validar approach antes de escalar a 70B.
* SIEMPRE incluir base model como baseline en evaluación. Si el fine-tuned no mejora measurablemente, descartar.
* El fine-tuning tarda 1-4 horas para datasets pequeños. No hay feedback en tiempo real — monitorear el run status.
* Para español: los modelos multilingual (Llama 3.1, Mixtral) funcionan bien. Los English-only (algunos GPT-J) degradan.
* Evaluation split: NUNCA evaluar con datos de training. Separar 20% como test set ANTES de fine-tune.
