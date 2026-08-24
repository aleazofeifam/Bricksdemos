---
name: sql-performance-troubleshooting
description: Diagnostica y corrige consultas lentas en Databricks SQL mediante medición reproducible, Query Profile, análisis de scans, joins, shuffles, cardinalidad y layout físico. Se usa cuando una query, dashboard o workload SQL incumple su objetivo de latencia, costo o estabilidad.
---

# SQL Performance Troubleshooting

Optimiza mediante evidencia.

Nunca comenzar aplicando `OPTIMIZE`, aumentando warehouse size o materializando una tabla sin identificar primero el bottleneck.

## Workflow

**Baseline → Profile → Hypothesis → Change → Re-measure → Keep/Revert**

---

## 1. Establish the baseline

Registrar:

```text
Query:
Consumer:
Warehouse:
Tiempo observado:
Objetivo:
Filas retornadas:
Frecuencia:
Parámetros:
Cache state:
Costo/importancia:
```

Ejecutar una medición reproducible.

Evitar comparar una ejecución cacheada contra una no cacheada.

---

## 2. Open Query Profile

Inspeccionar:

- top operators;
- filas procesadas;
- filas producidas;
- scans;
- joins;
- cardinalidad;
- shuffles;
- memory;
- spill;
- execution time;
- performance insights.

Buscar primero dónde se consume el tiempo.

No optimizar basándose únicamente en el texto SQL.

---

## 3. Classify the bottleneck

### Excessive scan

Investigar:

- filtros;
- partition/data skipping behavior;
- layout;
- columnas innecesarias;
- rango temporal.

### Join explosion

Comparar cardinalidad antes y después del join.

Validar:

- keys;
- duplicados;
- many-to-many;
- grain.

### Shuffle / aggregation

Revisar:

- cardinalidad de `GROUP BY`;
- joins;
- sorts;
- ventanas;
- agregaciones tempranas.

### Spill

Determinar si el problema es:

- query shape;
- cardinalidad;
- skew;
- volumen legítimo;
- capacidad de compute.

No aumentar compute antes de revisar la query.

### Repeated expensive transformation

Evaluar:

- materialized view;
- tabla curada;
- simplificación upstream;
- metric view materialization cuando aplique.

---

## 4. Check physical optimization

Para Unity Catalog managed tables:

1. revisar si predictive optimization está habilitado;
2. revisar automatic liquid clustering cuando sea aplicable;
3. revisar workload real;
4. sólo después considerar ajustes manuales.

No seleccionar clustering keys exclusivamente por intuición.

---

## 5. Check semantic duplication

Si muchos dashboards ejecutan variaciones de la misma lógica:

No limitar el análisis a optimizar cada query.

Preguntar:

- ¿debería existir una Metric View?
- ¿debería existir una materialización compartida?
- ¿existe una transformación repetida que pertenece upstream?

---

## 6. Use Genie Code as accelerator

Cuando Query Profile ofrece una recomendación accionable, Genie Code puede ayudar a:

- reescribir la consulta;
- explicar un bottleneck;
- proponer cambios.

Revisar siempre el cambio antes de aceptarlo.

No asumir que una query reescrita conserva automáticamente la misma semántica.

---

## 7. Change one thing at a time

Ejemplo:

```text
Baseline:
18.4 s

Hipótesis:
join multiplica cardinalidad.

Cambio:
deduplicar dimensión antes del join.

Resultado:
5.2 s

Correctness:
igual al resultado esperado.

Decisión:
mantener.
```

Evitar modificar simultáneamente:

- warehouse;
- query;
- clustering;
- materialización;

porque después no será posible atribuir la mejora.

---

## 8. Validate correctness after optimization

Performance no puede cambiar el resultado.

Comparar:

- row count;
- aggregates;
- NULL;
- duplicates;
- known test cases.

Cuando sea posible, comparar automáticamente la versión anterior y la nueva.

---

## Output

```text
Baseline:

Query Profile:
- bottleneck:

Hipótesis:

Cambio:

Resultado posterior:

Mejora:

Validación funcional:

Decisión:
- keep
- revert
- investigate further

Siguiente bottleneck:
- ...
```

---

## Databricks decision gates

### Query Profile

Core.

### Predictive Optimization / Automatic Liquid Clustering

Revisar antes de introducir optimizaciones físicas manuales.

### Genie Code

Aplicable como acelerador de diagnóstico y reescritura.

### Materialized Views

Aplicables cuando existe cálculo costoso reutilizado.

### Metric Views

Aplicables cuando el problema incluye duplicación semántica, no como arreglo genérico de performance.

### Spark Declarative Pipelines

Si el verdadero fix pertenece upstream, delegar a Data Engineering.

### Genie Agents

No forzar.

### Lakebase

No forzar.

### AI Functions

No forzar salvo que el bottleneck sea específicamente un workload de AI Functions.

### Unity AI Gateway

No forzar.

---

## Definition of Done

- [ ] Existe baseline reproducible.
- [ ] Se inspeccionó Query Profile.
- [ ] Se identificó una hipótesis.
- [ ] Se aplicó un cambio controlado.
- [ ] Se volvió a medir.
- [ ] Se comprobó correctness.
- [ ] Se documentó keep/revert.
- [ ] Se evaluaron optimizaciones automáticas antes de manuales.
- [ ] No se utilizaron thresholds arbitrarios como regla universal.
- [ ] La explicación está documentada en español.

## Gotchas

- Una query cacheada puede invalidar una comparación.
- Un join correcto sintácticamente puede provocar explosión de cardinalidad.
- Más compute puede ocultar una query incorrectamente diseñada.
- La materialización puede reducir latencia pero introducir costo y frescura.
- Optimizar performance sin validar resultados puede producir una query rápidamente incorrecta.
