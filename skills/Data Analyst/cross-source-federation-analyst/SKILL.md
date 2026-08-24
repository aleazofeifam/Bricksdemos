---
name: cross-source-federation-analyst
description: Guía análisis sobre datos distribuidos entre Databricks y sistemas externos mediante Lakehouse Federation y consultas cross-catalog. Se usa para reporting ad hoc, exploración, POCs o análisis que requieren consultar datos externos sin ingerirlos primero en Databricks.
---

# Cross-Source Federation for Analysts

Permite consultar datos externos de forma gobernada sin convertir automáticamente cada necesidad analítica en un pipeline de ingestión.

## Principio

**Federar primero cuando el objetivo sea explorar o consultar datos in-place.**

**Materializar o ingerir cuando el patrón de consumo justifique convertir esos datos en un producto analítico administrado.**

No decidir únicamente por número de filas o número de queries.

---

## 1. Discover

Identificar:

```text
Fuente externa:
Dataset:
Pregunta de negocio:
Frecuencia esperada:
Frescura requerida:
Volumen:
Selectividad:
Concurrencia:
SLA:
Impacto sobre sistema fuente:
Necesidad de escritura:
Consumidores:
```

---

## 2. Gate: confirmar que federation corresponde

Lakehouse Federation es apropiado cuando:

- se necesita consultar los datos sin moverlos;
- el uso es exploratorio o ad hoc;
- se está construyendo un POC;
- se necesita acceso gobernado a una fuente operacional existente;
- la frescura in-place es importante;
- el impacto sobre el sistema fuente es aceptable.

No utilizar query federation como default cuando:

- existe ingestión recurrente de alto volumen;
- se necesita aislar la carga analítica del sistema operacional;
- existen SLAs de latencia incompatibles con acceso remoto;
- los datos deben transformarse repetidamente;
- múltiples productos downstream dependen del dataset;
- se requiere escritura.

---

## 3. Validate governance

Antes de consultar:

- verificar que exista la Connection apropiada;
- verificar el foreign catalog;
- utilizar permisos de Unity Catalog;
- revisar sensibilidad del dataset;
- evitar replicar credenciales en notebooks o SQL.

Las consultas a foreign catalogs deben tratarse como acceso a sistemas productivos externos.

---

## 4. Query with pushdown in mind

Aplicar filtros lo antes posible.

Ejemplo:

```sql
-- Consulta analítica federada.
SELECT
    f.opportunity_id,
    f.amount,
    f.stage,
    c.customer_name,
    c.segment
FROM crm_foreign.public.opportunities AS f
JOIN production.gold.customers AS c
    ON f.account_id = c.crm_account_id
WHERE f.close_date >= CURRENT_DATE()
  AND f.stage IN ('Negotiation', 'Closed Won');
```

No seleccionar columnas innecesarias.

No asumir que cualquier expresión puede ejecutarse completamente en el sistema remoto.

Revisar el Query Profile y el comportamiento real.

---

## 5. Measure before materializing

Si la consulta no cumple expectativas:

Medir:

- tiempo remoto;
- filas retornadas;
- bytes transferidos;
- filtros aplicados;
- joins;
- concurrencia;
- carga sobre source DB.

Después elegir entre:

```text
mantener federado
        |
        +--> simplificar query
        |
        +--> mejorar filtros/pushdown
        |
        +--> crear dataset analítico local
        |
        +--> establecer ingestión recurrente
```

No materializar automáticamente la tabla más pequeña o más grande sin analizar el plan.

---

## 6. Escalate to ingestion when appropriate

Si los datos se convierten en una dependencia analítica estable:

1. documentar las queries y preguntas que justifican la ingestión;
2. definir frescura;
3. definir incrementalidad;
4. definir ownership;
5. delegar la construcción del pipeline a Data Engineering.

Cuando exista un conector administrado compatible, evaluar Lakeflow Connect.

Para transformación recurrente dentro de Databricks, favorecer Spark Declarative Pipelines cuando el patrón sea compatible.

---

## 7. Prepare for analytics consumers

Si el resultado será consumido por analistas o Genie:

No obligar al consumidor a comprender:

- nombre de la conexión;
- particularidades del DB remoto;
- joins técnicos;
- claves internas.

Crear una interfaz business-friendly cuando sea necesario.

Documentar:

- propósito;
- grain;
- frescura;
- source system;
- limitaciones.

---

## Lakebase decision gate

Lakehouse Federation consulta una base operacional existente; no crea una nueva.

Si durante discovery la necesidad real resulta ser:

- almacenar estado de una aplicación;
- escribir transacciones;
- construir un backend operacional;
- proporcionar una base PostgreSQL administrada para una aplicación;

detener esta skill y evaluar Lakebase mediante la skill arquitectónica correspondiente.

No confundir acceso federado con necesidad de una base transaccional.

---

## Output

```text
Fuente:
Pregunta:

Decisión:
- federar
- ingerir/materializar
- escalar arquitectura

Justificación:

SLA:
Frescura:

Impacto sobre source:
- ...

Gobernanza:
- ...

Query validada:
- ...

Plan futuro:
- ...
```

---

## Databricks decision gates

### Lakehouse Federation

Core.

### Spark Declarative Pipelines

Aplicable si el análisis demuestra que debe existir una transformación recurrente local.

### Lakeflow Connect

Evaluar para ingestión recurrente cuando exista un conector adecuado.

### Genie Agents

Aplicable cuando el dataset federado será parte del dominio conversacional. Asegurar metadata comprensible.

### Metric Views

Aplicable si sobre los datos federados o materializados existen KPIs gobernados.

### Lakebase

Sólo si se descubre una necesidad diferente: una nueva base operacional/transaccional.

### AI Functions

No forzar.

### Unity AI Gateway

No forzar.

---

## Definition of Done

- [ ] Se definió el patrón de consumo.
- [ ] Se confirmó que la necesidad es read-only.
- [ ] Se revisó impacto sobre el sistema fuente.
- [ ] Se utilizaron permisos de Unity Catalog.
- [ ] Se aplicaron filtros apropiados.
- [ ] Se midió el comportamiento real.
- [ ] La decisión federation vs ingestion está documentada.
- [ ] Se identificó si existe una dependencia productiva recurrente.
- [ ] La metadata para consumidores está documentada en español.

## Gotchas

- Federation no elimina el costo o carga sobre el sistema externo.
- El rendimiento depende también del sistema remoto y de la red.
- No todas las operaciones necesariamente se ejecutan en el source.
- Query federation es read-only.
- No convertir thresholds arbitrarios en reglas arquitectónicas.
- Si el workload deja de ser exploratorio, reconsiderar la arquitectura.
