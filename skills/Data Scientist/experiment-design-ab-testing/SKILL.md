---
name: experiment-design-ab-testing
description: Diseña, valida y analiza experimentos controlados y A/B tests con métricas gobernadas, randomización, power analysis, integrity checks, inferencia estadística y decision rules predefinidas. Úsala para medir causalmente el impacto de una intervención, feature, pricing change, modelo, campaña o experiencia de producto.
---

# Experiment Design & A/B Testing

Un experimento comienza definiendo la decisión, no calculando un p-value.

# Lifecycle

**Question → Estimand → Metrics → Design → Power → Randomize → Validate → Analyze → Decide**

---

## 1. Define the decision

Registrar:

```text
¿Qué cambio se está probando?
¿Qué decisión se tomará con el resultado?
¿Quién se verá afectado?
¿Cuál es el costo de false positive?
¿Cuál es el costo de false negative?
```

---

## 2. Define hypothesis

Ejemplo:

```text
Intervention:
Nuevo ranking de recomendaciones.

Population:
Usuarios activos elegibles.

Primary outcome:
Conversión por usuario dentro de ventana definida.
```

Evitar:

```text
"queremos ver si mejora"
```

---

## 3. Define the estimand

Especificar:

```text
population
treatment
control
outcome
time window
unit
```

Ejemplo:

```text
ATE sobre usuarios elegibles
durante 14 días
```

El estimand evita cambiar la pregunta después de observar resultados.

---

## 4. Define primary metric

Una métrica primary debe corresponder directamente a la hipótesis.

Antes del experimento:

- revisar definición;
- owner;
- grain;
- filtros;
- temporalidad.

Si existe una Metric View, reutilizarla.

Si el KPI es empresarial y reusable pero no existe semántica gobernada, hacer handoff a `semantic-layer-strategy`.

---

## 5. Define guardrail metrics

Ejemplos:

```text
revenue
latency
refunds
cancellations
customer complaints
retention
```

El experimento puede mejorar primary metric y ser perjudicial globalmente.

---

## 6. Define assignment unit

Ejemplos:

```text
user
account
store
region
session
device
```

La unidad debe minimizar contamination/interference.

No randomizar sesiones si el tratamiento persiste a nivel usuario.

---

## 7. Check interference

Preguntar:

```text
¿un tratamiento de A afecta a B?
```

Ejemplos:

```text
social network
marketplace
shared inventory
pricing
sales teams
```

Si sí, considerar:

- cluster randomization;
- geo experiment;
- switchback;
- otro diseño.

---

## 8. Power analysis

Definir:

```text
baseline
minimum detectable effect
variance
alpha/error control
power
allocation
```

Utilizar librerías estadísticas probadas o métodos establecidos.

No mantener una fórmula simplificada universal dentro del skill.

El MDE debe ser económicamente significativo, no escogido para reducir sample size.

---

## 9. Pre-register decision rules

Antes de iniciar definir:

```text
primary metric
secondary metrics
guardrails
experiment horizon
minimum sample requirements
stopping rule
exclusion criteria
multiple-testing strategy
```

Esto limita researcher degrees of freedom.

---

## 10. Deterministic assignment

La asignación debe ser:

```text
stable
auditable
reproducible
```

Puede utilizarse hashing cuando el diseño lo permita.

Ejemplo conceptual:

```sql
CASE
  WHEN pmod(hash(user_id, :experiment_salt), 10000) < :control_cutoff
    THEN 'control'
  ELSE 'treatment'
END
```

Validar que el mismo usuario no cambie de variante accidentalmente.

---

## 11. Exposure logging

Separar:

```text
assignment
```

de:

```text
actual exposure
```

Registrar:

```text
assigned_at
exposed_at
variant
experiment_id
unit_id
```

No asumir que asignado = tratado.

---

## 12. Sample-ratio mismatch

Antes de estudiar outcomes revisar:

```text
expected allocation
vs
observed allocation
```

Un SRM puede indicar:

- instrumentation bug;
- assignment bug;
- exclusion bias;
- pipeline problem.

