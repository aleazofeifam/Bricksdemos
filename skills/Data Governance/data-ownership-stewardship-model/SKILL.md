---
name: data-ownership-stewardship-model
description: Implementa un modelo de ownership de datos en UC — asignar owners a tablas/schemas, definir responsabilidades de stewards, crear workflow de solicitud de acceso, y escalar governanza sin bottleneck central. Úsala cuando nadie sepa quién es responsable de qué dato.
---

# Data Ownership & Stewardship Model

Modelo organizacional para escalar la gobernanza de datos sin bottleneck central.

## Roles definidos

| Rol | Responsabilidad | Implementación UC |
|-----|----------------|-------------------|
| Data Owner | Decide quién accede, aprueba cambios | OWNER de schema |
| Data Steward | Mantiene calidad, documenta, clasifica | Tag `steward` + grants de MODIFY |
| Data Consumer | Usa datos dentro de su permiso | SELECT grant |
| Platform Admin | Infraestructura, no decisiones de negocio | Account admin |

## Implementación

```sql
-- 1. Asignar ownership de schema al SP del dominio
ALTER SCHEMA production.finance OWNER TO `finance_platform_sp`;

-- 2. Tag con owner lógico (persona)
ALTER SCHEMA production.finance SET TAGS ('domain_owner' = 'carlos.martinez@company.com');
ALTER SCHEMA production.finance SET TAGS ('steward_team' = 'finance-data-stewards');

-- 3. Grants por rol
GRANT USE SCHEMA ON SCHEMA production.finance TO `finance_stewards`;
GRANT SELECT ON SCHEMA production.finance TO `finance_consumers`;
GRANT MODIFY ON SCHEMA production.finance TO `finance_stewards`;

-- 4. Detectar ownership huérfana
SELECT s.schema_name, s.schema_owner,
  t.tag_value AS domain_owner
FROM system.information_schema.schemata s
LEFT JOIN system.information_schema.schema_tags t
  ON s.catalog_name = t.catalog_name AND s.schema_name = t.schema_name
  AND t.tag_name = 'domain_owner'
WHERE t.tag_value IS NULL  -- Schemas sin owner asignado
```

## Workflow de solicitud de acceso

1. Consumer solicita acceso (Jira/Slack/form)
2. Steward del dominio revisa y aprueba
3. Platform admin ejecuta GRANT (o automatizar con SP + API)
4. Registrar en audit log custom

## Gotchas

* UC OWNER es un solo principal (no grupo). Usar un Service Principal por dominio como owner técnico.
* Cambiar OWNER requiere ser owner actual O admin. Si owner deja la empresa → tablas huérfanas.
* Crear alert: "schemas where domain_owner tag references email not in active directory" → ownership orphan.
* Ownership NO se hereda. Una tabla en schema `finance` owned por SP_finance puede tener owner diferente al schema.
* Usar tags para "logical owner" (persona responsable) vs UC OWNER (principal técnico con permisos).
* Revisión trimestral: recertificar que owners siguen vigentes y que grants corresponden a roles activos.
