---
name: self-service-analytics-enablement
description: Habilita self-service analytics gobernado para usuarios de negocio mediante datos business-friendly, semántica reutilizable, Metric Views y Genie Agents. Úsala cuando los usuarios dependan del equipo de datos para preguntas recurrentes, cuando se quiera habilitar analytics conversacional sobre un dominio, cuando sea necesario preparar tablas o métricas para Genie, o cuando existan múltiples definiciones de los mismos KPIs. No usar como skill principal para optimización puntual de SQL, diseño visual de dashboards o construcción de pipelines.
---

# Self-Service Analytics Enablement

Convierte un dominio de datos en un producto analítico gobernado que usuarios de negocio puedan explorar sin depender del equipo de datos para cada pregunta.

El objetivo no es simplemente crear un dashboard, una vista o un Genie Agent. El objetivo es lograr que las preguntas recurrentes del negocio puedan responderse de forma consistente utilizando datos comprensibles, métricas oficiales y semántica reutilizable.

## Principio operativo

Para necesidades analíticas recurrentes, seguir este orden por defecto:

**pregunta de negocio → KPI/semántica oficial → Metric View cuando aplique → Genie Agent → dashboard o reporte sólo cuando el patrón de consumo lo requiera**

No comenzar automáticamente construyendo un dashboard o escribiendo SQL ad hoc.

## Resultado esperado

Al finalizar, debe existir suficiente contexto y gobernanza para que:

- los usuarios entiendan qué datos están disponibles;
- las tablas y columnas críticas tengan significado de negocio;
- los KPIs reutilizables tengan una definición única;
- un Genie Agent pueda interpretar preguntas reales del dominio;
- las respuestas críticas puedan validarse mediante benchmarks;
- sea evidente quién es responsable de las definiciones y datos;
- nuevas preguntas no obliguen automáticamente a crear nuevos reportes.

---

## 1. Discover: entender primero las preguntas

Antes de modificar datos o crear artefactos, determina qué decisiones intenta tomar el usuario.

Recopila la información disponible y pregunta únicamente por aquello que no pueda inferirse o inspeccionarse.

Identifica:

1. **Audiencia**
   - ¿Quién va a consumir los datos?
   - ¿Qué nivel de conocimiento del dominio tiene?
   - ¿En qué idioma formula normalmente sus preguntas?

2. **Objetivo**
   - ¿Qué decisiones quiere tomar?
   - ¿Qué intenta detectar, comparar, explicar o monitorear?

3. **Preguntas reales**
   - Solicita ejemplos literales de preguntas que los usuarios hacen hoy.
   - Prioriza preguntas reales sobre preguntas inventadas por el equipo técnico.
   - Como punto de partida, intenta obtener entre 10 y 20 preguntas representativas cuando el alcance lo permita.

4. **KPIs y conceptos**
   - ¿Qué métricas aparecen repetidamente?
   - ¿Cuáles tienen una definición formal?
   - ¿Quién es el owner de cada definición?
   - ¿Existen definiciones diferentes para el mismo término?

5. **Datos**
   - ¿Qué tablas, vistas o Metric Views responden actualmente esas preguntas?
   - ¿Cuál es su granularidad?
   - ¿Con qué frecuencia se actualizan?
   - ¿Qué restricciones de acceso o sensibilidad existen?

No diseñes todavía la solución. Primero crea un mapa:

```text
Pregunta
→ concepto/KPI
→ dimensiones necesarias
→ fuente de datos
→ definición oficial
→ consumidor
```

---

## 2. Decide: elegir el patrón de consumo correcto

Clasifica la necesidad antes de crear un artefacto.

| Necesidad | Default |
|---|---|
| Preguntas exploratorias recurrentes en lenguaje natural | Genie Agent |
| KPI corporativo o reutilizado por múltiples consumidores | Metric View |
| Monitoreo visual persistente o ejecutivo | Dashboard + semántica gobernada |
| Distribución periódica a destinatarios concretos | Reporting programado |
| Investigación puntual no recurrente | SQL/análisis ad hoc |
| Transformación de texto, extracción, clasificación o enriquecimiento con IA | Evaluar primero una Databricks AI Function especializada |

