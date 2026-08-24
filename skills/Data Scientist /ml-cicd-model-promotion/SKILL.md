---
name: ml-cicd-model-promotion
description: CI/CD para modelos ML — pipeline de promoción staging→prod con validación automática, alias de UC, canary deployment, rollback, y gates de calidad. Úsala cuando necesites automatizar la promoción de modelos sin intervención manual y con garantías de calidad.
---

# ML CI/CD & Model Promotion

Automatiza el lifecycle de modelos: train → validate → promote → canary → full rollout → monitor.

## Promotion Pipeline (Job nocturno)

```python
import mlflow
from mlflow import MlflowClient

client = MlflowClient()
MODEL_NAME = "production.ml.churn_model"
METRIC_THRESHOLD = 0.82  # AUC mínimo
REGRESSION_TOLERANCE = 0.01  # No puede bajar más que 1pp vs champion

# 1. Obtener último run de training
latest_run = mlflow.search_runs(
    experiment_names=["/churn-training"],
    order_by=["start_time DESC"], max_results=1
).iloc[0]

new_auc = latest_run["metrics.val_auc"]
new_version = latest_run["tags.model_version"]

# 2. Comparar contra champion actual
try:
    champion_version = client.get_model_version_by_alias(MODEL_NAME, "champion")
    champion_run = mlflow.get_run(champion_version.run_id)
    champion_auc = champion_run.data.metrics["val_auc"]
except:
    champion_auc = 0  # No hay champion aún

# 3. Gate de calidad
if new_auc >= METRIC_THRESHOLD and new_auc >= champion_auc - REGRESSION_TOLERANCE:
    # Promote!
    client.set_registered_model_alias(MODEL_NAME, "champion", new_version)
    print(f"Promoted v{new_version} (AUC={new_auc:.4f}) over previous (AUC={champion_auc:.4f})")
else:
    print(f"BLOCKED: v{new_version} AUC={new_auc:.4f} < threshold or regression")
```

## Canary Deployment (10% traffic)

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Split traffic: 90% champion, 10% challenger
w.serving_endpoints.update_config("churn-endpoint", served_entities=[
    {"entity_name": MODEL_NAME, "entity_version": champion_v, "traffic_percentage": 90},
    {"entity_name": MODEL_NAME, "entity_version": new_v, "traffic_percentage": 10},
])
# Después de 1h sin degradación: 100% al nuevo
```

## Rollback

```python
# Instantáneo: re-apuntar alias a versión anterior
client.set_registered_model_alias(MODEL_NAME, "champion", previous_version)
# El endpoint detecta el cambio de alias automáticamente (~30s)
```

## Gotchas

* Los "stages" (Staging/Production) están DEPRECADOS en UC. Usar alias (`champion`, `challenger`, `archived`).
* Un alias apunta a UNA sola versión. Para A/B de modelos, usar `traffic_config` del endpoint con 2 served entities.
* El validation job debe correr en el MISMO environment que prod (mismas libs, misma Spark version) para evitar discrepancias.
* El rollback de endpoint tarda ~30s (no instantáneo). Durante ese tiempo, el viejo modelo sigue sirviendo.
* SIEMPRE comparar contra el champion ACTUAL, no contra un threshold fijo. Un modelo puede superar 0.82 pero ser peor que el champion de 0.89.
* Loggear TODAS las decisiones de promoción como MLflow tags para audit trail.
* Para modelos críticos: agregar gate humano (approval en Jira/Slack) entre canary y full rollout.
