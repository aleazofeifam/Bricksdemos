# Data Analyst Skills

## Propósito

Esta carpeta contiene las skills de la persona **Data Analyst**. El objetivo del sistema no es generar SQL aislado, sino ayudar al analista a convertir una pregunta de negocio en una respuesta **correcta, gobernada, reutilizable y consumible** por usuarios humanos o por experiencias conversacionales como Genie Agents.

El lifecycle de Data Analyst parte de una pregunta real del negocio y termina en una de varias formas de consumo: análisis ad hoc, Metric View, Genie Agent, dashboard o reporte programado.

## Lifecycle

```text
Pregunta de negocio
        ↓
Definir intención y audiencia
        ↓
Identificar KPIs y semántica oficial
        ↓
¿Existe Metric View?
   ├── Sí → reutilizar
   └── No → evaluar si debe crearse
        ↓
Preparar metadata business-friendly
        ↓
Elegir patrón de análisis
        ↓
Validar SQL / resultados / grain
        ↓
Elegir forma de consumo
   ├── Genie Agent
   ├── Dashboard
   ├── Reporting
   └── Análisis ad hoc
        ↓
Benchmark / validación
        ↓
Publicar y observar uso
```

## Estado final del sistema

El bloque de Data Analyst quedó diseñado alrededor de ocho skills:

| Skill | Para qué sirve | Cuándo usarla |
|---|---|---|
| `self-service-analytics-enablement` | Convierte un dominio de datos en una experiencia de autoservicio gobernada | Cuando negocio depende de Data para cada pregunta o se quiere habilitar Genie |
| `semantic-layer-strategy` | Decide dónde deben vivir KPIs, medidas y lógica semántica reusable | Cuando hay definiciones inconsistentes entre dashboards, SQL o equipos |
| `advanced-analytics-sql-patterns` | Guía análisis complejos como cohortes, funnels, LTV, RFM o churn | Cuando una pregunta supera una agregación SQL básica |
| `cross-source-federation-analyst` | Decide cuándo consultar datos externos in-place y cuándo ingerirlos | Cuando el análisis cruza Lakehouse + bases externas |
| `dashboard-storytelling-design` | Convierte métricas en una experiencia visual orientada a decisiones | Cuando los datos existen pero no está claro cómo presentarlos |
| `parameterized-reporting-templates` | Diseña reporting reusable sin duplicar dashboards o queries | Cuando distintas audiencias necesitan variantes del mismo reporte |
| `sql-performance-troubleshooting` | Diagnostica SQL lento con baseline → profile → hipótesis → cambio → medición | Cuando un dashboard/query incumple latencia o costo esperado |
| `window-functions-masterclass` | Diseña y valida cálculos analíticos con contexto entre filas | Para rolling metrics, ranking, LAG/LEAD, sessionization y acumulados |

## Cómo funciona el sistema

Las skills no son un menú para cargar todas a la vez. Funcionan como unidades especializadas que pueden encadenarse.

### Flujo de routing recomendado

```text
¿La pregunta es de autoservicio / lenguaje natural?
        ↓
self-service-analytics-enablement
        ↓
¿Hay KPI reusable?
        ↓
semantic-layer-strategy
        ↓
¿Hace falta análisis avanzado?
        ↓
advanced-analytics-sql-patterns
        ↓
¿El resultado debe visualizarse?
        ↓
dashboard-storytelling-design
```

Otro flujo:

```text
Datos externos
    ↓
cross-source-federation-analyst
    ↓
¿Se vuelve consumo recurrente?
    ↓
Handoff a Data Engineer
    ↓
Ingestión / SDP
```

## Principios globales

1. **La pregunta de negocio va antes que el SQL.**
2. **No inventar KPIs.** Verificar definiciones existentes y ownership.
3. **Metric Views son el default para KPIs estables y reutilizables cuando aplica.**
4. **Genie Agent es la interfaz conversacional preferida para preguntas recurrentes sobre datos estructurados cuando el dominio está preparado.**
5. **Metadata de tablas y columnas debe ser comprensible para negocio y agentes.**
6. **No exponer todo el catálogo a Genie.** Seleccionar el mínimo conjunto relevante.
7. **No convertir cada necesidad en un dashboard.**
8. **Todo código, comentarios, docstrings y documentación generados deben estar en español**, salvo solicitud explícita contraria.
9. **No forzar Lakebase, Unity AI Gateway, SDP o AI Functions** si el problema no los necesita.

## Ejemplos de uso

### Ejemplo 1 — Habilitar Genie para ventas

**Situación**

El equipo comercial pregunta constantemente:

