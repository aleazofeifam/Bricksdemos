---
name: legacy-database-migration-patterns
description: Migrar datos desde bases legacy (Oracle, SQL Server, MySQL, PostgreSQL on-prem) a Unity Catalog usando Lakeflow Connect, JDBC bulk, o export/load. Mapeo de tipos, handling de stored procedures, y validación de integridad. Úsala para migraciones de datos de base de datos relacional a Databricks.
---

# Legacy Database Migration to Unity Catalog

Patrones para migrar datos de bases relacionales (Oracle, SQL Server, MySQL, PostgreSQL) a Delta tables en Unity Catalog.

## Decision Framework

| Método | Cuándo | Límites |
|--------|--------|--------|
| Lakeflow Connect | <250 tablas, SaaS/DB con conector soportado | No custom logic |
| JDBC Parallelized | Tablas grandes, necesitas control de partitioning | Requiere red accesible |
| Export + COPY INTO | Sin red directa, archivos exportados a bucket | Manual, no CDC |

## Patrón: JDBC Parallelized (máximo control)

```python
df = (spark.read.format("jdbc")
  .option("url", "jdbc:oracle:thin:@host:1521:ORCL")
  .option("dbtable", "SCHEMA.LARGE_TABLE")
  .option("user", dbutils.secrets.get("migration", "oracle_user"))
  .option("password", dbutils.secrets.get("migration", "oracle_pass"))
  .option("fetchSize", "10000")  # DEFAULT 10 es lentísimo
  .option("partitionColumn", "ID")  # PK numérica
  .option("lowerBound", "1")
  .option("upperBound", "10000000")
  .option("numPartitions", "20")
  .load())

df.write.format("delta").mode("overwrite").saveAsTable("production.raw.large_table")
```

## Mapeo de tipos críticos

| Source (Oracle) | Delta/Spark | Gotcha |
|----------------|-------------|--------|
| NUMBER(38,0) | DECIMAL(38,0) | No usar BIGINT (overflow) |
| DATE | TIMESTAMP | Oracle DATE incluye hora! |
| CLOB | STRING | Puede ser >2GB, truncar |
| RAW/BLOB | BINARY | Considerar Volume |
| VARCHAR2(4000) | STRING | OK directo |

| Source (SQL Server) | Delta/Spark | Gotcha |
|--------------------|-------------|--------|
| DATETIME2 | TIMESTAMP | OK |
| IDENTITY | BIGINT + GENERATED ALWAYS | No hay auto-increment nativo |
| NVARCHAR(MAX) | STRING | OK |
| BIT | BOOLEAN | OK |

## Validación post-migración

```sql
-- Comparar counts
SELECT 'source' AS origin, 1500000 AS row_count  -- valor del source
UNION ALL
SELECT 'delta', COUNT(*) FROM production.raw.large_table;

-- Checksum de columnas críticas
SELECT SUM(HASH(id, amount, created_date)) AS checksum
FROM production.raw.large_table;
```

## Gotchas

* Oracle DATE incluye hora (YYYY-MM-DD HH:MI:SS) — SIEMPRE mapear a TIMESTAMP, nunca a DATE de Spark.
* JDBC `fetchSize` default es 10 filas — cambiar a 10000+ para performance aceptable.
* `partitionColumn` DEBE ser numérica y con distribución uniforme. NO usar STRING ni DATE como partition column.
* Si no hay columna numérica buena: usar `ROWNUM` en subquery para Oracle, `ROW_NUMBER()` para SQL Server.
* SQL Server IDENTITY no existe en Delta — usar `GENERATED ALWAYS AS IDENTITY` en la tabla destino o `monotonically_increasing_id()` (no es secuencial).
* Lakeflow Connect OAuth (Salesforce) solo se configura en UI, no en CLI/DAB.
* Para stored procedures: NO hay equivalente directo — migrar lógica a notebooks o SQL scripting con `EXECUTE IMMEDIATE`.
* Validar SIEMPRE con COUNT + checksum. Diferencias comunes: NULLs tratados distinto, timezone conversions, trailing spaces en CHAR.
