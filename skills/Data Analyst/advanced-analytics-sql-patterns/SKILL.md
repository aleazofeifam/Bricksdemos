---
name: advanced-analytics-sql-patterns
description: Guía análisis avanzados en Databricks SQL para cohortes, retención, funnels, LTV, RFM, segmentación y otras métricas analíticas complejas. Se usa cuando una pregunta de negocio requiere cálculos multietapa, comportamiento temporal o segmentación que supera una agregación SQL básica.
---

# Advanced Analytics SQL Patterns

Resuelve análisis avanzados empezando por la definición de negocio y terminando con un resultado validado y reutilizable.

No comenzar copiando un patrón SQL.

## Workflow

**Pregunta → definición → grain → eventos → SQL → validación → semántica reutilizable**

---

## 1. Discover

Determinar:

- ¿qué intenta decidir el usuario?
- ¿cuál es la población?
- ¿cuál es la unidad de análisis?
- ¿qué evento inicia el análisis?
- ¿qué evento representa éxito o fracaso?
- ¿cuál es el periodo?
- ¿qué exclusiones existen?
- ¿qué dimensiones se necesitan?

Ejemplo:

```text
Pregunta:
¿Cuál es nuestra retención a 90 días?

Antes de escribir SQL definir:
- qué significa "cliente";
- qué significa "activo";
- qué evento inicia el periodo;
- si se mide por calendario o ventanas exactas;
- si una recompra reactiva al cliente.
```

---

## 2. Select the analytical pattern

### Cohortes / Retención

Usar cuando se compara comportamiento desde un evento inicial común.

Definir:

```text
cohort_event
activity_event
cohort_period
observation_period
retention_condition
```

No mezclar cohortes mensuales con ventanas semanales sin hacerlo explícito.

### Funnel

Usar cuando existe una secuencia ordenada de eventos.

Definir:

```text
step_1
step_2
step_3
...
allowed_time_window
event_order
deduplication_rule
```

Nunca considerar que un usuario completó el funnel simplemente porque aparecen todos los eventos si ocurrieron fuera de orden.

### LTV

Definir antes:

- revenue vs margin;
- gross vs net;
- ventana histórica;
- refunds;
- moneda;
- clientes activos/inactivos;
- horizonte observado vs predicho.

### RFM

Definir:

- fecha de referencia;
- ventana;
- evento de compra;
- monetary value;
- población elegible.

Los buckets deben describirse como segmentación relativa, no como categorías universales.

### Churn

No existe una definición universal.

Definir el evento de churn antes de calcularlo.

---

## 3. Inspect the data

Antes de la query final validar:

```sql
-- Validación de granularidad
SELECT
  COUNT(*) AS filas,
  COUNT(DISTINCT customer_id) AS clientes,
  COUNT(DISTINCT order_id) AS pedidos
FROM production.gold.orders;
```

Revisar:

- duplicados;
- timestamps;
- zonas horarias;
- estados;
- registros tardíos;
- cancelaciones;
- NULL;
- keys de joins.

---

## 4. Build incrementally

Construir la lógica por etapas verificables.

Ejemplo para cohortes:

```text
1. identificar primera actividad;
2. asignar cohorte;
3. identificar actividad posterior;
4. calcular periodo relativo;
5. contar población;
6. calcular denominador;
7. calcular ratio.
```

No producir una CTE de cientos de líneas sin poder inspeccionar resultados intermedios.

---

## 5. Validate numerators and denominators

Para cada ratio:

```text
Métrica:
Numerador:
Denominador:
Exclusiones:
Periodo:
Grain:
```

Seleccionar al menos una cohorte/segmento pequeño y calcular manualmente el resultado esperado.

Compararlo contra SQL.

---

## 6. Promote reusable semantics

Después del análisis preguntar:

**¿Esta definición será utilizada nuevamente?**

Si no:

- mantenerla como análisis ad hoc bien documentado.

Si sí:

- verificar si ya existe una Metric View;
- crear o extender una Metric View cuando el KPI sea estable y gobernado;
- documentar definición, owner y dimensiones;
- evitar mantener múltiples versiones del mismo KPI.

---

## 7. Prepare conversational analytics

Si las preguntas forman parte de un patrón recurrente:

Registrar ejemplos como:

```text
¿Cuál fue la retención de la cohorte de enero?
¿Cómo cambia la retención por región?
¿Qué segmento tiene mayor LTV?
¿Dónde perdemos más usuarios en el funnel?
```

Cuando corresponda, incorporar estos patrones al Genie Agent del dominio después de validar la semántica.

---

## AI Functions decision gate

Cuando los datos necesarios sean texto o documentos, comprobar antes si una AI Function resuelve el problema directamente.

Ejemplos:

- clasificación → `ai_classify`
- extracción estructurada → `ai_extract`
- resumen → `ai_summarize`
- masking de entidades → `ai_mask`
- necesidad general sobre un modelo/end-point → evaluar `ai_query`

No construir código Python o una integración LLM personalizada antes de revisar estas alternativas.

Validar resultados de IA con muestras representativas antes de utilizarlos como dimensión o KPI.

---

## Output

```text
Pregunta de negocio:

Definiciones:
- ...

Población:
Grain:
Periodo:

Patrón analítico:
- cohort / funnel / LTV / RFM / otro

Resultado:
- ...

Validaciones realizadas:
- ...

Supuestos:
- ...

Semántica reutilizable:
- sí/no

Metric View:
- existente / recomendada / no aplica

Preguntas candidatas para Genie:
- ...
```

---

## Databricks decision gates

### Metric Views

Aplicable cuando el resultado se convierte en una definición reutilizable.

### Genie Agents

Aplicable cuando el negocio realiza recurrentemente estas preguntas.

### AI Functions

Aplicable cuando el análisis depende de texto, documentos o clasificación/enriquecimiento con IA.

### Spark Declarative Pipelines

No construir pipelines dentro de esta skill. Delegar transformaciones productivas a Data Engineering.

### Lakebase

No forzar.

### Unity AI Gateway

No forzar para análisis SQL estándar.

---

## Definition of Done

- [ ] La pregunta de negocio está definida.
- [ ] El grain está identificado.
- [ ] Numerador y denominador están explícitos cuando aplica.
- [ ] Se revisaron duplicados y joins.
- [ ] Se validó al menos un caso conocido.
- [ ] Los supuestos están documentados.
- [ ] Se comprobó si el KPI ya existe.
- [ ] Se evaluó Metric View si la lógica será reutilizada.
- [ ] Se evaluaron AI Functions si existe información no estructurada.
- [ ] Las explicaciones y comentarios generados están en español.

## Gotchas

- Funnel sin orden temporal no representa conversión.
- Retención depende de la definición de actividad.
- Churn debe definirse antes de calcularse.
- LTV histórico y LTV predicho son métricas diferentes.
- Los percentiles relativos pueden cambiar aunque el comportamiento absoluto no cambie.
- Un query técnicamente correcto puede responder la pregunta de negocio equivocada.
