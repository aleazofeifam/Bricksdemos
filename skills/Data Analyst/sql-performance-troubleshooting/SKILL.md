---
name: sql-performance-troubleshooting
description: Diagnostica y resuelve queries SQL lentos en DBSQL — lectura de query profile, identificación de bottlenecks (scan, shuffle, spill), y acciones correctivas. Úsala cuando un reporte o dashboard exceda su SLA de tiempo de respuesta.
---

# SQL Performance Troubleshooting

Workflow paso a paso para diagnosticar y resolver queries lentos.

## Proceso de diagnóstico

1. **Abrir Query Profile** (SQL Editor → History → click en query → Profile tab)
2. **Identificar operador más costoso** (% de tiempo en el plan)
3. **Aplicar fix según bottleneck:**

| Bottleneck | Síntoma | Fix |
|-----------|---------|-----|
| Full Table Scan | Scan domina 80%+ del tiempo | Liquid clustering en columnas de filtro |
| Shuffle | Exchange/Sort entre stages | Reducir JOINs o pre-agregar |
| Spill to disk | Memory exceeded warnings | Aumentar warehouse size o reducir datos |
| Planning time >5s | Muchas tablas/views | Simplificar, materializar CTEs |

## Fixes comunes

```sql
-- Fix 1: Agregar liquid clustering
ALTER TABLE production.gold.transactions CLUSTER BY (transaction_date, customer_id);
OPTIMIZE production.gold.transactions;

-- Fix 2: Materializar CTE pesado
CREATE TABLE production.gold.pre_aggregated AS
SELECT customer_id, DATE_TRUNC('MONTH', txn_date) AS month,
  SUM(amount) AS monthly_total
FROM production.gold.transactions
GROUP BY customer_id, month;

-- Fix 3: Filtro más selectivo
-- Antes (45s): WHERE year = 2026
-- Después (3s): WHERE transaction_date >= '2026-01-01' AND transaction_date < '2027-01-01'
```

## Gotchas

* Liquid clustering NO es inmediato. Se aplica en el próximo OPTIMIZE, no en la próxima query.
* El Query Profile muestra planificación separada de ejecución. Si planning >5s: demasiadas tablas en el plan.
* El caching de DBSQL funciona por result hash. Si cambias un parámetro, no cachea.
* Para queries >30 minutos: considerar materialized view en vez de query directa.
* `EXPLAIN ANALYZE` da el plan real (con datos), no solo estimado. Siempre preferir sobre `EXPLAIN` solo.
* Photon requiere warehouse Medium o superior. En Small no hay Photon available.
* Clustering columns: elegir las MÁS usadas en WHERE (max 4). Más de 4 no ayuda.
