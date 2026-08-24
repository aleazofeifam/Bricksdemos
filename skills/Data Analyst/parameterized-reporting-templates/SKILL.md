---
name: parameterized-reporting-templates
description: Templates de reportes parametrizados en Databricks SQL — queries con parámetros dinámicos, scheduled reports por audiencia, y distribución automática de insights. Úsala cuando necesites enviar reportes personalizados a distintos stakeholders sin duplicar queries.
---

# Parameterized Reporting Templates

Cómo crear reportes dinámicos que se adapten por audiencia sin duplicar lógica.

## Query con parámetros

```sql
-- Parámetros: :region, :start_date, :end_date
SELECT
  DATE_TRUNC('WEEK', order_date) AS week,
  region,
  COUNT(DISTINCT customer_id) AS unique_customers,
  SUM(amount) AS revenue,
  AVG(amount) AS avg_order_value
FROM production.gold.orders
WHERE region = :region
  AND order_date BETWEEN :start_date AND :end_date
GROUP BY week, region
ORDER BY week DESC
```

## Distribución por audiencia (Job notebook)

```python
regions = ["LATAM", "EMEA", "APAC", "NAM"]
recipients = {"LATAM": "cfo-latam@co.com", "EMEA": "cfo-emea@co.com"}

for region in regions:
    # Ejecutar query parametrizada
    report_df = spark.sql(f"""
      SELECT * FROM production.gold.weekly_summary
      WHERE region = '{region}'
        AND week >= DATE_TRUNC('WEEK', CURRENT_DATE() - INTERVAL 4 WEEKS)
    """)

    # Guardar como CSV en Volume
    path = f"/Volumes/production/reports/weekly/{region}_{today}.csv"
    report_df.toPandas().to_csv(path, index=False)

    # Notificar (via webhook o email API)
    print(f"Report for {region} saved to {path}")
```

## Gotchas

* Los parámetros de Databricks SQL NO soportan listas dinámicas. `WHERE region IN (:regions)` con multi-select no funciona. Usar ARRAY_CONTAINS o string parsing.
* Scheduled dashboards envían snapshot estático (imagen), no interactivo. Para interactivo: compartir link con filtro pre-aplicado.
* Para PDF export: usar la API `POST /api/2.0/sql/dashboards/{id}/export` (no es self-service aún).
* Si el reporte necesita lógica condicional compleja, usar notebook + job en vez de dashboard parametrizado.
* Los parámetros de fecha deben tener DEFAULT value para que el schedule funcione sin intervención humana.
* Following workspace policies: scheduled refresh no menor a 12 horas.
