---
name: dashboard-storytelling-design
description: Diseña AI/BI dashboards orientados a decisiones, con jerarquía visual, KPIs gobernados, filtros, drill-down y narrativa analítica. Se usa cuando existen datos y métricas disponibles pero es necesario convertirlos en una experiencia visual clara para ejecutivos, operaciones o usuarios de negocio.
---

# Dashboard Storytelling & Design

Diseña dashboards que ayuden a tomar decisiones.

No comenzar acomodando gráficos.

## Workflow

**Audiencia → decisión → KPIs → narrativa → visualización → interacción → validación**

---

## 1. Discover the decision

Preguntar:

```text
Audiencia:
¿Qué decisión debe tomar?
¿Con qué frecuencia?
¿Qué pregunta debe poder responder en pocos segundos?
¿Qué acción debería tomar cuando algo cambia?
¿Qué detalles necesita investigar después?
```

Un dashboard puede cubrir varias preguntas relacionadas si pertenecen al mismo workflow de decisión.

No imponer "un dashboard = una pregunta".

---

## 2. Validate the semantic layer

Antes del diseño visual:

- identificar KPIs;
- verificar definiciones;
- buscar Metric Views existentes;
- identificar owners;
- validar grain;
- confirmar frescura.

No esconder fórmulas empresariales críticas dentro de cada widget.

Si un KPI se reutiliza, favorecer una definición semántica gobernada.

---

## 3. Build the narrative

Default:

```text
Estado actual
    ↓
Cambio
    ↓
Causa
    ↓
Segmentación
    ↓
Detalle
    ↓
Acción
```

Ejemplo:

```text
Revenue actual
↓
vs target / vs periodo anterior
↓
tendencia
↓
regiones que explican el cambio
↓
productos/clientes relevantes
↓
detalle investigable
```

No añadir una visualización que no contribuya a una decisión o investigación.

---

## 4. Select the visualization by task

### Valor actual

- KPI
- counter

### Cambio en el tiempo

- line chart
- area chart cuando corresponda

### Comparación categórica

- bar chart

### Distribución

- histogram
- box-oriented visualization cuando esté disponible/aplique

### Relación

- scatter plot

### Detalle

- table

### Geografía

- map únicamente si ubicación aporta significado

Evitar seleccionar un gráfico sólo porque resulte visualmente atractivo.

---

## 5. Design the first viewport

Priorizar:

- contexto;
- KPIs importantes;
- variaciones;
- alertas;
- tendencia principal.

El número de widgets depende del caso.

Preferir menor complejidad cuando dos visualizaciones comunican la misma información.

---

## 6. Use titles as analytical context

Evitar:

```text
Revenue Chart
Sales by Region
Table 1
```

Preferir títulos que indiquen claramente:

- medida;
- periodo;
- comparación;
- población.

Los títulos no deben inventar conclusiones que los datos no demuestren.

---

## 7. Design interaction

Determinar conscientemente:

- filtros globales;
- filtros por página;
- parámetros;
- drill-down;
- cross-filtering;
- navegación.

No incluir filtros que no cambien una decisión relevante.

Mantener nombres coherentes con la capa semántica.

---

## 8. Accessibility

No transmitir significado únicamente mediante color.

Revisar:

- contraste;
- legibilidad;
- etiquetas;
- unidades;
- decimales;
- formatos de fecha;
- tamaños relativos;
- consistencia entre páginas.

Evitar asumir universalmente que verde significa positivo o rojo negativo.

---

## 9. Use Genie Code where useful

Cuando Genie Code esté disponible, puede utilizarse para acelerar:

- descubrimiento de datasets;
- creación inicial de visualizaciones;
- filtros;
- layouts;
- páginas;
- refinamiento.

Tratar el resultado como un borrador que debe ser validado.

No delegar a Genie Code:

- la definición oficial del KPI;
- la interpretación final del negocio;
- los criterios de aceptación.

---

## 10. Add conversational exploration

Para dashboards destinados a usuarios de negocio, evaluar el Genie Agent asociado.

Preparar preguntas como:

```text
¿Por qué cayó revenue este mes?
¿Qué regiones explican la diferencia?
¿Cuáles son los diez productos con mayor crecimiento?
¿Existe algún segmento fuera de objetivo?
```

La conversación debe utilizar la misma semántica gobernada que el dashboard.

No permitir que el dashboard y Genie presenten definiciones distintas del mismo KPI.

---

## 11. Validate with users

Probar:

1. mostrar el dashboard sin explicación;
2. preguntar qué entienden;
3. solicitar que encuentren una respuesta concreta;
4. observar dónde dudan;
5. corregir;
6. repetir.

Validar también:

- números;
- filtros;
- performance;
- permisos;
- responsive layout;
- datos vacíos.

---

## Output

```text
Audiencia:
Decisión principal:

KPIs:
- ...

Metric Views:
- ...

Narrativa:
1.
2.
3.

Páginas:
- ...

Interacciones:
- ...

Preguntas para Genie:
- ...

Validaciones:
- ...

Riesgos:
- ...
```

---

## Databricks decision gates

### AI/BI Dashboards

Core.

### Metric Views

Core para KPIs reutilizables.

### Genie Agents

Altamente aplicable para permitir investigación después de observar el dashboard.

### Genie Code

Usar como acelerador de authoring, no como owner de la semántica.

### AI Functions

Aplicables upstream si el dashboard requiere clasificación, extracción o enriquecimiento de datos.

### Spark Declarative Pipelines

Delegar a Data Engineering cuando falten transformaciones productivas.

### Lakebase

No forzar.

### Unity AI Gateway

No forzar.

---

## Definition of Done

- [ ] Existe una audiencia definida.
- [ ] Existe una decisión principal.
- [ ] Los KPIs fueron validados.
- [ ] Se verificaron Metric Views existentes.
- [ ] Cada visualización tiene propósito.
- [ ] La jerarquía de lectura es comprensible.
- [ ] Los filtros fueron probados.
- [ ] Se validó accesibilidad básica.
- [ ] Se validaron permisos.
- [ ] Se validó performance.
- [ ] Se evaluó Genie para exploración conversacional.
- [ ] La documentación está en español.

## Gotchas

- Un dashboard no sustituye una definición semántica.
- Más widgets no significan más información útil.
- Menos widgets tampoco garantiza un buen diseño.
- No utilizar color como único significado.
- No inventar políticas de refresh universales.
- No mostrar precisión numérica mayor que la necesaria para decidir.
