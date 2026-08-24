---
name: sensitive-data-discovery-remediation
description: Descubre datos sensibles a escala en Unity Catalog — escaneo automático con ai_classify + regex, clasificación por sensibilidad, y remediación (mask, restrict, tag). Úsala cuando necesites un inventario de PII/PHI/PCI en un catálogo completo o detectar columnas sensibles en tablas nuevas.
---

# Sensitive Data Discovery & Remediation

Workflow para escanear, clasificar y remediar datos sensibles a escala.

## Paso 1: Escaneo con regex + ai_classify

```sql
-- Detectar columnas candidatas a PII por nombre
SELECT table_catalog, table_schema, table_name, column_name
FROM system.information_schema.columns
WHERE table_catalog = 'production'
  AND (column_name RLIKE '(?i)(email|phone|ssn|rut|curp|cpf|cedula|passport|credit_card|tarjeta)'
       OR column_name RLIKE '(?i)(nombre|apellido|direccion|address|dob|birth)')
ORDER BY table_schema, table_name;
```

```sql
-- Confirmar con ai_classify en sample
SELECT column_name,
  ai_classify(
    CONCAT('Column name: ', column_name, '. Sample values: ',
           CONCAT_WS(', ', COLLECT_LIST(CAST(value AS STRING)))),
    ARRAY('PII_email', 'PII_phone', 'PII_national_id', 'PII_name', 'PII_address', 'financial', 'not_sensitive')
  ) AS classification
FROM (
  SELECT column_name, value
  FROM table TABLESAMPLE (100 ROWS)
  UNPIVOT (value FOR column_name IN (col1, col2, col3))
)
GROUP BY column_name
```

## Paso 2: Remediar

```sql
-- Aplicar mask automático a columnas PII detectadas
CREATE OR REPLACE FUNCTION production.security.mask_pii(v STRING)
RETURNS STRING
RETURN CASE WHEN is_account_group_member('pii_readers') THEN v
            ELSE CONCAT(LEFT(v, 2), '***', RIGHT(v, 2)) END;

ALTER TABLE production.crm.customers
  ALTER COLUMN email SET MASK production.security.mask_pii;
ALTER TABLE production.crm.customers
  ALTER COLUMN phone SET MASK production.security.mask_pii;

-- Tag para tracking
ALTER TABLE production.crm.customers ALTER COLUMN email SET TAGS ('sensitivity' = 'confidential');
```

## Gotchas

* ai_classify tiene costo por invocación — NO escanear todas las filas. Sample de 100 es suficiente para detección.
* Regex de RUT chileno: `[0-9]{7,8}-[0-9Kk]`. CURP mexicano: `[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2}`. CPF brasileño: `[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}`. Incluir patterns LATAM.
* El escaneo debe ser INCREMENTAL (solo tablas nuevas/modificadas). Usar `last_altered` de information_schema.
* Columnas con nombres genéricos (col_1, value, data) son candidatas — NO asumir que nombre = contenido.
* La función de mask recibe el valor y DEBE devolver el MISMO tipo (STRING→STRING, no STRING→NULL).
* El masking aplica en Genie, dashboards, views — no hay bypass accidental.
* Coverage metric: `(columns_tagged / total_string_columns) * 100`. Target: >90% de tablas gold.
