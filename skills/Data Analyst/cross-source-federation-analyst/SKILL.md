---
name: cross-source-federation-analyst
description: Permite consultar datos de múltiples fuentes sin moverlos — Lakehouse Federation (MySQL, PostgreSQL, SQL Server, Snowflake) + queries cross-catalog para analistas. Úsala cuando necesites combinar datos de sistemas externos con datos del lakehouse en una sola query.
---

# Cross-Source Federation for Analysts

Cómo combinar datos de múltiples fuentes en una sola query sin mover datos.

## Consultar tabla federada

```sql
-- Si ya existe el foreign catalog configurado:
SELECT
  f.opportunity_id,
  f.amount AS opp_amount,
  f.stage,
  l.customer_name,
  l.lifetime_value
FROM salesforce_catalog.public.opportunities f
JOIN production.gold.customers l
  ON f.account_id = l.sf_account_id
WHERE f.close_date >= CURRENT_DATE()
  AND f.stage IN ('Negotiation', 'Closed Won')
```

## Cuándo materializar vs federar

| Criterio | Federar (query directo) | Materializar (copiar a Delta) |
|----------|------------------------|-------------------------------|
| Frecuencia de uso | <3 queries/día | >3 queries/día |
| Tamaño de tabla remota | <1M filas | >1M filas |
| Latencia aceptable | >5 segundos OK | <2 segundos requerido |
| Frescura requerida | Real-time | Diaria OK |

## Materializar para uso frecuente

```sql
-- Scheduled job: copiar tabla remota a lakehouse diariamente
CREATE OR REPLACE TABLE production.staging.sf_opportunities AS
SELECT * FROM salesforce_catalog.public.opportunities
WHERE close_date >= CURRENT_DATE() - INTERVAL 90 DAYS;
```

## Gotchas

* Federation ejecuta filtros en la FUENTE solo si son pushable (equalities, ranges). JOINs entre foreign tables NO se pushean — se traen ambas tablas completas al cluster.
* Para JOINs cross-source: materializar la tabla MÁS PEQUEÑA primero, luego JOIN con la grande.
* La latencia depende de la fuente (red, carga del source DB), no del warehouse de Databricks.
* No todas las funciones SQL se pushean al source. Solo predicados básicos (=, <, >, IN, BETWEEN).
* Queries a foreign tables NO se cachean en DBSQL result cache.
* Si la foreign table cambia schema en el source, ejecutar `REFRESH FOREIGN SCHEMA` para sincronizar metadata.
* Para analistas: preferir vistas que encapsulen el JOIN foreign+local, así no necesitan saber qué es federado.
