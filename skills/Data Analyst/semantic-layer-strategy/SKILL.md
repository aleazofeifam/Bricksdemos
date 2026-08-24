---
name: semantic-layer-strategy
description: Estrategia de capa semántica en Databricks — cuándo usar metric view vs materialized view vs vista SQL vs tabla gold. Decision framework para elegir la abstracción correcta. Úsala cuando haya confusión sobre dónde definir una métrica o qué tipo de view usar.
---

# Semantic Layer Strategy

Framework de decisión para elegir la abstracción correcta en Databricks.

## Decision Matrix

| Necesidad | Solución | Refresh | Performance |
|-----------|----------|---------|-------------|
| KPI con dimensiones (revenue by region) | Metric View | Al vuelo | OK si tabla base <10M |
| Transformación pesada pre-computada | Materialized View | En pipeline DLT | Excelente |
| Lógica ligera reutilizable | Vista SQL | Al vuelo | Depende de complejidad |
| Snapshot periódico para BI | Tabla gold + schedule | Job diario | Excelente |
| Métricas derivadas cross-domain | Metric View sobre MV | Híbrido | Buena |

## Cuándo usar cada una

### Metric View (capa semántica gobernada)
```yaml
# Ideal para: métricas de negocio con pocas dimensiones, tabla base razonable
version: 0.1
source: production.gold.orders
measures:
  - name: total_revenue
    expr: SUM(amount)
  - name: order_count
    expr: COUNT(*)
dimensions:
  - name: order_date
    expr: order_date
  - name: region
    expr: region
```

### Materialized View (pre-computada)
```sql
-- Ideal para: JOINs pesados, agregaciones sobre >100M filas
CREATE MATERIALIZED VIEW production.gold.customer_360 AS
SELECT c.*, COUNT(o.id) AS total_orders, SUM(o.amount) AS ltv
FROM customers c LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY ALL;
```

### Vista SQL (lógica ligera)
```sql
-- Ideal para: filtros simples, renombramientos, uniones ligeras
CREATE VIEW production.gold.active_customers AS
SELECT * FROM customers WHERE last_activity >= CURRENT_DATE() - 90;
```

## Gotchas

* Metric views NO se materializan (calculan al vuelo). No usar para métricas que requieren aggregation de >100M filas en real-time.
* Materialized views se refrescan SOLO en pipeline DLT, no bajo demanda. Si necesitas refresh ad-hoc, usa tabla + job.
* Views SQL no tienen statistics → el optimizador trabaja peor que con tablas. Para queries frecuentes, materializar.
* NO anidar views >3 niveles. Causa: performance catastrophe + lineage confuso + debugging imposible.
* Metric views se consultan con MEASURE(): `SELECT region, MEASURE(total_revenue) FROM mv GROUP BY region`.
* Si una métrica la usan >3 dashboards con la misma definición → metric view. Si solo 1 dashboard → view SQL.
