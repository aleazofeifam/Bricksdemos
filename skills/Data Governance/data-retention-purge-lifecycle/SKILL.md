---
name: data-retention-purge-lifecycle
description: Implementa políticas de retención y eliminación de datos en Delta/UC — TTL por tabla, purge schedule, GDPR right-to-erasure, y archivado a cold storage. Úsala cuando necesites borrar datos por compliance, controlar storage, o implementar data lifecycle management.
---

# Data Retention & Purge Lifecycle

Políticas de retención, eliminación, y archivado de datos.

## Clasificación por retention tier

| Tier | Retención | Ejemplo | Acción al vencer |
|------|----------|---------|------------------|
| Hot | 90 días | Logs operativos | DELETE + VACUUM |
| Warm | 1 año | Transacciones | ARCHIVE (Deep Clone) |
| Cold | 5 años | Compliance/legal | Move to Glacier |
| Permanent | Indefinido | Datos maestros | Nunca borrar |

## Implementación: Job de retention diario

```sql
-- Paso 1: DELETE filas vencidas
DELETE FROM production.ops.application_logs
WHERE log_date < CURRENT_DATE() - INTERVAL 90 DAYS;

-- Paso 2: OPTIMIZE para compactar
OPTIMIZE production.ops.application_logs
WHERE log_date >= CURRENT_DATE() - INTERVAL 90 DAYS;

-- Paso 3: VACUUM para liberar storage
VACUUM production.ops.application_logs RETAIN 168 HOURS;
```

## GDPR Right to Erasure (borrado completo)

```sql
-- 1. Borrar de todas las tablas
DELETE FROM production.gold.customers WHERE user_id = 'ERASURE-REQUEST-456';
DELETE FROM production.gold.orders WHERE customer_id = 'ERASURE-REQUEST-456';
DELETE FROM production.gold.interactions WHERE user_id = 'ERASURE-REQUEST-456';

-- 2. PURGE de time travel (elimina de versiones históricas)
REORG TABLE production.gold.customers APPLY (PURGE);
REORG TABLE production.gold.orders APPLY (PURGE);

-- 3. Registrar para compliance
INSERT INTO production.compliance.erasure_audit
VALUES ('ERASURE-REQUEST-456', CURRENT_TIMESTAMP(), CURRENT_USER(), 'completed');
```

## Archivado a cold storage

```sql
-- Deep Clone a external location con lifecycle policy
CREATE TABLE archive.cold.transactions_2024
  DEEP CLONE production.gold.transactions
  LOCATION 's3://archive-bucket/transactions/2024/';

-- Después de validar el archive:
DELETE FROM production.gold.transactions
WHERE transaction_date < '2025-01-01';
```

## Gotchas

* `VACUUM RETAIN 0 HOURS` requiere `SET spark.databricks.delta.retentionDurationCheck.enabled = false`. PELIGROSO si hay queries concurrentes.
* REORG PURGE es la forma SEGURA de eliminar tombstones de time travel post-DELETE.
* Delta time travel mantiene datos BORRADOS accesibles por default 7 días. Para GDPR estricto: esto es retención ilegal si no se purga.
* Archivado a cold: usar DEEP CLONE (no SHALLOW CLONE) — Deep Clone copia datos físicamente, Shallow solo referencia.
* El job de retention debe correr en OFF-PEAK hours para no impactar queries de BI.
* Mantener registro de TODAS las eliminaciones para audit trail (tabla de erasure_audit).
* Following workspace policies: use RemoveAfter tags on all resources to signal retention expectations.
