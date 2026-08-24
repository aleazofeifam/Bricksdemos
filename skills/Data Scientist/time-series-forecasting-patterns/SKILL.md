---
name: time-series-forecasting-patterns
description: Diseña y valida forecasting de series temporales en Databricks comenzando con ai_forecast como baseline administrado y escalando a modelos clásicos o custom sólo cuando backtesting y requisitos del negocio lo justifican. Úsala para demanda, revenue, capacity, inventory, traffic, staffing u otras predicciones temporales.
---

# Time Series Forecasting Patterns

Forecasting comienza definiendo la decisión y el horizonte.

No escogiendo Prophet.

# Lifecycle

**Decision → Series → Baseline → Backtest → Compare → Operationalize → Monitor**

---

## 1. Define the decision

Preguntar:

```text
¿Qué decisión usa el forecast?
¿Con qué anticipación?
¿Cada cuánto se actualiza?
¿Qué costo tiene overforecast?
¿Qué costo tiene underforecast?
```

El horizon debe venir del proceso de decisión.

---

## 2. Define series

Registrar:

```text
Time column:
Target:
Frequency:
Groups:
History:
Missing periods:
Known future covariates:
Past-only covariates:
Holidays:
Non-negative requirement:
Hierarchy:
```

---

## 3. Validate target semantics

Antes de forecasting verificar:

```text
¿Qué significa revenue/demand/etc.?
¿Es gross o net?
¿Qué timezone?
¿Qué currency?
¿Qué estados se incluyen?
```

Si la métrica tiene definición empresarial reutilizable:

evaluar Metric View con `semantic-layer-strategy`.

El forecast no debe entrenarse sobre un KPI ambiguo.

---

## 4. Build a temporal spine

Detectar:

```text
missing dates
duplicate periods
irregular frequency
timezone shifts
```

No tratar ausencia de registro como valor cero automáticamente.

Determinar con negocio si significa:

```text
0
missing
closed
unknown
```

---

## 5. Temporal split only

Nunca utilizar random split convencional sobre series temporales.

Usar:

```text
train → past
validation/test → future
```

Para robustez considerar rolling-origin backtesting.

---

## 6. Establish naive baselines

Antes de cualquier modelo comparar contra:

```text
last value
seasonal naive
moving average
business baseline
```

Un modelo complejo debe superar un baseline razonable.

---

# Default: ai_forecast

Evaluar `ai_forecast` como primera alternativa cuando se encuentre disponible.

Utilizar la versión recomendada actual según la plataforma.

Ejemplo conceptual:

```sql
SELECT *
FROM ai_forecast(
    TABLE(
        SELECT
            event_date,
            revenue,
            region,
            marketing_spend
        FROM production.analytics.daily_revenue
    ),
    horizon => '30 days',
    time_col => 'event_date',
    value_col => 'revenue',
    group_col => 'region',
    covariate_col => 'marketing_spend',
    holiday_region => 'US',
    positive_only => true,
    version => '2'
);
```

Adaptar parámetros a la sintaxis vigente y al caso.

No copiar este ejemplo literalmente sin revisar requisitos actuales.

---

## 7. ai_forecast capabilities

Evaluar cuando corresponda:

```text
group_col
covariates
holidays
prediction intervals
positive forecasts
multiple metrics
```

No añadir covariates que no estarán disponibles en el futuro.

---

## 8. Backtest ai_forecast

Tratarlo como cualquier otro modelo.

Ejecutar:

```text
historical cutoff 1
historical cutoff 2
historical cutoff 3
...
```

Calcular métricas.

---

## 9. Select error metric

Según el caso:

```text
MAE
RMSE
WAPE
MAPE
sMAPE
pinball loss
business-weighted cost
```

No utilizar MAPE automáticamente cuando existen valores cercanos a cero.

---

## 10. Business loss

Cuando underforecast y overforecast tienen costos diferentes:

crear una métrica de negocio.

Ejemplo:

```text
underforecast inventory cost
> overforecast holding cost
```

Puede ser más relevante que RMSE.

---

# Escalation gate

Escalar a modelos custom sólo cuando:

```text
baseline insufficient
ai_forecast insufficient
special constraints
custom interpretability requirement
domain model requirement
research requirement
```

---

## 11. Classical/custom approaches

