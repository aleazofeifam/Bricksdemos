---
name: compliance-framework-uc-mapping
description: Mapea controles de compliance (SOC2, ISO27001, GDPR, leyes de protección de datos LATAM) a funcionalidades de Unity Catalog — grants, audit logs, tags, row filters, encryption. Úsala cuando compliance pregunte cómo demostrar que cumples un control específico.
---

# Compliance Framework → Unity Catalog Mapping

Cómo demostrar cumplimiento regulatorio con capabilities de Databricks.

## SOC2 Trust Services Criteria → UC

| Control SOC2 | Capability UC | Evidencia |
|-------------|--------------|-----------|
| CC6.1 Access Control | Grants + ABAC + Row Filters | `SHOW GRANTS ON` + system.access.audit |
| CC6.2 Authentication | SSO + MFA (Okta) | Workspace settings audit |
| CC6.3 Access Removal | REVOKE + SCIM deprovisioning | Grant history in audit log |
| CC7.2 Monitoring | System tables + alerts | Dashboard de anomalías |
| CC8.1 Change Management | Lineage + Git + DABs | table_lineage + git history |

## GDPR Art. 17 (Right to Erasure)

```sql
-- Implementar derecho al olvido
-- 1. Borrar datos del sujeto
DELETE FROM production.gold.customers WHERE customer_id = 'GDPR-REQUEST-123';
DELETE FROM production.gold.orders WHERE customer_id = 'GDPR-REQUEST-123';

-- 2. Purgar de time travel (obligatorio para GDPR completo)
REORG TABLE production.gold.customers APPLY (PURGE);
REORG TABLE production.gold.orders APPLY (PURGE);

-- 3. Registrar la acción para evidencia
INSERT INTO production.compliance.erasure_log
VALUES ('GDPR-REQUEST-123', CURRENT_TIMESTAMP(), 'completed', CURRENT_USER());
```

## Dashboard de evidencia para auditor

```sql
-- Query: accesos a datos confidenciales últimos 30 días
SELECT
  user_identity.email AS who,
  request_params.full_name_arg AS what_table,
  action_name AS what_action,
  event_date AS when_date,
  COUNT(*) AS access_count
FROM system.access.audit
WHERE action_name IN ('getTable', 'commandSubmit')
  AND event_date >= CURRENT_DATE() - 30
GROUP BY ALL
ORDER BY access_count DESC
```

## Gotchas

* GDPR "right to erasure": DELETE simple NO basta — Delta time travel retiene datos 7 días. Usar REORG PURGE.
* `VACUUM RETAIN 0 HOURS` es alternativa pero PELIGROSA (queries concurrentes fallan). REORG PURGE es más seguro.
* Audit logs (system.access.audit) retienen 365 días por defecto. Suficiente para la mayoría de frameworks.
* Los grants a grupos se resuelven en runtime — no hay API de "effective permissions". Hay que computar membership × grants manualmente.
* Para SOC2 "change management": el lineage muestra quién ACCEDIÓ, no quién CAMBIÓ. Para cambios: usar Git history del bundle.
* Leyes LATAM (Ley 19.628 Chile, LFPDPPP México, LGPD Brasil): similares a GDPR pero con variaciones en plazos y sanciones. Mapear individualmente.
