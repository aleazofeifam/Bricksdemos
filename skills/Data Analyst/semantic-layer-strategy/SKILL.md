---
name: semantic-layer-strategy
description: Guía la selección y diseño de la capa semántica en Databricks usando Metric Views, SQL views, materialized views y tablas curadas. Se usa cuando existen KPIs duplicados, definiciones inconsistentes entre dashboards, necesidad de preparar datos para Genie Agents, o dudas sobre dónde debe residir la lógica analítica reutilizable.
---

# Semantic Layer Strategy

Diseña una capa semántica gobernada donde los conceptos de negocio tengan una definición reutilizable y los consumidores no necesiten reconstruir la misma lógica en cada query, dashboard o Genie Agent.

## Principio central

Separar siempre dos decisiones:

1. **¿Dónde vive la definición semántica?**
2. **¿Cómo se optimiza físicamente su ejecución?**

No elegir entre Metric View y Materialized View como si fueran necesariamente alternativas equivalentes.

Una métrica puede estar gobernada mediante una Metric View y utilizar optimizaciones o materializaciones según corresponda.

---

## 1. Discover: identificar la semántica real

Antes de crear una nueva abstracción, identificar:

- pregunta de negocio;
- KPI o concepto utilizado;
- definición matemática;
- granularidad;
- dimensiones permitidas;
- filtros de negocio;
- owner;
- consumidores actuales;
- implementaciones existentes.

Buscar primero si el KPI ya existe en:

- Metric Views;
- dashboards;
- vistas SQL;
- tablas Gold;
- notebooks;
- queries recurrentes;
- Genie Agents.

No crear una nueva definición antes de revisar las existentes.

---

## 2. Detect: encontrar inconsistencias

Para cada KPI crítico, construir:

```text
KPI:
Definición de negocio:
Owner:
Numerador:
Denominador:
Grain:
Dimensiones:
Filtros implícitos:
Timezone:
Currency:
Fuente:
Implementaciones encontradas:
```

Si existen varias implementaciones, compararlas antes de seleccionar una como oficial.

No asumir que la versión más utilizada es necesariamente la correcta.

---

## 3. Decide: seleccionar la abstracción semántica

### Metric View

Default cuando existe:

- KPI reutilizable;
- medida que debe mantenerse consistente;
- análisis flexible por múltiples dimensiones;
- consumo desde varios dashboards o consultas;
- consumo por Genie Agents;
- necesidad de metadata semántica reutilizable.

Ejemplo:

```yaml
version: 1.1
comment: Métricas comerciales oficiales.
source: production.gold.orders

fields:
  - name: region
    expr: source.region
    display_name: Región
    synonyms:
      - territorio
      - zona comercial

  - name: order_month
    expr: DATE_TRUNC('MONTH', source.order_date)
    display_name: Mes del pedido

measures:
  - name: total_revenue
    expr: SUM(source.amount)
    comment: Ingreso neto reconocido según la definición comercial vigente.
    display_name: Ingreso total
    synonyms:
      - revenue
      - ventas netas
      - facturación
```

La metadata debe describir el significado de negocio, no simplemente repetir el nombre técnico.

### SQL View

Usar cuando se necesita:

- encapsular lógica relacional relativamente simple;
- presentar nombres o columnas business-friendly;
- restringir columnas expuestas;
- reutilizar un dataset lógico sin persistir resultados.

No utilizar una cascada de vistas para ocultar un modelo difícil de comprender.

### Materialized View

Considerar cuando:

- existe una transformación costosa utilizada repetidamente;
- la latencia de consulta justifica precálculo;
- una agregación o join recurrente puede beneficiarse de refresh incremental;
- el consumidor no requiere que cada query vuelva a calcular toda la transformación.

No asumir que requiere un pipeline creado manualmente.

Evaluar la estrategia de refresh y verificar si la consulta puede beneficiarse de incrementalización.

### Tabla Gold

Usar cuando el resultado representa:

- un producto de datos persistente;
- una entidad o dataset empresarial reutilizable;
- una transformación con lifecycle propio;
- una interfaz contractual consumida por múltiples workloads.

La tabla Gold no sustituye automáticamente a la capa semántica.