Posibles alternativas:

```text
ETS
ARIMA/SARIMA
Prophet
StatsForecast
gradient boosting with lag features
deep learning
domain-specific models
```

No utilizar Prophet como segundo paso universal.

---

## 12. Multiple series

Para miles de series evaluar:

```text
global model
grouped ai_forecast
distributed classical models
hierarchical forecasting
```

No crear un Python model por SKU automáticamente.

Muchas series pueden ser demasiado sparsely observed para ese patrón.

---

## 13. Intermittent demand

Detectar:

```text
many zeros
sporadic events
```

No aplicar un forecasting general sin considerar métodos apropiados para intermittent demand.

---

## 14. Hierarchies

Si existe:

```text
company
→ region
→ store
→ SKU
```

determinar si los forecasts deben reconciliar entre niveles.

No aceptar resultados donde totals parent no coincidan con children si el negocio requiere coherencia.

---

## 15. AI Runtime gate

Para forecasting custom que requiera:

- GPU;
- deep learning;
- large-scale training;

evaluar AI Runtime.

No utilizar GPU para un workload que un SQL function o modelo CPU resuelve adecuadamente.

---

## 16. MLflow

Para custom forecasting registrar:

```text
training window
horizon
frequency
features
model
params
metrics
backtests
```

Comparar modelos mediante MLflow.

---

## 17. Operationalize

Si el forecast debe producirse recurrentemente:

crear un pipeline productivo.

Para preparación/transformación recurrente:

hacer handoff a Data Engineer y favorecer Spark Declarative Pipelines.

No dejar forecast productivo como notebook manual.

---

## 18. Store forecasts

Persistir:

```text
forecast_generated_at
forecast_for_time
group
prediction
lower/upper interval cuando existe
model/version
```

Esto permite evaluar forecasts históricos después de recibir actuals.

---

## 19. Monitor forecast quality

Después de que llegan actuals:

```text
forecast
vs
actual
```

por:

```text
horizon
group
time
business segment
```

No evaluar sólo un error agregado.

---

## 20. Genie

Si usuarios de negocio deben consultar:

```text
forecast
actual
variance
drivers
```

preparar metadata y semántica para Genie.

Preguntas candidatas:

```text
¿Cuál es el forecast de ventas del próximo mes?
¿Qué regiones tienen mayor riesgo de quedar bajo target?
¿Dónde está aumentando el error del forecast?
```

No hacer que Genie calcule una predicción ad hoc si existe un forecast oficial persistido.

---

## 21. Lakebase gate

Si una aplicación operacional necesita consumir/modificar forecasts con:

```text
low-latency reads
transactional adjustments
human overrides
workflow state
```

evaluar Lakebase como parte de la application architecture.

No utilizar Lakebase como almacén analítico primario del entrenamiento.

---

# Output

```text
Decision:

Series:
- time:
- target:
- groups:
- frequency:

Horizon:

Baseline:
- naive:
- ai_forecast:

Backtesting:
- ...

Metrics:
- statistical:
- business:

Selected approach:
- ...

Covariates:
- ...

Operationalization:
- ...

Monitoring:
- ...

Genie:
- ...

Known limitations:
- ...
```

# Definition of Done

- [ ] La decisión de negocio está definida.
- [ ] Horizon proviene del negocio.
- [ ] Target tiene semántica clara.
- [ ] Se revisó Metric View cuando aplica.
- [ ] Frecuencia y gaps están entendidos.
- [ ] Existe naive baseline.
- [ ] Se evaluó ai_forecast.
- [ ] Se realizó backtesting temporal.
- [ ] Se seleccionó métrica apropiada.
- [ ] Se consideró business loss.
- [ ] Custom model tiene justificación si se utilizó.
- [ ] Forecasts productivos están versionados/persistidos.
- [ ] Existe monitoring de forecast vs actual.
- [ ] Pipeline recurrente está operationalized.
- [ ] Metadata está documentada en español.

# Gotchas

- Más historia no siempre significa mejor forecast.
- Más horizonte no es automáticamente malo; depende de señal y decisión.
- Missing period no significa cero.
- Covariate futura debe estar disponible en el momento de inferencia.
- Mejor RMSE no necesariamente significa mejor decisión.
- No sustituir backtesting por fit sobre todo el histórico.
