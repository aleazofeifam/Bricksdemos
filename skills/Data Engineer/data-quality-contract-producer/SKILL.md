---
name: data-quality-contract-producer
description: Define y operacionaliza contratos de datos entre productores y consumidores, incluyendo schema, semántica, freshness, completeness, validity, ownership, cambios compatibles y criterios de calidad ejecutables. Úsala al publicar un nuevo producto de datos, formalizar SLAs, prevenir breaking changes, acordar expectativas con consumidores o convertir reglas de calidad dispersas en un contrato verificable.
---

# Data Quality Contract for Producers

Un data contract describe lo que un productor promete entregar y lo que un consumidor puede asumir.

No es sólo un conjunto de expectations.

---

# Contract layers

Todo contrato debe considerar:

```text
1. Identity
2. Schema
3. Semantics
4. Data quality
5. Freshness
6. Availability
7. Ownership
8. Security
9. Change policy
10. Consumer expectations
```

---

## 1. Discover consumers

Antes de redactar el contrato identificar:

```text
Dataset:
Producer:
Owner:
Consumers:
Critical consumers:
Business processes:
Dashboards:
Genie Agents:
ML models:
Applications:
```

Utilizar lineage cuando esté disponible.

No declarar consumidores únicamente de memoria.

---

## 2. Define identity

```yaml
dataset: production.gold.orders
domain: commerce
owner: commerce-data
version: "1.0"
```

El versionado del contrato no tiene que coincidir con una versión física de Delta.

---

## 3. Define schema guarantees

Por columna crítica registrar:

```yaml
columns:
  - name: order_id
    type: string
    nullable: false
    semantic: Identificador único del pedido.
    classification: internal
```

No prometer estabilidad para columnas técnicas que no forman parte de la interfaz del producto.

---

## 4. Define grain explicitly

Ejemplo:

```yaml
grain:
  description: Una fila por pedido.
  key:
    - order_id
```

El grain es parte del contrato.

Una tabla con el mismo schema pero grain diferente representa un breaking change semántico.

---

## 5. Define semantic guarantees

Ejemplo:

```yaml
semantics:
  order_status:
    definition: Estado vigente del pedido.
    accepted_values:
      - PENDING
      - COMPLETE
      - CANCELLED
```

No asumir que un nombre comprensible elimina la necesidad de definición.

---

## 6. Define quality rules

Clasificar reglas:

```text
ROW
- not null
- domain validity
- range validity
- format

TABLE
- uniqueness
- row volume
- reconciliation

TEMPORAL
- freshness
- event delay

BUSINESS
- balance reconciliation
- referential business rules
```

---

## 7. Choose enforcement mechanism

### Pipeline Expectations

Adecuado para constraints por registro.

Ejemplo:

```python
from pyspark import pipelines as dp

ORDER_RULES = {
    "order_id_presente": "order_id IS NOT NULL",
    "estado_valido": "status IN ('PENDING','COMPLETE','CANCELLED')",
    "importe_no_negativo": "amount >= 0"
}

@dp.table(
    name="orders_silver",
    comment="Pedidos validados de acuerdo con el contrato del dominio comercial."
)
@dp.expect_all(ORDER_RULES)
def orders_silver():
    return spark.readStream.table("orders_bronze")
```

### Validation dataset

Usar para checks como:

- uniqueness;
- aggregate reconciliation;
- cross-table validation.

### Data Quality Monitoring

Utilizar como mecanismo complementario para:

- anomaly detection;
- freshness patterns;
- completeness patterns;
- health visibility.

No utilizar anomaly detection como sustituto de un SLA contractual explícito.

---

## 8. Select violation policy

Para cada rule definir:

```text
WARN
DROP
FAIL
QUARANTINE
```

Ejemplo:

```yaml
quality:
  order_id:
    rule: "order_id IS NOT NULL"
    action: fail

  optional_campaign:
    rule: "campaign_id IS NOT NULL"
    action: warn
```

La criticidad debe venir del impacto del dato.

No usar el mismo comportamiento para todas las reglas.

---

## 9. Freshness contract

Definir:

```yaml
freshness:
  expected_by: "07:00 America/Costa_Rica"
  data_timestamp: ingestion_timestamp
  owner: commerce-data
```

O:

```yaml
freshness:
  maximum_data_delay: PT2H
```

No confundir:

```text
pipeline finished
```

con:

```text
data is fresh
```

---

## 10. Completeness contract

Evitar thresholds inventados.

Derivar criterios de:

- negocio;
- historical baseline;
- upstream expectations;
- reconciliation.

Ejemplo:

```yaml
completeness:
  description: Todos los pedidos confirmados del sistema fuente deben aparecer.
  validation:
    type: reconciliation
    key: order_id
```

---

## 11. Metadata contract

Toda tabla contractual debe tener:

```text
table comment
critical column comments
owner
domain
sensitivity tags cuando aplique
```

Ejemplo:

```sql
COMMENT ON TABLE production.gold.orders IS
  'Pedidos consolidados del dominio comercial. Granularidad: una fila por pedido.';

COMMENT ON COLUMN production.gold.orders.order_id IS
  'Identificador único del pedido en el sistema de comercio electrónico.';
```

Comentarios en español salvo requerimiento contrario.

---

## 12. Change classification

### Compatible

Ejemplos:

```text
nueva columna opcional
nueva documentación
nuevo tag no restrictivo
```

### Potentially breaking

Ejemplos:

```text
rename
drop
type change
nullable → non-null
grain change
semantic definition change
timezone change
unit/currency change
```

No clasificar cambios sólo a nivel de schema.

---

## 13. Breaking-change workflow

```text
proposed change
      ↓
impact analysis
      ↓
consumer identification
      ↓
compatibility option
      ↓
migration window
      ↓
parallel support
      ↓
consumer validation
      ↓
deprecation
```

No codificar "7 días" o "30 días" como regla universal.

El periodo depende del contrato y criticidad.

---

## 14. Lineage impact

Antes de un breaking change revisar:

```text
downstream tables
dashboards
queries
jobs
pipelines
models
Metric Views
Genie consumption
```

Si el impacto no puede determinarse completamente, documentar incertidumbre.

---

## 15. Genie readiness

Cuando un dataset sea consumido por Genie:

El contrato debe contener semántica suficiente para responder:

```text
¿Qué representa esta tabla?
¿Cuál es el grain?
¿Qué significa cada dimensión crítica?
¿Qué tan fresca está?
¿Quién la administra?
```

Capturar preguntas reales del consumidor.

Si aparecen KPIs oficiales:

hacer handoff a `semantic-layer-strategy`.

No definir múltiples fórmulas de KPI dentro del contract.

---

## 16. Contract representation

Mantener una representación versionada junto al código cuando el proceso del equipo lo permita.

Ejemplo conceptual:

```yaml
contract:
  dataset: production.gold.orders
  version: "1.2"
  owner: commerce-data

  grain:
    key: [order_id]

  freshness:
    maximum_delay: PT2H

  quality:
    - name: order_id_required
      expression: order_id IS NOT NULL
      action: fail

  change_policy:
    compatibility: additive
```

Puede adaptarse a ODCS u otro estándar organizacional si el equipo ya lo utiliza.

No introducir un estándar nuevo sin necesidad.

---

## 17. Validate the contract

Antes de publicar:

- ejecutar rules;
- verificar schema real;
- verificar metadata;
- verificar owner;
- verificar consumers;
- verificar freshness;
- revisar ejemplos de datos;
- revisar lineage.

---

## Output

```text
Dataset:
Owner:
Consumers:

Contract:
- schema:
- grain:
- semantics:
- freshness:
- completeness:
- quality:
- security:

Enforcement:
- expectations:
- validation datasets:
- monitoring:

Breaking change policy:
- ...

Metadata:
- ...

Genie readiness:
- ...

Known gaps:
- ...
```

---

# Definition of Done

- [ ] Existe owner.
- [ ] Se identificaron consumidores.
- [ ] El grain está explícito.
- [ ] Se identificaron columnas contractuales.
- [ ] Existe definición semántica de campos críticos.
- [ ] Las reglas de calidad están clasificadas.
- [ ] Cada regla tiene un comportamiento consciente.
- [ ] Freshness está definido como dato, no sólo como job.
- [ ] Completeness tiene criterio verificable.
- [ ] Se documentó change policy.
- [ ] Se revisó lineage.
- [ ] Se publicó metadata.
- [ ] Se revisó Genie-readiness si aplica.
- [ ] Código y documentación están en español.

# Gotchas

- Expectations son constraints de calidad, no un data contract completo.
- Una anomalía histórica no sustituye un SLA.
- Schema compatible puede ser semánticamente incompatible.
- Grain es parte del contrato.
- El mismo nombre de KPI puede esconder definiciones diferentes.
- No inventar thresholds de calidad sin un source of truth.
