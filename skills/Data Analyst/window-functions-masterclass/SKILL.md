---
name: window-functions-masterclass
description: Guía el diseño y validación de cálculos analíticos con window functions en Databricks SQL, incluyendo ranking, LAG/LEAD, acumulados, moving windows, comparaciones temporales y sessionization. Se usa cuando un cálculo requiere contexto entre filas sin colapsarlas mediante GROUP BY.
---

# Window Functions Masterclass

Selecciona y valida correctamente window functions para cálculos que necesitan conservar cada fila mientras utilizan contexto de otras filas.

## Core model

Toda window function debe responder cuatro preguntas:

```text
¿Qué entidad separa los grupos?      → PARTITION BY
¿En qué orden ocurre el cálculo?     → ORDER BY
¿Qué filas participan?               → frame
¿Qué función se aplica?              → SUM/LAG/RANK/etc.
```

No escribir la función hasta responderlas.

---

## 1. Select the pattern

### Ranking

Necesidad:

```text
top N
posición
orden relativo
```

Elegir:

- `ROW_NUMBER()` si cada fila necesita una posición única;
- `RANK()` si los empates comparten posición y dejan gaps;
- `DENSE_RANK()` si los empates comparten posición sin gaps.

---

### Previous / next value

Necesidad:

```text
comparar con periodo anterior
detectar cambio
calcular diferencia entre eventos
```

Usar:

- `LAG`
- `LEAD`

Ejemplo:

```sql
SELECT
    mes,
    ingreso,
    LAG(ingreso, 1) OVER (ORDER BY mes) AS ingreso_mes_anterior
FROM ingresos_mensuales;
```

---

### Running total

Definir explícitamente el frame:

```sql
SELECT
    fecha,
    ingreso_diario,
    SUM(ingreso_diario) OVER (
        ORDER BY fecha
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS ingreso_acumulado
FROM ingresos_diarios;
```

---

### Moving window

Definir qué significa realmente "últimos 7":

- siete filas;
- siete días calendario;
- siete observaciones;
- siete días con actividad.

No asumir que son equivalentes.

---

### Sessionization / gaps and islands

Definir:

- entidad;
- timestamp;
- máximo gap;
- evento boundary;
- timezone.

Después:

```text
LAG timestamp
→ detectar nuevo grupo
→ acumulado de flags
→ session_id
```

---

## 2. Validate ordering

Una window sin orden correcto puede devolver un resultado técnicamente válido pero semánticamente incorrecto.

Verificar:

- timestamp;
- duplicados en sort key;
- tie-breaker;
- timezone.

Cuando el orden debe ser determinístico, agregar un criterio adicional.

Ejemplo:

```sql
ORDER BY event_time, event_id
```

---

## 3. Validate partition

Preguntar:

**¿El cálculo debe reiniciarse para quién o para qué?**

Ejemplos:

```text
cliente
producto
cuenta
región
cohorte
```

No omitir `PARTITION BY` cuando el cálculo debe reiniciarse por entidad.

---

## 4. Validate frame semantics

Distinguir conscientemente:

```text
ROWS
RANGE
```

No utilizar un frame sólo porque aparece en un ejemplo.

Construir una muestra pequeña cuando existan:

- fechas faltantes;
- valores repetidos;
- irregularidad temporal.

---

## 5. Validate temporal comparisons

Para YoY/MoM:

No asumir que:

```sql
LAG(valor, 12)
```

significa automáticamente "mismo mes del año anterior".

Eso sólo es cierto si:

- existe una fila por cada periodo;
- no hay periodos faltantes;
- el orden es consistente.

Cuando falten periodos, crear o utilizar un calendario apropiado antes de comparar.

---

## 6. Inspect performance

Las windows pueden requerir:

- sort;
- shuffle;
- particiones grandes.

Si la consulta presenta problemas:

- abrir Query Profile;
- revisar cardinalidad;
- revisar partition keys;
- revisar skew;
- evaluar preagregación.

No cambiar el cálculo únicamente por performance si altera la semántica.

---

## 7. Promote reusable window metrics

Preguntar después:

**¿Este cálculo es una métrica oficial reutilizable?**

Ejemplos:

- rolling revenue;
- cumulative target attainment;
- year-over-year growth;
- trailing customer count.

Si sí:

- revisar Metric Views existentes;
- evaluar modelarlo como una medida reutilizable/window measure;
- documentar semántica;
- evitar repetir la misma window expression en múltiples dashboards.

---

## 8. Prepare for Genie

Si el cálculo será preguntado conversacionalmente:

Registrar sinónimos y preguntas reales.

Ejemplo:

```text
¿Cómo vamos acumulado este año?
¿Cuál es el crecimiento interanual?
Muéstrame el promedio móvil de cuatro semanas.
¿Quién está en el top 10 por ventas?
```

No esperar que Genie deduzca qué significa "acumulado" o "rolling" si el negocio tiene una definición específica.

---

## Output

```text
Pregunta:

Entidad:
Partition:

Orden:
Order by:

Frame:

Window function:

Edge cases:
- ...

Validación:
- ...

KPI reutilizable:
- sí/no

Metric View:
- existente / recomendada / no aplica
```

---

## Databricks decision gates

### Databricks SQL window functions

Core.

### Metric Views

Aplicables cuando la medida temporal es estable y reutilizable.

### Genie Agents

Aplicables cuando la métrica debe poder consultarse en lenguaje natural.

### SQL Performance Troubleshooting

Invocar la skill correspondiente si la window genera un problema de performance significativo.

### Spark Declarative Pipelines

No forzar. Si el cálculo debe transformarse en un dataset productivo upstream, delegar a Data Engineering.

### AI Functions

No forzar.

### Lakebase

No forzar.

### Unity AI Gateway

No forzar.

---

## Definition of Done

- [ ] Está claro qué entidad define la partición.
- [ ] Está definido el orden.
- [ ] El orden es determinístico cuando debe serlo.
- [ ] El frame fue seleccionado conscientemente.
- [ ] Se probaron gaps y duplicados cuando aplican.
- [ ] Se validó temporalidad.
- [ ] Se revisó performance cuando el volumen lo requiere.
- [ ] Se evaluó Metric View para cálculos reutilizables.
- [ ] Los comentarios y documentación están en español.

## Gotchas

- `LAG(..., 12)` no significa YoY si faltan periodos.
- `ROWS` y `RANGE` no son intercambiables.
- Ranking sin tie-breaker puede no ser determinístico.
- Sessionization depende completamente de la definición del gap.
- Una window correcta no arregla un dataset con grain incorrecto.
- No duplicar una window KPI gobernada en cada dashboard.