No interpretar causalmente el resultado hasta investigarlo.

---

## 13. Invariant checks

Comparar características pre-treatment que no deberían cambiar.

Ejemplos:

```text
historical activity
pre-period revenue
country
tenure
```

Grandes desequilibrios pueden señalar problemas de randomización o implementación.

---

## 14. Peeking

No ejecutar repeated fixed-horizon tests y detener cuando `p < .05`.

Si el negocio necesita continuous monitoring, utilizar un diseño secuencial apropiado.

El método debe definirse antes del análisis.

---

## 15. Estimate effect

Reportar:

```text
control mean/rate
treatment mean/rate
absolute effect
relative effect
confidence/credible interval
uncertainty
```

No reportar sólo p-value.

---

## 16. Practical significance

Distinguir:

```text
statistically detectable
```

de:

```text
worth deploying
```

Comparar con MDE/business threshold.

---

## 17. Multiple metrics

Para múltiples hipótesis definir un método de error control apropiado.

No aplicar Bonferroni automáticamente a cualquier dashboard de métricas.

Distinguir:

```text
primary hypothesis
guardrails
exploratory metrics
```

---

## 18. Variance reduction

Evaluar técnicas como:

```text
CUPED
stratification
covariate adjustment
```

cuando cumplen supuestos.

Medir cuánto reducen varianza en ese experimento.

No asumir un porcentaje de mejora.

---

## 19. Heterogeneous effects

Después del análisis primary, investigar segmentos predefinidos o exploratorios.

Etiquetar claramente análisis exploratorios.

Evitar cherry-picking de segmentos.

---

## 20. ai_top_drivers gate

Cuando exista un cambio real en una métrica y se quiera entender qué dimensiones contribuyen:

evaluar `ai_top_drivers` cuando esté disponible.

Úsalo como:

```text
diagnóstico/exploración
```

no como prueba causal del tratamiento.

La causalidad proviene del diseño experimental.

---

## 21. Model experiment

Si el A/B compara modelos:

coordinar con:

`ml-cicd-model-promotion`

y registrar:

```text
model version
endpoint route
exposure
prediction
outcome
```

---

## 22. Decision

Ejemplo:

```text
SHIP
- meaningful primary improvement
- guardrails acceptable

DO NOT SHIP
- degradation
- insufficient value

CONTINUE / NEW EXPERIMENT
- uncertainty remains
```

No interpretar “not significant” como evidencia de igualdad.

---

## Output

```text
Experiment:

Decision:
- ...

Hypothesis:
- ...

Estimand:
- ...

Population:
Unit:
Treatment:
Control:

Primary metric:
- definition:
- Metric View:

Guardrails:
- ...

Power:
- baseline:
- MDE:
- assumptions:

Assignment:
- ...

Integrity:
- SRM:
- invariant checks:

Results:
- control:
- treatment:
- absolute effect:
- relative effect:
- uncertainty:

Segments:
- ...

Decision:
- ...

Follow-up:
- ...
```

# Definition of Done

- [ ] La decisión está definida.
- [ ] Existe estimand.
- [ ] Primary metric está gobernada.
- [ ] Se revisó Metric View.
- [ ] Existen guardrails.
- [ ] Assignment unit está definida.
- [ ] Se revisó interference.
- [ ] Existe power analysis.
- [ ] Stopping rule fue definido antes del resultado.
- [ ] Assignment es reproducible.
- [ ] Exposure está registrado.
- [ ] Se revisó SRM.
- [ ] Se revisaron invariants.
- [ ] Se reporta effect size y uncertainty.
- [ ] Practical significance está considerada.
- [ ] Exploratory findings están diferenciados.
- [ ] Documentación está en español.

# Gotchas

- `p < 0.05` no mide importancia económica.
- No significativo no significa equivalente.
- Assignment no significa exposure.
- Peeking invalida un fixed-horizon test convencional.
- Segment analysis post-hoc puede crear falsos descubrimientos.
- `ai_top_drivers` ayuda a explicar diferencias; no establece causalidad.
