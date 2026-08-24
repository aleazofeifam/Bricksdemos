---
name: experiment-design-ab-testing
description: Diseña y evalúa A/B tests y experimentos controlados en Databricks — cálculo de tamaño de muestra, randomización determinista, análisis de significancia estadística, y reporting de resultados. Úsala cuando el usuario necesite validar una hipótesis con datos experimentales o evaluar el impacto de un cambio.
---

# A/B Test Design & Analysis

Workflow completo para diseñar, ejecutar y analizar experimentos controlados en Databricks.

## Paso 1: Power Analysis (tamaño de muestra)

```python
from scipy import stats
import numpy as np

def sample_size_proportions(baseline_rate, mde, alpha=0.05, power=0.80):
    """Calcula N por grupo para test de proporciones."""
    effect_size = mde / np.sqrt(baseline_rate * (1 - baseline_rate))
    analysis = stats.norm.ppf(1 - alpha/2) + stats.norm.ppf(power)
    n = (analysis / effect_size) ** 2
    return int(np.ceil(n))

# Ejemplo: baseline conversion 5%, quiero detectar +1pp
n = sample_size_proportions(0.05, 0.01)
print(f"Necesitas {n:,} usuarios por grupo")  # ~7,850
```

## Paso 2: Randomización determinista

```sql
-- Asignación estable con hash (no cambia entre runs)
SELECT
  user_id,
  CASE WHEN ABS(HASH(user_id, 'experiment_v2_2026')) % 100 < 50
       THEN 'control' ELSE 'treatment' END AS variant
FROM users
WHERE signup_date < '2026-08-01'  -- Solo usuarios pre-existentes
```

## Paso 3: Análisis de resultados

```python
from scipy.stats import chi2_contingency, norm
import pandas as pd

# Cargar resultados
results = spark.sql("""
  SELECT variant, COUNT(*) AS n,
    COUNT_IF(converted) AS conversions,
    COUNT_IF(converted) / COUNT(*) AS rate
  FROM experiment_results
  WHERE experiment = 'rec_model_v2'
  GROUP BY variant
""").toPandas()

control = results[results.variant == 'control'].iloc[0]
treatment = results[results.variant == 'treatment'].iloc[0]

# Z-test para proporciones
p_pool = (control.conversions + treatment.conversions) / (control.n + treatment.n)
se = np.sqrt(p_pool * (1 - p_pool) * (1/control.n + 1/treatment.n))
z_stat = (treatment.rate - control.rate) / se
p_value = 2 * (1 - norm.cdf(abs(z_stat)))
lift = (treatment.rate - control.rate) / control.rate

print(f"Lift: {lift:.2%}, p-value: {p_value:.4f}")
print(f"{'SIGNIFICATIVO' if p_value < 0.05 else 'NO significativo'}")
```

## Gotchas

* NO usar `random()` para asignar grupo — no es determinista entre runs. Usar `HASH(user_id, salt)` que es estable.
* El "peeking problem" (mirar resultados antes de completar N) infla falsos positivos. Decidir horizon ANTES de empezar.
* Para métricas con alta varianza (revenue), usar CUPED: restar la métrica pre-experimento como covariable para reducir varianza ~30-40%.
* Validar balance: los grupos deben tener N similar y distribuciones similares de covariables (age, tenure). Si no están balanceados, hay sesgo.
* Novelty effect: las primeras 48h pueden mostrar lift artificial. Excluir los primeros 2 días del análisis.
* Network effects: si usuarios interactúan entre sí (social), el SUTVA assumption se viola. Usar cluster randomization.
* Multiple testing: si evaluas 5 métricas, ajustar alpha con Bonferroni (alpha/5) o usar FDR.