### Regla para KPIs

Si una métrica representa una definición de negocio reutilizable, **no la redefinas independientemente en cada query, dashboard o ejemplo de Genie**.

Primero verifica si ya existe una Metric View apropiada.

Si existe:

- reutilízala;
- valida que la definición corresponda al KPI solicitado;
- reutiliza su semántica en lugar de duplicar lógica.

Si no existe y el KPI es suficientemente estable y reutilizable:

- recomienda crear una Metric View;
- identifica owner y definición;
- documenta dimensiones, medidas y filtros de negocio;
- añade metadata semántica útil para consumidores humanos y agentes cuando corresponda.

No conviertas automáticamente toda agregación ad hoc en una Metric View.

---

## 3. Prepare: hacer que los datos sean comprensibles

Para cada activo que será consumido directamente por negocio o por Genie, revisa:

### Tabla o vista

Debe quedar claro:

- propósito;
- granularidad;
- dominio;
- frecuencia de actualización;
- owner o equipo responsable;
- significado de sus principales campos.

### Columnas

Prioriza la documentación de:

- identificadores de negocio;
- fechas importantes;
- dimensiones utilizadas para filtrar o agrupar;
- cantidades y unidades;
- métricas;
- estados y códigos que no sean autoexplicativos.

No gastes contexto documentando columnas técnicas irrelevantes para el consumidor.

### Nombres

No renombres automáticamente columnas, tablas o APIs existentes sólo para traducirlas al español. Un cambio de identificador puede romper consumidores.

Cuando los nombres técnicos existentes no sean claros:

1. conserva el identificador si cambiarlo implica riesgo;
2. agrega una descripción clara en español;
3. añade sinónimos de negocio cuando el mecanismo lo soporte;
4. crea una capa business-friendly únicamente cuando mejore realmente el consumo.

### Ejemplo

```sql
COMMENT ON TABLE production.analytics.ventas_diarias IS
  'Ventas del dominio comercial. Granularidad: una fila por línea de pedido. Actualización diaria.';

COMMENT ON COLUMN production.analytics.ventas_diarias.ingreso_neto IS
  'Ingreso neto de la línea de pedido después de los descuentos aplicables, expresado en USD.';
```

Todo comentario, docstring, explicación técnica y documentación generada por esta skill debe estar en **español**, salvo que el usuario solicite explícitamente otro idioma.

No traduzcas nombres de objetos existentes si hacerlo puede alterar contratos o dependencias.

---

## 4. Simplify: reducir ambigüedad antes de configurar Genie

No expongas indiscriminadamente todo el catálogo.

Selecciona los activos que mejor representen el dominio y elimina ambigüedad innecesaria.

Considera:

- ocultar columnas irrelevantes para el usuario;
- resolver nombres ambiguos;
- documentar relaciones importantes;
- pre-unir o denormalizar cuando una estructura compleja perjudique claramente la interpretación;
- reutilizar Metric Views cuando exista semántica empresarial estable.

El número de tablas no es una regla fija.

Usa el **conjunto mínimo de objetos que permita responder correctamente al alcance definido**.

Añade objetos adicionales sólo cuando preguntas reales demuestren que son necesarios.

---

## 5. Curate: configurar el Genie Agent

El Genie Agent debe representar **un dominio y una audiencia concretos**.

Define explícitamente:

### Propósito

Ejemplo:

```text
Este Genie Agent ayuda al equipo comercial a analizar ventas,
clientes, productos y cumplimiento de objetivos para Latinoamérica.
```

Evita propósitos como:

```text
Responder cualquier pregunta sobre todos los datos de la empresa.
```

### Sample questions

Selecciona preguntas reales y representativas.

Las sample questions deben ayudar al usuario a entender:

- qué puede preguntar;
- qué métricas existen;
- qué dimensiones puede explorar;
- qué nivel de detalle está disponible.

No uses únicamente preguntas sencillas diseñadas para que la demo funcione.

Incluye también preguntas que representen ambigüedades o variaciones reales del negocio.

### Semántica e instrucciones

Aplicar este orden de preferencia:

1. metadata clara de tablas y columnas;
2. Metric Views y definiciones estructuradas cuando corresponda;
3. expresiones SQL para conceptos de negocio;
4. ejemplos SQL verificados;
5. instrucciones de texto sólo para reglas que no puedan expresarse correctamente mediante los mecanismos anteriores.

Evita repetir la misma regla en varios lugares.

Si dos instrucciones se contradicen, resuelve la contradicción antes de publicar el agente.

---

## 6. Teach: convertir preguntas conocidas en conocimiento reutilizable

Para las preguntas recurrentes más importantes:

1. determina la respuesta esperada;
2. identifica la semántica oficial;
3. escribe o valida el SQL correcto;
4. comprueba manualmente el resultado;
5. utiliza el ejemplo como conocimiento para Genie cuando aporte valor.

No enseñes a Genie una query sólo porque ejecuta correctamente.

Primero valida que:

- utiliza el KPI correcto;
- respeta la granularidad;
- utiliza los filtros correctos;
- no duplica filas por joins;
- trata correctamente fechas y zonas horarias;
- respeta permisos y sensibilidad;
- produce un resultado que el owner de negocio considera correcto.

---

## 7. Validate: construir un benchmark real

No considerar terminado un Genie Agent porque cinco preguntas de demostración funcionaron.

Construye un benchmark con las preguntas prioritarias.

Para cada pregunta crítica:

```text
Pregunta canónica
├── formulación alternativa 1
├── formulación alternativa 2
├── formulación alternativa 3, si aporta valor
└── respuesta o SQL de referencia cuando sea posible
```

Incluye variaciones naturales como:

```text
¿Cuánto vendimos en Chile el mes pasado?

Ventas Chile mes anterior

Muéstrame el revenue de Chile del último mes cerrado.
```

Las distintas formulaciones deben representar la misma intención cuando se espera la misma respuesta.

### Validar al menos

- selección de la fuente correcta;
- KPI correcto;
- filtros correctos;
- joins correctos;
- granularidad correcta;
- resultado consistente con la respuesta de referencia;
- comportamiento frente a preguntas ambiguas;
- permisos del usuario consumidor.

No inventes un porcentaje universal de precisión como criterio de aprobación.

Define el objetivo con el equipo responsable según criticidad del dominio y utiliza el benchmark para medirlo.

---

## 8. Resolve: corregir errores de forma estructurada

Cuando Genie responda incorrectamente, no agregues inmediatamente una instrucción de texto.

Diagnostica primero la causa.

```text
Respuesta incorrecta
        │
        ├── ¿Metadata insuficiente?
        │      → mejorar descripción o sinónimos
        │
        ├── ¿KPI ambiguo o duplicado?
        │      → corregir semántica / Metric View
        │
        ├── ¿Join o grain incorrecto?
        │      → corregir modelo o ejemplo SQL
        │
        ├── ¿Pregunta frecuente con patrón específico?
        │      → agregar ejemplo SQL validado
        │
        └── ¿Regla no representable de otra forma?
               → agregar instrucción textual concreta
```

Después de cada cambio importante, vuelve a ejecutar los benchmarks relevantes.

No optimices solamente la pregunta que falló; verifica que la corrección no degrade otras preguntas.

---

## 9. Publish: entregar un producto de datos, no sólo un chat

Antes de publicar, entrega un resumen que incluya:

```text
Dominio:
Audiencia:
Objetivo:

Preguntas prioritarias:
- ...

KPIs oficiales:
- KPI:
  definición:
  owner:
  Metric View existente: sí/no

Activos utilizados:
- ...

Metadata corregida:
- ...

Genie Agent:
- propósito:
- sample questions:
- ejemplos SQL:
- instrucciones especiales:

Benchmark:
- preguntas evaluadas:
- resultados:
- fallos pendientes:

Riesgos o gaps:
- ...

Recomendaciones siguientes:
- ...
```

---

## 10. Observe: mantener el self-service

El self-service no termina al publicar.

Revisa periódicamente:

- nuevas preguntas de usuarios;
- preguntas que Genie no puede responder;
- feedback negativo;
- cambios de esquema;
- nuevos KPIs;
- definiciones que cambiaron;
- assets obsoletos;
- benchmarks que dejaron de pasar.