- ¿Cuánto vendimos este mes?
- ¿Qué región cayó?
- ¿Cuál es el revenue por producto?
- ¿Cómo vamos contra target?

**Skills**

```text
self-service-analytics-enablement
        ↓
semantic-layer-strategy
```

**Prompt sugerido**

```text
Analiza el dominio de ventas para habilitar self-service analytics.
Primero identifica las preguntas reales del negocio, las tablas relevantes,
los KPIs existentes y si ya existen Metric Views.

Después prepara el dominio para un Genie Agent:
- metadata;
- grain;
- dimensiones;
- KPIs;
- sample questions;
- casos de benchmark.

No inventes definiciones de revenue. Si existen varias, detén la recomendación
y muestra la inconsistencia.
```

---

### Ejemplo 2 — Diseñar un dashboard ejecutivo

**Situación**

Las métricas ya están gobernadas, pero el CFO necesita un dashboard.

**Skills**

```text
dashboard-storytelling-design
```

**Prompt sugerido**

```text
Diseña un AI/BI Dashboard para el CFO.

La decisión principal es entender si estamos cumpliendo el target mensual,
qué regiones explican la desviación y qué productos requieren atención.

Reutiliza Metric Views existentes.
No vuelvas a definir KPIs dentro de los widgets.
Propón narrativa, páginas, filtros, drill-down y preguntas de follow-up
que deberían poder hacerse al Genie Agent del mismo dominio.
```

---

### Ejemplo 3 — SQL lento

**Situación**

Un dashboard tarda demasiado.

**Skill**

```text
sql-performance-troubleshooting
```

**Prompt sugerido**

```text
Diagnostica esta query siguiendo:
baseline → Query Profile → bottleneck → hipótesis → cambio → re-medición.

No recomiendes aumentar compute, clustering o materialización antes
de identificar el bottleneck real.
Valida que cualquier optimización mantenga exactamente la misma semántica.
```

## Handoffs a otras personas

| Señal | Handoff |
|---|---|
| Hace falta construir ingestion o transformación recurrente | Data Engineer |
| Aparece un modelo predictivo o experimentación ML | Data Scientist |
| Hay problemas de clasificación, permisos, ownership o retention | Data Governance |
| Se necesita una base transaccional / operacional | Arquitectura con Lakebase |
| Se necesita gobernar agentes, MCPs, modelos o tools | Data Governance / Unity AI Gateway |

## Cargar estas skills dentro de Databricks

> **PLACEHOLDER — reemplazar esta sección con el procedimiento validado para su workspace.**

El objetivo de esta sección es mostrar cómo cargar las skills de esta carpeta dentro de Databricks para que Genie Code / el entorno de agente pueda descubrirlas y utilizarlas.

### Flujo que debería mostrar el GIF

1. Abrir el entorno de Databricks donde se administran o cargan Agent Skills.
2. Seleccionar la opción para agregar/importar skills.
3. Cargar o apuntar a la carpeta `Data Analyst`.
4. Confirmar que las ocho skills aparecen disponibles.
5. Abrir una de ellas y verificar que `SKILL.md` fue detectado.
6. Ejecutar un prompt de prueba y mostrar cómo el agente selecciona la skill correspondiente.

### Placeholder para el GIF

```markdown
![Cómo cargar las skills de Data Analyst en Databricks](./assets/load-data-analyst-skills-databricks.gif)
```

> Reemplazar `./assets/load-data-analyst-skills-databricks.gif` por la ruta final del GIF cuando esté disponible.

### Prueba mínima sugerida después de cargar

```text
Tengo tablas de ventas en Unity Catalog y quiero habilitar preguntas
en lenguaje natural para el equipo comercial.

Identifica qué debo preparar antes de crear el Genie Agent,
incluyendo metadata, KPIs y Metric Views.
```

La respuesta esperada debe activar principalmente:

```text
self-service-analytics-enablement
```

y, cuando corresponda:

```text
semantic-layer-strategy
```

## Qué NO debe hacer esta persona

- Crear pipelines productivos complejos.
- Definir políticas de retención o compliance.
- Entrenar modelos porque una consulta sea difícil.
- Inventar KPIs.
- Exponer datos sensibles únicamente mediante instrucciones de prompt.
- Usar Lakebase como reemplazo de un Lakehouse analítico.
- Introducir productos Databricks sin un trigger técnico real.

## Resultado esperado

Una interacción correcta de esta persona produce:

```text
preguntas correctas
+
semántica consistente
+
metadata útil
+
SQL validado
+
consumo apropiado
+
self-service gobernado
```

El objetivo final es que el negocio pueda explorar información con menos dependencia del equipo de datos sin sacrificar semántica, seguridad ni confianza.
