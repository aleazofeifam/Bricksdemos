---
name: model-drift-monitoring-action
description: Monitorea drift de modelos ML en producción — feature drift (PSI/KS test), prediction drift, y concept drift (degradación de accuracy). Define thresholds y acciones automáticas (alertar, re-train, rollback). Úsala cuando un modelo en serving necesite vigilancia continua.
---

# Model Drift Monitoring & Automated Actions

Detecta degradación de modelos en producción y actúa automáticamente.

## Paso 1: Habilitar inference logging

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Activar inference table en el endpoint
w.serving_endpoints.update_config("churn-endpoint",
    auto_capture_config={"enabled": True,
        "catalog_name": "production", "schema_name": "ml",
        "table_name_prefix": "churn_inference"})
```

## Paso 2: Calcular PSI diario

```sql
-- Population Stability Index: comparar distribución actual vs baseline
WITH baseline AS (
  SELECT feature_1, NTILE(10) OVER (ORDER BY feature_1) AS bin
  FROM production.ml.training_data
),
current AS (
  SELECT feature_1, NTILE(10) OVER (ORDER BY feature_1) AS bin
  FROM production.ml.churn_inference_payload
  WHERE date >= CURRENT_DATE() - 1
),
psi AS (
  SELECT
    SUM((curr_pct - base_pct) * LN(curr_pct / base_pct)) AS psi_score
  FROM (
    SELECT bin, COUNT(*)/SUM(COUNT(*)) OVER() AS base_pct FROM baseline GROUP BY bin
  ) b JOIN (
    SELECT bin, COUNT(*)/SUM(COUNT(*)) OVER() AS curr_pct FROM current GROUP BY bin
  ) c USING (bin)
)
SELECT psi_score,
  CASE WHEN psi_score < 0.1 THEN 'OK'
       WHEN psi_score < 0.2 THEN 'WARNING'
       ELSE 'DRIFT_DETECTED' END AS status
FROM psi
```

## Acciones automáticas

| PSI Score | Estado | Acción |
|-----------|--------|--------|
| < 0.1 | OK | Nada |
| 0.1 - 0.2 | Warning | Alert a Slack |
| > 0.2 | Drift | Trigger retrain job |
| Accuracy < SLA por 3 días | Critical | Rollback a versión anterior |

## Gotchas

* PSI es sensible al número de bins. Usar 10 bins quantile-based (no fixed-width).
* KS test no funciona bien con distribuciones multimodales. Usar chi-squared para categóricas.
* Feature drift SIN accuracy drop = OK (el modelo es robusto). NO re-entrenar innecesariamente.
* Accuracy drop SIN feature drift = posible concept shift o data labeling issue.
* Lakehouse Monitor con `InferenceLog` profile_type requiere columnas `model_id`, `prediction`, `timestamp`.
* La inference table tiene lag de ~5 minutos. No usar para alertas real-time.
* Comparar SIEMPRE contra el baseline de training, no contra el día anterior (evita drift gradual invisible).