Una nueva pregunta recurrente puede indicar:

- metadata faltante;
- semántica faltante;
- una Metric View nueva;
- un nuevo ejemplo;
- ampliación legítima del dominio.

No agregues tablas o instrucciones de forma automática.

Primero determina cuál de esas causas explica la necesidad.

---

## Databricks decision gates

Esta skill está alineada con las prioridades de plataforma, pero no debe forzar productos donde no corresponden.

### Genie Agent

**Core de esta skill.**

Usarlo como default cuando usuarios de negocio necesiten investigar recurrentemente datos estructurados mediante lenguaje natural.

### Metric Views

**Core cuando existan KPIs estables y reutilizables.**

Preferir una definición semántica gobernada sobre duplicar fórmulas en queries, dashboards o ejemplos.

### AI Functions

**Aplicable, no obligatoria.**

Cuando el análisis requiera extracción, clasificación, sentimiento, masking, generación u otra transformación de IA soportada, evaluar primero una AI Function especializada antes de crear código LLM personalizado.

### Lakebase

**No forzar.**

Si durante discovery se descubre una necesidad de writes transaccionales, estado operacional, aplicación OLTP o baja latencia, esa necesidad queda fuera del objetivo principal de esta skill y debe tratarse con la skill arquitectónica correspondiente.

### Unity AI Gateway

**No forzar.**

Esta skill configura consumo analítico con Genie. Si el caso evoluciona hacia agentes personalizados, MCPs, model APIs u otro tráfico de IA que deba ser gobernado, remitir a la skill de AI governance correspondiente.

### Spark Declarative Pipelines

**No forzar.**

Si para habilitar el producto analítico es necesario construir o refactorizar pipelines, delegar ese trabajo a las skills de Data Engineering y preferir Spark Declarative Pipelines cuando el patrón sea compatible.

---

## Definition of Done

No declarar completada la tarea hasta comprobar:

- [ ] Existe una audiencia y propósito definidos.
- [ ] Se recopilaron preguntas reales representativas.
- [ ] Se identificaron los KPIs críticos.
- [ ] Cada KPI crítico tiene definición y owner conocidos, o el gap está explícitamente documentado.
- [ ] Se verificó si existen Metric Views reutilizables.
- [ ] Los principales activos tienen metadata comprensible para negocio.
- [ ] La granularidad de cada activo crítico está documentada.
- [ ] El Genie Agent utiliza únicamente los datos necesarios para su dominio.
- [ ] Sample questions representan necesidades reales.
- [ ] Ejemplos SQL utilizados por Genie fueron validados.
- [ ] Existe un benchmark para las preguntas críticas.
- [ ] Los cambios importantes fueron regresionados contra el benchmark.
- [ ] Los permisos fueron revisados desde la perspectiva del usuario consumidor.
- [ ] Los comentarios, docstrings y documentación generados están en español.
- [ ] Los gaps y riesgos pendientes fueron documentados.

---

## Gotchas

- **No confundas self-service con proliferación de dashboards.** Una pregunta recurrente puede ser mejor atendida mediante Genie.
- **No inventes KPIs en SQL ad hoc si existe una definición oficial.**
- **No expongas todo el catálogo a Genie por comodidad.** Mantén el dominio enfocado.
- **No uses un número fijo de tablas como regla universal.** Usa el conjunto mínimo que cubra las preguntas reales.
- **No crees una vista por cada pregunta.** Simplifica el modelo únicamente cuando reduzca ambigüedad o complejidad real.
- **No uses instrucciones textuales para compensar metadata deficiente.** Corrige primero el dato y su semántica.
- **No agregues ejemplos SQL sin validar el resultado con el significado de negocio.**
- **No pruebes solamente el happy path.** Incluye sinónimos, formulaciones alternativas y preguntas ambiguas.
- **No renombres objetos productivos únicamente para traducirlos.** Documenta en español sin romper contratos.
- **No fuerces Lakebase, Unity AI Gateway, SDP ni AI Functions cuando el workload no los necesite.**
