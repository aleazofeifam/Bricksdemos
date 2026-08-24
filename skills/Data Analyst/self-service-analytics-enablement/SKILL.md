---
name: self-service-analytics-enablement
description: Habilita self-service analytics para usuarios de negocio — documentar tablas con COMMENTs claros, crear vistas business-friendly, curar Genie Space con ejemplos, y definir métricas gobernadas. Úsala cuando el equipo de negocio dependa del equipo de datos para cada consulta ad-hoc.
---

# Self-Service Analytics Enablement

Estrategia para que el negocio se auto-sirva sin depender del equipo de datos.

## Paso 1: Preparar tablas business-friendly

```sql
-- Vistas denormalizadas con nombres legibles
CREATE OR REPLACE VIEW production.analytics.ventas_diarias AS
SELECT
  o.order_date AS fecha,
  c.customer_name AS cliente,
  c.region AS region,
  p.product_name AS producto,
  p.category AS categoria,
  o.quantity AS cantidad,
  o.amount AS ingreso_neto
FROM production.gold.orders o
JOIN production.gold.customers c ON o.customer_id = c.id
JOIN production.gold.products p ON o.product_id = p.id;

-- Documentar en lenguaje de negocio
COMMENT ON TABLE production.analytics.ventas_diarias IS
  'Ventas diarias con detalle de cliente y producto. Granularidad: 1 fila = 1 línea de pedido. Actualización: diaria antes de 6AM.';

COMMENT ON COLUMN production.analytics.ventas_diarias.ingreso_neto IS
  'Ingreso neto en USD después de descuentos e impuestos.';
```

## Paso 2: Top-20 preguntas del negocio

Identificar y documentar las preguntas más frecuentes:
1. "¿Cuánto vendimos este mes vs el anterior?"
2. "¿Cuáles son los top 10 productos?"
3. "¿Cuál es la retención por cohorte?"
4. "¿Qué clientes están en riesgo de churn?"

## Paso 3: Curar Genie Space

- Incluir SOLO las 5-7 tablas relevantes (no todo el catálogo)
- Escribir 10+ ejemplos SQL anotados para las preguntas top
- Instrucciones en lenguaje del dominio ("revenue" no "SUM(amount)")

## Gotchas

* Los usuarios de negocio NO entienden JOINs. Crear vistas denormalizadas: 1 vista = 1 pregunta de negocio.
* Genie genera SQL más preciso si las columnas tienen COMMENTs descriptivos. "col_1" → "Fecha de última compra".
* NO documentar columnas internas/técnicas (_ingested_at, _hash, etc.) — confunden a Genie y a usuarios.
* Usar nombres en español si la audiencia es hispanohablante. Genie entiende español.
* Limitar a 5-7 tablas por Genie Space. Más tablas = más confusión = respuestas menos precisas.
* La primera experiencia es crítica. Si la primera pregunta del usuario falla, no volverá. Validar top-5 preguntas manualmente.
* Metric views son el puente ideal: el negocio pregunta "revenue by region" y Genie usa MEASURE() correctamente.