Una tabla Gold puede ser la fuente de una Metric View.

---

## 4. Model: definir KPIs correctamente

Para cada medida oficial:

1. identificar el evento o entidad que representa;
2. definir grain;
3. definir agregación;
4. definir filtros;
5. definir dimensiones válidas;
6. especificar unidades;
7. especificar tratamiento de NULL;
8. especificar tratamiento temporal;
9. identificar owner;
10. documentar sinónimos.

Ejemplo conceptual:

```text
KPI: Revenue

NO suficiente:
SUM(amount)

Correcto:
Ingreso neto reconocido de pedidos confirmados,
excluyendo anulaciones,
en moneda corporativa,
según fecha de reconocimiento financiero.
```

La lógica SQL debe implementar la definición, no convertirse en su definición.

---

## 5. Validate: comprobar la semántica

Para cada KPI crítico, crear casos conocidos:

```text
Caso:
Periodo:
Segmento:
Valor esperado:
Fuente utilizada para validarlo:
Resultado obtenido:
Diferencia:
```

Validar:

- total general;
- una dimensión;
- múltiples dimensiones;
- fechas límite;
- NULL;
- duplicados;
- joins;
- filtros implícitos.

Si existen discrepancias, no publicar la métrica hasta resolverlas o documentarlas explícitamente.

---

## 6. Prepare for Genie

Si la semántica será consumida por Genie:

Revisar:

- comments;
- display names;
- synonyms;
- dimensiones;
- medidas;
- joins;
- grain;
- nombres ambiguos.

Preguntar:

- ¿cómo llama realmente el negocio a este KPI?
- ¿qué sinónimos utiliza?
- ¿qué preguntas formula?
- ¿qué dimensiones espera utilizar?

Preferir semántica estructurada sobre instrucciones textuales repetitivas.

---

## 7. Publish

Entregar:

```text
Dominio:

KPIs oficiales:
- KPI:
  definición:
  owner:
  Metric View:

Objetos semánticos creados o reutilizados:
- ...

Objetos físicos:
- ...

Consumidores:
- dashboards
- Genie Agents
- reporting
- análisis SQL

Definiciones duplicadas encontradas:
- ...

Decisiones pendientes:
- ...
```

---

## Databricks decision gates

### Metric Views

Core de esta skill para KPIs reutilizables.

### Genie Agents

Core como consumidor de la semántica. Preparar metadata para preguntas reales del negocio.

### Materialized Views

Usarlas como decisión de performance, no como sustituto automático de la semántica.

### Spark Declarative Pipelines

Si hace falta construir o modificar el pipeline que produce las tablas fuente, delegar a Data Engineering y favorecer Spark Declarative Pipelines cuando corresponda.

### AI Functions

No forzar. Aplican sólo cuando la semántica requiere información derivada mediante extracción, clasificación u otro enriquecimiento con IA.

### Lakebase

No forzar. Una necesidad OLTP pertenece a otra decisión arquitectónica.

### Unity AI Gateway

No forzar para analytics semántico.

---

## Definition of Done

- [ ] Se identificaron los KPIs relevantes.
- [ ] Se buscaron definiciones existentes antes de crear nuevas.
- [ ] Cada KPI crítico tiene definición de negocio.
- [ ] Cada KPI crítico tiene owner o el gap está documentado.
- [ ] Se conoce grain y dimensiones.
- [ ] Se seleccionó conscientemente Metric View, SQL view, materialized view o tabla.
- [ ] La decisión semántica está separada de la decisión de performance.
- [ ] Las métricas fueron comparadas contra casos conocidos.
- [ ] La metadata necesaria para Genie fue revisada cuando aplica.
- [ ] Los comentarios y documentación generados están en español.

## Gotchas

- No crear una nueva métrica sólo porque escribirla en SQL sea fácil.
- No usar el número de dashboards como criterio universal para decidir una Metric View.
- No elegir una materialized view únicamente por el tamaño de una tabla.
- No esconder semántica empresarial crítica dentro de dashboards.
- No duplicar fórmulas oficiales en múltiples queries.
- No optimizar físicamente antes de verificar que la definición sea correcta.
