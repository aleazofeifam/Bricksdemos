---
name: finops-idle-warehouses
description: Detecta warehouses SQL que llevan más de 2 horas activos sin queries, indicando posible capacidad ociosa. Usar cuando el usuario pregunte si hay warehouses idle, quiera reducir costos de compute inactivo, o necesite validar configuraciones de auto-stop.
---

# Warehouses Activos sin Carga Útil

## Cuándo usar este skill

Cuando el usuario pregunte:
- "¿Hay warehouses encendidos sin uso?"
- "¿Cuáles warehouses están idle?"
- "¿Tenemos compute desperdiciado ahora mismo?"
- "Validar configuraciones de auto-stop"
- "¿Cuánto tiempo llevan activos los warehouses?"

## Query SQL

```sql
WITH latest_events AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY workspace_id, warehouse_id
      ORDER BY event_time DESC
    ) AS rn
  FROM system.compute.warehouse_events
)
SELECT
  workspace_id,
  warehouse_id,
  event_type,
  cluster_count,
  event_time,
  TIMESTAMPDIFF(MINUTE, event_time, CURRENT_TIMESTAMP()) / 60.0 AS hours_in_state
FROM latest_events
WHERE rn = 1
  AND event_type IN ('RUNNING', 'SCALED_UP')
  AND TIMESTAMPDIFF(MINUTE, event_time, CURRENT_TIMESTAMP()) >= 120
ORDER BY hours_in_state DESC;
```

## Notas de interpretación

- Un warehouse con `hours_in_state > 2` y sin queries recientes es candidato a investigar.
- **NO detener automáticamente**. Primero confirmar:
  - ¿Tiene dependencias de dashboards o alertas?
  - ¿Hay un SLA que requiere warm-start?
  - ¿Es un warehouse compartido con horario predecible?
- La acción correcta suele ser configurar auto-stop (10-15 min para prod, 5-10 para dev).
- Cada hora de warehouse idle con 1 cluster = ~$0.40-$1.00+ USD dependiendo del tamaño.

## Tablas requeridas

- `system.compute.warehouse_events` (SELECT)
