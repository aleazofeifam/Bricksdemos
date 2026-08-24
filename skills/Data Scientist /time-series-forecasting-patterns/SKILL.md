---
name: time-series-forecasting-patterns
description: Pronósticos de series temporales en Databricks — ai_forecast para quick wins, Prophet/statsforecast para modelos clásicos, y distributed forecasting con pandas UDF para miles de series. Úsala para demanda, ventas, tráfico, o cualquier predicción temporal.
---

# Time Series Forecasting Patterns

Estrategia por complejidad: ai_forecast → Prophet → Distributed forecasting.

## Quick Win: ai_forecast (SQL)

```sql
SELECT * FROM ai_forecast(
  TABLE(SELECT date, revenue FROM production.gold.daily_revenue),
  horizon => 30,
  frequency => 'D'
);
```

## Distributed: 2000 series con Prophet

```python
from prophet import Prophet
import pandas as pd

def forecast_series(pdf: pd.DataFrame) -> pd.DataFrame:
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    model.fit(pdf[['ds', 'y']])
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    forecast['sku_id'] = pdf['sku_id'].iloc[0]
    return forecast[['sku_id', 'ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(30)

schema = "sku_id string, ds date, yhat double, yhat_lower double, yhat_upper double"
forecasts = (spark.table("production.gold.daily_sales")
    .groupBy("sku_id")
    .applyInPandas(forecast_series, schema=schema))
forecasts.write.mode("overwrite").saveAsTable("production.ml.forecasts")
```

## Gotchas

* ai_forecast requiere tabla con EXACTAMENTE date + value columns. Más columnas → error.
* Prophet necesita columnas nombradas `ds` y `y` exactamente (no `date`, no `revenue`).
* Para distribución: usar `applyInPandas()` con schema explícito (NO `pandas_udf` con iterator para forecasting).
* Series con <30 puntos históricos NO deben modelarse (ruido domina señal). Filtrar antes.
* Split temporal: NUNCA split aleatorio en time series. Siempre train=pasado, test=futuro.
* Forecast horizon > 30% del historial disponible → resultados poco confiables.
* Estacionalidad múltiple (weekly + yearly) es default en Prophet pero NO en statsforecast — activar explícitamente.
* Materializar forecasts en Delta: re-invocar el modelo cada query es lento y caro.
