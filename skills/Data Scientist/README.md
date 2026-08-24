# Data Scientist Skills

## Propósito

Esta carpeta contiene las skills de la persona **Data Scientist**. El objetivo no es entrenar modelos por defecto, sino elegir la solución de menor complejidad que alcanza el resultado requerido y mantener un lifecycle reproducible, evaluable y gobernado.

El sistema cubre ML clásico, forecasting y GenAI. Para GenAI, el patrón central es:

```text
¿Existe capability administrada?
        ↓
¿Existe modelo base suficiente?
        ↓
¿Prompt/retrieval/tools resuelven?
        ↓
Evaluar
        ↓
Sólo después considerar fine-tuning
```

## Lifecycle

```text
Problema
   ↓
Definir outcome y baseline
   ↓
Elegir solución de menor complejidad
   ├── Genie Agent
   ├── AI Functions
   ├── ai_forecast
   ├── Foundation/model service
   └── Custom ML
        ↓
Experimentar con MLflow 3
        ↓
Evaluar
        ↓
Registrar / reproducir
        ↓
Promover
        ↓
Servir
        ↓
Unity AI Gateway cuando aplica
        ↓
Monitorear
        ↓
Feedback / retraining / rollback
```

## Estado final del sistema

| Skill | Para qué sirve | Cuándo usarla |
|---|---|---|
| `agent-evaluation-workflow` | Evalúa agentes, RAG, tool-calling y sistemas multiagente con traces/scorers | Antes de deployment, después de cambios o ante fallos de calidad |
| `llm-fine-tuning-databricks` | Decide si realmente hace falta fine-tuning y usa AI Runtime cuando sí | Cuando prompting/retrieval/model choice no alcanzan |
| `ml-cicd-model-promotion` | Promueve modelos candidate → challenger → champion | Para batch o real-time serving con gates y rollback |
| `model-drift-monitoring-action` | Separa drift, performance y operational health | Para modelos productivos que necesitan vigilancia |
| `experiment-design-ab-testing` | Diseña experimentos controlados e inferencia causal | Para evaluar features, pricing, campañas o modelos |
| `reproducibility-environment-pinning` | Hace experimentos auditables y reproducibles | Cuando resultados deben recrearse o promoverse |
| `time-series-forecasting-patterns` | Diseña forecasting con baseline → ai_forecast → custom si hace falta | Para demanda, ventas, capacity, inventory o tráfico |
| `cost-efficient-training-patterns` | Minimiza costo del lifecycle de entrenamiento | Cuando training es caro, lento o GPU-intensive |

## Cómo funciona el sistema

### Decision funnel para GenAI

```text
¿Es structured analytics?
        ├── Sí → Genie Agent / Data Analyst
        ↓ No
¿Es una transformación acotada de IA?
        ├── Sí → AI Functions
        ↓ No
¿Un foundation model actual alcanza?
        ├── Sí → model service
        ↓ No
¿Prompt/few-shot alcanza?
        ├── Sí → mantener simple
        ↓ No
¿Retrieval/tools resuelven?
        ├── Sí → RAG / agent
        ↓ No
¿Hay evidencia de gap?
        └── Sí → fine-tuning
```

### Lifecycle de un modelo clásico

```text
Experiment
  ↓
reproducibility-environment-pinning
  ↓
MLflow 3
  ↓
ml-cicd-model-promotion
  ↓
Serving
  ↓
model-drift-monitoring-action
```

## Principios globales

1. **La mejor optimización de training puede ser no entrenar.**
2. **Genie se evalúa primero para structured analytics.**
3. **AI Functions se evalúan primero para tareas acotadas como clasificación, extracción, resumen o masking.**
4. **Fine-tuning no es una base de conocimiento.**
5. **AI Runtime reemplaza Foundation Model Fine-tuning legacy para nuevos workflows.**
6. **Todo candidate necesita baseline y evaluation dataset.**
7. **MLflow 3 es el backbone de experimentación, tracing, evaluation y lifecycle.**
8. **Unity AI Gateway se evalúa para model services, agents, MCPs y tools productivos.**
9. **Drift no significa automáticamente retrain.**
10. **Todo código, comentarios, docstrings y documentación generados deben estar en español.**

