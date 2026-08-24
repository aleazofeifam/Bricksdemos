---
name: multi-tenant-data-isolation
description: Patrones de aislamiento de datos multi-tenant en Unity Catalog — catalog-per-tenant, schema-per-tenant, row-level filtering por tenant_id. Úsala cuando el usuario tenga múltiples clientes o unidades de negocio compartiendo infraestructura y necesite aislar datos entre ellos.
---

# Multi-Tenant Data Isolation in Unity Catalog

Patrones arquitectónicos para aislar datos entre tenants (clientes, BUs, regiones) en un lakehouse compartido.

## Decision Framework

| Patrón | Cuándo usarlo | Límite práctico |
|--------|-------------|----------------|
| Catalog-per-tenant | Aislamiento total, regulación estricta | <50 tenants |
| Schema-per-tenant | Buen balance aislamiento/gestión | <500 tenants |
| Row-filter (tabla compartida) | Escala masiva, queries cross-tenant | Ilimitado |

## Instrucciones: Schema-per-tenant + Row Filter (recomendado)

1. **Estructura base:**
   ```
   catalog: production
   schemas: tenant_acme, tenant_globex, tenant_initech, ...
   shared schema: production.cross_tenant (vistas agregadas internas)
   ```

2. **Crear row filter dinámico:**
   ```sql
   CREATE FUNCTION production.security.tenant_filter(tenant_id_col STRING)
   RETURNS BOOLEAN
   RETURN (
     is_account_group_member(concat('tenant_', tenant_id_col))
     OR is_account_group_member('data_platform_admins')
   );
   ```

3. **Aplicar a tablas compartidas:**
   ```sql
   ALTER TABLE production.shared.transactions
     SET ROW FILTER production.security.tenant_filter ON (tenant_id);
   ```

4. **Vistas cross-tenant (solo para admins):**
   ```sql
   CREATE VIEW production.cross_tenant.all_transactions AS
   SELECT * FROM production.shared.transactions;
   -- El row filter aplica automáticamente según el grupo del usuario
   ```

## Gotchas

* Catalog-per-tenant escala mal después de ~50 catalogs (límites internos de UC, overhead de gestión de permisos).
* El row filter ejecuta por CADA query — en tablas >1B filas el impacto es measurable (~5-15% overhead). Usa liquid clustering por `tenant_id` para mitigar.
* `is_account_group_member()` es más seguro que `current_user()` — un usuario puede estar en múltiples tenants vía grupos.
* El row filter aplica también en Genie, dashboards, y a través de vistas. NO hay bypass accidental.
* Column masks + row filters se pueden combinar (ej: tenant A ve sus datos completos, tenant B ve columnas sensibles enmascaradas).
* Para datos de referencia compartidos (países, monedas), NO aplicar row filter — ponerlos en schema `public` sin filtro.
* Los Service Principals heredan membrezía de grupo — asignar SP por tenant si cada tenant tiene su propio job de ingesta.
* Testing: SIEMPRE probar con un usuario de prueba del tenant (no admin) para verificar que el filtro funciona.
