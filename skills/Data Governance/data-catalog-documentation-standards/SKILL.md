---
name: data-catalog-documentation-standards
description: Estándares de documentación del catálogo de datos — COMMENT en tablas y columnas, tags obligatorios, naming conventions por capa, y métricas de cobertura. Úsala cuando el catálogo de UC sea un desierto sin descripciones y nadie entienda qué datos hay disponibles.
---

# Data Catalog Documentation Standards

Estándares para mantener un catálogo de datos vivo, documentado y descubrible.

## Naming Conventions

```
{layer}_{domain}_{entity}[_{qualifier}]

Ejemplos:
  bronze_crm_contacts_raw
  silver_crm_contacts_deduped
  gold_sales_revenue_daily
  staging_finance_budget_temp
```

| Capa | Prefijo | Uso |
|------|---------|-----|
| Raw/Landing | bronze_ | Datos sin transformar |
| Cleaned | silver_ | Deduplicados, tipados, validados |
| Business | gold_ | Listos para consumo |
| Staging | staging_ | Temporales de proceso |

## Template de COMMENT

```sql
-- Tabla
COMMENT ON TABLE production.gold.orders IS
  'Pedidos completados. Granularidad: 1 fila = 1 línea de pedido. '
  'Fuente: sistema ERP via pipeline diario (6AM UTC). '
  'Owner: equipo-comercial. Contacto: #data-sales en Slack.';

-- Columnas críticas
COMMENT ON COLUMN production.gold.orders.revenue IS
  'Ingreso neto en USD tras descuentos e impuestos. No incluye envío.';
COMMENT ON COLUMN production.gold.orders.order_date IS
  'Fecha de creación del pedido (timezone UTC). No es fecha de envío.';
```

## Tags obligatorios

```sql
ALTER TABLE production.gold.orders SET TAGS (
  'domain' = 'sales',
  'owner' = 'team-commercial',
  'sensitivity' = 'internal',
  'tier' = 'gold',
  'refresh_frequency' = 'daily'
);
```

## Métricas de cobertura

```sql
-- Dashboard: % de tablas documentadas
SELECT
  table_catalog, table_schema,
  COUNT(*) AS total_tables,
  COUNT_IF(comment IS NOT NULL AND comment != '') AS documented,
  ROUND(COUNT_IF(comment IS NOT NULL) * 100.0 / COUNT(*), 1) AS coverage_pct
FROM system.information_schema.tables
WHERE table_catalog = 'production'
  AND table_type = 'MANAGED'
GROUP BY table_catalog, table_schema
ORDER BY coverage_pct ASC
```

## Gotchas

* COMMENT ON TABLE tiene límite de 4096 chars. Ser conciso pero completo.
* COMMENTs se PIERDEN con DROP + CREATE TABLE. Usar ALTER TABLE para preservar. O incluir COMMENT en el CREATE.
* Tags son key-value strings (no typed). Definir vocabulario controlado en un documento de referencia.
* En Genie/BI, los COMMENTs aparecen como tooltips. Escribirlos para USUARIOS de negocio, no para developers.
* Coverage target: >85% de tablas gold con COMMENT. <50% = el catálogo es inútil para discovery.
* Los COMMENTs en columnas son más importantes que en tablas para Genie (ayudan a generar SQL correcto).
* NO documentar columnas internas (_ingested_at, _file_path, _rescued_data) — confunden a usuarios y a Genie.