## Ejemplos de uso

### Ejemplo 1 — ¿Necesito fine-tuning?

**Skill**

```text
llm-fine-tuning-databricks
```

**Prompt sugerido**

```text
Tenemos un modelo base que clasifica tickets pero no alcanza la calidad deseada.

Antes de proponer fine-tuning:
1. evalúa AI Functions;
2. evalúa otro foundation model;
3. evalúa prompting/few-shot;
4. evalúa retrieval/tools si el problema es conocimiento;
5. establece baseline y benchmark.

Sólo si queda un gap demostrado, diseña un experimento de fine-tuning con AI Runtime.
```

---

### Ejemplo 2 — Evaluar un agente con tools

**Skill**

```text
agent-evaluation-workflow
```

**Prompt sugerido**

```text
Evalúa este agente de soporte.

No evalúes sólo la respuesta final.
Incluye:
- tool selection;
- argumentos;
- groundedness;
- safety;
- latency;
- cost;
- unnecessary tool calls;
- failure handling.

Construye un evaluation dataset con casos reales, edge cases y slices.
```

---

### Ejemplo 3 — Forecast de demanda

**Skill**

```text
time-series-forecasting-patterns
```

**Prompt sugerido**

```text
Necesito forecast semanal de demanda por SKU.

Primero define:
- decisión;
- horizon;
- frequency;
- missing periods;
- hierarchy;
- business loss.

Compara naive baseline contra ai_forecast con backtesting.
Sólo propone un modelo custom si demuestra mejora material.
```

---

### Ejemplo 4 — Drift en producción

**Skill**

```text
model-drift-monitoring-action
```

**Prompt sugerido**

```text
Detectamos un cambio fuerte en la distribución de features.

No hagas retraining automáticamente.
Primero separa:
- data drift;
- prediction drift;
- data quality issue;
- actual performance;
- operational health.

Determina root cause e impacto antes de seleccionar una acción.
```

## Handoffs a otras personas

| Señal | Handoff |
|---|---|
| El problema es preguntas sobre structured data | Data Analyst / Genie |
| Faltan pipelines/features confiables | Data Engineer |
| Hay problemas de access, classification, retention o AI governance | Data Governance |
| Aparece KPI reusable | Data Analyst / Metric Views |

## Cargar estas skills dentro de Databricks

> **PLACEHOLDER — reemplazar esta sección con el procedimiento validado para su workspace.**

El GIF debe enseñar cómo cargar la carpeta `Data Scientist`, confirmar que las ocho skills fueron detectadas y ejecutar un prompt que active una skill.

### Flujo que debería mostrar el GIF

1. Abrir el entorno de Databricks que administra Agent Skills.
2. Importar/agregar la carpeta `Data Scientist`.
3. Confirmar detección de los ocho `SKILL.md`.
4. Abrir `agent-evaluation-workflow`.
5. Ejecutar un prompt de evaluación.
6. Mostrar que el agente utiliza la skill.

### Placeholder para el GIF

```markdown
![Cómo cargar las skills de Data Scientist en Databricks](./assets/load-data-scientist-skills-databricks.gif)
```

> Reemplazar por la ruta definitiva del GIF.

### Prueba mínima sugerida

```text
Tengo un agente RAG con tools y quiero comparar la versión actual
contra un nuevo modelo antes de producción.
```

La skill esperada es:

```text
agent-evaluation-workflow
```

## Qué NO debe hacer esta persona

- Fine-tunear un modelo sólo porque existe training data.
- Usar training loss como criterio de éxito.
- Construir un custom agent para structured analytics sin evaluar Genie.
- Reentrenar automáticamente por cualquier señal de drift.
- Promover el último run sin compararlo contra champion/baseline.
- Confundir cambiar un alias con desplegar automáticamente un real-time endpoint.
- Construir una infraestructura GPU compleja sin demostrar necesidad.

## Resultado esperado

```text
problema correcto
+
baseline
+
solución mínima viable
+
experimentación reproducible
+
evaluación
+
deployment gobernado
+
monitoring
+
feedback loop
```
