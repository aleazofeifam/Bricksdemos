---
name: cost-efficient-training-patterns
description: Estrategias para reducir costo de entrenamiento ML — early stopping, progressive resizing, spot instances, gradient accumulation, mixed precision, y data sampling inteligente. Úsala cuando el presupuesto de training sea limitado o el modelo tarde demasiado en entrenar.
---

# Cost-Efficient ML Training Patterns

Reduce costos de entrenamiento sin sacrificar calidad del modelo.

## Estrategia progresiva (recomendada)

1. **Sample 10%** → validar approach (< 5 min)
2. **Early stopping** → no quemar epochs innecesarios
3. **Full data** solo si sample muestra mejora con más datos
4. **Spot instances** para jobs no-críticos

## Implementación

```python
from sklearn.model_selection import learning_curve
import numpy as np

# 1. Learning curve: ¿más datos ayudan?
train_sizes, train_scores, val_scores = learning_curve(
    model, X_sample, y_sample,
    train_sizes=[0.1, 0.3, 0.5, 0.7, 1.0],
    cv=3, scoring='roc_auc'
)
# Si val_score se estabiliza antes de 100% → no necesitas todos los datos

# 2. Early stopping (XGBoost ejemplo)
import xgboost as xgb
model = xgb.XGBClassifier(
    n_estimators=1000,  # Alto, pero con early stopping
    early_stopping_rounds=50,
    eval_metric='auc'
)
model.fit(X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False)
print(f"Stopped at {model.best_iteration} iterations (de 1000)")
```

## Cluster config para cost savings

```yaml
# Job cluster con spot instances (DAB)
resources:
  jobs:
    training_job:
      job_clusters:
        - job_cluster_key: training
          new_cluster:
            spark_version: "15.4.x-gpu-ml-scala2.12"
            node_type_id: "g5.xlarge"
            num_workers: 4
            aws_attributes:
              first_on_demand: 1  # Driver on-demand, workers spot
              availability: SPOT_WITH_FALLBACK
              spot_bid_price_percent: 100
```

## Gotchas

* Early stopping en distributed training requiere sync de métrica entre workers. Usar callback de framework.
* Mixed precision (fp16/bf16) da ~2x speedup pero puede causar NaN en gradientes. Usar gradient scaling.
* Spot instances pueden interrumpirse mid-epoch. Checkpoint obligatorio cada N steps.
* `first_on_demand: 1` = driver estable + workers spot. Si driver es spot y se interrumpe, TODO el job falla.
* Gradient accumulation simula batch size grande sin más RAM pero alarga tiempo por epoch (tradeoff).
* Para tablas >100GB: usar Delta `TABLESAMPLE` para exploración, no `.limit()` (limit no es random).
* En Databricks: la forma más simple de spot es en job clusters (no all-purpose). All-purpose no soporta spot workers fácilmente.
