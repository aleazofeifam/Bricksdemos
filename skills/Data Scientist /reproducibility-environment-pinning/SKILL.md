---
name: reproducibility-environment-pinning
description: Garantiza reproducibilidad de experimentos ML — pinning de dependencias, data snapshots con Delta time travel, seed management, y environment specification. Úsala cuando un resultado deba ser exactamente replicable meses después para auditoría o debugging.
---

# ML Reproducibility & Environment Pinning

Workflow para garantizar que cualquier experimento sea replicable en el futuro.

## Checklist de reproducibilidad

```python
import mlflow
import subprocess
import json

with mlflow.start_run(run_name="churn-rf-v3") as run:
    # 1. Pin data version
    data_version = spark.sql(
        "DESCRIBE HISTORY production.ml.features LIMIT 1"
    ).collect()[0].version
    mlflow.log_param("data_version", data_version)
    mlflow.log_param("data_query",
        f"SELECT * FROM production.ml.features VERSION AS OF {data_version}")

    # 2. Pin environment
    pip_freeze = subprocess.check_output(["pip", "freeze"]).decode()
    mlflow.log_text(pip_freeze, "environment/pip_freeze.txt")
    mlflow.log_param("dbr_version", spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion"))

    # 3. Fix ALL seeds
    import numpy as np, random
    SEED = 42
    np.random.seed(SEED)
    random.seed(SEED)
    mlflow.log_param("random_seed", SEED)

    # 4. Train with logging
    mlflow.sklearn.autolog()
    model = RandomForestClassifier(n_estimators=200, random_state=SEED)
    model.fit(X_train, y_train)

    # 5. Tag as reproducible
    mlflow.set_tag("reproducible", "true")
```

## Reproducir un experimento pasado

```python
# Cargar exactamente los mismos datos
old_run = mlflow.get_run("abc123")
data_version = old_run.data.params["data_version"]
df = spark.read.table("production.ml.features").version(int(data_version))

# Recrear environment
pip_freeze = mlflow.artifacts.download_artifacts(
    run_id="abc123", artifact_path="environment/pip_freeze.txt")
# pip install -r pip_freeze.txt
```

## Gotchas

* Delta time travel tiene retention de 30 días por defecto. Extender con `ALTER TABLE SET TBLPROPERTIES ('delta.logRetentionDuration' = '365 days')` si necesitas reproducir >30d.
* `numpy.random.seed()` ≠ `torch.manual_seed()` ≠ `random.seed()`. Fijar los TRES si usas múltiples libs.
* El orden de filas en DataFrames de Spark NO es determinista sin `.sort()`. Siempre ordenar antes de split.
* VACUUM borra versiones anteriores al retention → si necesitas snapshots long-term, DEEP CLONE a otra tabla.
* El cluster DBR version afecta resultados (diferentes versiones de numpy/sklearn internos). Loggear siempre.
* Para PyTorch: también fijar `torch.backends.cudnn.deterministic = True` y `torch.use_deterministic_algorithms(True)`.
