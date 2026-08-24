---
name: uc-permissions-audit-compliance
description: Audita permisos en Unity Catalog — detecta sobre-privilegio, accesos no autorizados, principals huérfanos, y genera evidencia para compliance. Úsala para revisiones de seguridad, preparación de auditorías, o detección de anomalías de acceso.
---

# UC Permissions Audit & Compliance

Detectar sobre-privilegio y generar evidencia de compliance.

## Audit de grants actuales

```sql
-- Quién tiene acceso a schemas de producción
SELECT
  grantee AS principal,
  privilege_type,
  table_catalog, table_schema,
  'SCHEMA' AS securable_type
FROM system.information_schema.schema_privileges
WHERE table_catalog = 'production'
  AND privilege_type IN ('ALL_PRIVILEGES', 'MODIFY', 'OWN')
ORDER BY grantee, table_schema
```

## Detectar sobre-privilegio

```sql
-- Principals con más de 5 grants directos (posible over-privilege)
SELECT grantee, COUNT(DISTINCT table_schema) AS schemas_with_access,
  COLLECT_SET(privilege_type) AS privilege_types
FROM system.information_schema.schema_privileges
WHERE table_catalog = 'production'
GROUP BY grantee
HAVING COUNT(DISTINCT table_schema) > 5
ORDER BY schemas_with_access DESC
```

## Accesos fuera de horario (anomalía)

```sql
SELECT user_identity.email, action_name,
  request_params.full_name_arg AS accessed_object,
  event_time, HOUR(event_time) AS hour_of_day
FROM system.access.audit
WHERE action_name = 'getTable'
  AND HOUR(event_time) NOT BETWEEN 7 AND 22  -- Fuera de horario laboral
  AND event_date >= CURRENT_DATE() - 7
ORDER BY event_time DESC
```

## Reporte para auditor (CSV export)

```sql
-- Evidencia: todos los grants en producción
SELECT grantee, privilege_type, table_catalog, table_schema, table_name,
  'active' AS status, CURRENT_TIMESTAMP() AS audit_date
FROM system.information_schema.table_privileges
WHERE table_catalog = 'production'
ORDER BY grantee, table_schema, table_name
```

## Gotchas

* `SHOW GRANTS` incluye permisos heredados del catálogo/schema padre — no se pueden revocar parcialmente.
* system.access.audit tiene lag de ~15 minutos. No sirve para alertas real-time.
* Los grants a grupos se resuelven en runtime. No hay "effective permissions" API directa.
* Service Principals heredan membership de grupo pero NO aparecen en `SHOW GRANTS ON USER`.
* Un principal puede ser usuario O grupo O SP — enumerar los tres tipos en audit.
* Los permisos de information_schema solo muestran lo que el usuario actual puede ver. Correr como admin para audit completa.
