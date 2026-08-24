---
name: data-quality-contract-producer
description: Define y publica data contracts (SLAs de calidad) para tablas que produces — schema garantizado, freshness promise, completeness thresholds, y cómo notificar a consumidores de breaking changes. Úsala cuando necesites formalizar el acuerdo entre productor y consumidor de datos o gestionar cambios de schema sin romper downstream.
---

# Data Quality Contracts for Producers

Patrón para formalizar acuerdos de calidad entre productores y consumidores de datos usando Unity Catalog features.

## Componentes de un Data Contract

1. **Schema contract** — columnas garantizadas, tipos, nullability
2. **Freshness SLA** — cuándo estarán disponibles los datos
3. **Completeness** — % mínimo de filas no-null en columnas críticas
4. **Valid values** — dominios permitidos por columna
5. **Version & change policy** — cómo se notifican breaking changes

## Implementación en Unity Catalog

```sql
-- 1. Documentar contrato en COMMENT + TBLPROPERTIES
ALTER TABLE production.gold.orders SET TBLPROPERTIES (
  'data_contract.version' = '2.1',
  'data_contract.owner' = 'data-platform-team',
  'data_contract.freshness_sla' = '6h',
  'data_contract.consumers' = 'bi-team,ml-team,finance'
);

COMMENT ON TABLE production.gold.orders IS
  'Contract v2.1: Orders gold table. Freshness SLA: 6h. '
  'Breaking changes require 7-day notice to consumers. '
  'Contact: #data-platform-team on Slack.';

-- 2. Implementar validaciones como DLT expectations
-- (en el pipeline que produce la tabla)
@dlt.expect("completeness_customer_id", "customer_id IS NOT NULL")
@dlt.expect("valid_status", "status IN ('PENDING','COMPLETE','FAILED')")
@dlt.expect("freshness_within_24h", "order_date >= CURRENT_DATE() - 1")

-- 3. Crear monitor de completeness
CREATE OR REFRESH MONITOR production.gold.orders
WITH (
  SCHEDULE CRON '0 7 * * *',
  CUSTOM_METRICS (
    'null_rate_customer_id' = 'COUNT_IF(customer_id IS NULL) / COUNT(*)'
  ),
  ALERT_CONDITION 'null_rate_customer_id > 0.01'  -- <1% nulls
);

-- 4. Tag para discovery
ALTER TABLE production.gold.orders SET TAGS ('contract_tier' = 'gold', 'sensitivity' = 'internal');
```

## Breaking Change Workflow

1. Bump `data_contract.version` en TBLPROPERTIES
2. Publicar RFC en canal de Slack con 7 días de anticipación
3. Crear vista de compatibilidad temporal si es posible
4. Ejecutar cambio
5. Verificar que consumidores no tienen errores (lineage check)
6. Remover vista de compatibilidad después de 30 días

## Gotchas

* No hay "data contracts" nativos en Databricks — es un patrón construido sobre expectations + monitors + tags + TBLPROPERTIES.
* El COMMENT de tabla tiene límite de 4096 chars. Para contratos extensos, usar TBLPROPERTIES (sin límite práctico por key).
* Los consumidores deben subscribirse explícitamente (no hay push notification nativa). Usar un canal de Slack + tag `data_contract.consumers`.
* Un contrato roto (ej: freshness SLA breach) debe disparar alert automática. Combinar con skill `pipeline-observability-sla`.
* Para schemas dinámicos (ej: columnas nuevas de Auto Loader), el contrato debe especificar `additive_only: true` (nuevas columnas OK, nunca remover).
