---
name: pipeline-observability-sla
description: Define y operacionaliza SLIs, SLOs y observabilidad end-to-end para Lakeflow pipelines y sus productos de datos. Úsala para freshness SLAs, pipeline health, lag, backlog, quality monitoring, incident detection, operational dashboards, runbooks y análisis de degradaciones.
---

# Pipeline Observability & SLA

Un pipeline exitoso puede entregar datos incorrectos o atrasados.

Por eso separar:

```text
PIPELINE HEALTH
DATA HEALTH
CONSUMER HEALTH
```

---

# Observability dimensions

```text
1. Execution
2. Freshness
3. Data delay
4. Completeness
5. Quality
6. Backlog
7. Cost
8. Consumer impact
```

No medir únicamente SUCCESS/FAILED.

---

## 1. Define the consumer expectation

Ejemplo:

```text
Finance necesita ventas completas
antes de las 07:00 America/Costa_Rica
cada día hábil.
```

Convertirlo en SLIs.

---

## 2. Define SLIs

### Pipeline availability

```text
¿las actualizaciones necesarias completaron?
```

### Update duration

```text
¿cuánto tarda el pipeline?
```

### Data freshness

```text
¿hasta qué momento contienen datos los targets?
```

### Data delay

```text
availability_timestamp - event_timestamp
```

### Completeness

```text
¿se recibió el volumen esperado?
```

### Quality

```text
¿qué porcentaje/registros violaron rules?
```

### Backlog

```text
¿cuánto trabajo pendiente existe?
```

---

## 3. Define SLOs from business requirements

No inventar:

```text
1 hour
5%
99.9%
```

Derivarlos de:

- contract;
- business process;
- operational criticality.

Ejemplo:

```text
SLI:
MAX(ingestion_timestamp)

SLO:
debe contener información hasta T-60m
durante horario operacional.
```

---

## 4. Pipeline execution monitoring

Utilizar `system.lakeflow.pipeline_update_timeline` para análisis account-level cuando esté disponible.

Ejemplo conceptual:

```sql
SELECT
    workspace_id,
    pipeline_id,
    update_id,
    result_state,
    period_start_time,
    period_end_time
FROM system.lakeflow.pipeline_update_timeline
WHERE period_start_time >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS;
```

No asumir que el schema de system tables permanece idéntico indefinidamente.

Revisar documentación actual si cambia.

---

## 5. Pipeline event log

Utilizar el event log como fuente detallada para:

- progress;
- errors;
- expectation metrics;
- lineage;
- resource information.

Ejemplo:

```sql
SELECT
    timestamp,
    event_type,
    level,
    message,
    details
FROM event_log('<pipeline-id>')
WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY
ORDER BY timestamp DESC;
```

No inventar una tabla `system.lakeflow.pipeline_events`.

---

## 6. Measure data freshness from the data

Preferir una columna o criterio que represente la realidad del dato:

```text
ingested_at
event_timestamp
business_date
source watermark
expected partition
```

Ejemplo:

```sql
SELECT
    MAX(ingested_at) AS ultima_ingesta,
    CURRENT_TIMESTAMP() - MAX(ingested_at) AS retraso
FROM production.gold.orders;
```

Seleccionar la columna correcta para el contrato.

`last_altered` de metadata no es una medida universal de data freshness.

---

## 7. Data delay

Cuando existe event time:

```sql
SELECT
    percentile(
        unix_timestamp(ingested_at) - unix_timestamp(event_timestamp),
        0.95
    ) AS p95_delay_seconds
FROM production.silver.events
WHERE ingested_at >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY;
```

Adaptar la ventana y percentile al SLO real.

---

## 8. Streaming backlog

Para streaming revisar métricas disponibles en Pipeline UI.

Según source pueden incluir:

```text
backlog bytes
backlog records
backlog seconds
backlog files
```

No exigir la misma métrica para todos los sources.

---

## 9. Quality observability

Para expectations:

consultar event log y capturar tendencias de:

```text
passed
failed
dropped
flow failures
```

No limitar quality a contar filas finales.

---

## 10. Data Quality Monitoring

Para observabilidad amplia de activos de Unity Catalog evaluar anomaly detection.

Puede aportar:

- freshness anomaly;
- completeness anomaly;
- health indicators;
- downstream impact;
- root-cause hints.

Utilizarlo como complemento.

No sustituir un SLO determinístico crítico por un modelo de anomalía histórica.

---

## 11. Alert design

Crear alertas únicamente cuando exista acción.

Cada alerta debe tener:

```text
condition
severity
owner
channel
runbook
deduplication
resolution
```

Evitar:

```text
alerta
→ Slack
→ nadie responsable
```

---

## 12. Incident severity

Ejemplo conceptual:

```text
SEV1
critical consumers blocked

SEV2
SLO breach approaching/limited impact

SEV3
degradation without current consumer failure
```

Adaptar al proceso de la organización.

---

## 13. Event hooks

Evaluar event hooks cuando se requiera reacción custom basada en eventos del pipeline.

Mantenerlos:

- asynchronous-friendly;
- pequeños;
- sin lógica de transformación;
- observables.

No depender de event hooks para operaciones que necesiten guarantees transaccionales.

---

## 14. Operational dashboard

Mostrar como mínimo cuando resulte útil:

```text
current status
freshness
data delay
recent failures
duration trend
quality trend
backlog
cost
owner
```

No agregar métricas porque estén disponibles.

---

## 15. Cost observability

Relacionar pipeline metadata con billing/system data cuando el equipo necesite:

- unit economics;
- cost regression;
- inefficient jobs.

Performance y reliability pueden tener tradeoffs de costo.

---

## 16. Consumer impact

Para incidente importante identificar:

```text
downstream tables
Metric Views
dashboards
Genie Agents
models
applications
```

Priorizar incidentes por impacto y no sólo por qué pipeline falló.

---

## 17. Genie data freshness

Si un Genie Agent consume una tabla:

considerar su freshness SLA como parte de la readiness del agente.

Un agente puede responder SQL correctamente utilizando datos obsoletos.

No declarar el agente healthy únicamente porque responde preguntas.

---

## 18. AI observability gate

Si el pipeline o producto también ejecuta:

- LLM calls;
- agents;
- MCP tools;

la observabilidad del pipeline no sustituye la observabilidad de esas interacciones.

Evaluar Unity AI Gateway para tráfico, cost, access y behavior governance.

---

## 19. Runbook

Para cada alerta crítica documentar:

```text
symptom
dashboard/query
probable causes
diagnostic sequence
safe recovery
escalation
verification
```

---

## Output

```text
Product:

Consumer expectation:
- ...

SLIs:
- execution:
- freshness:
- delay:
- completeness:
- quality:
- backlog:
- cost:

SLOs:
- ...

Sources:
- system tables:
- event log:
- data:
- DQM:

Alerts:
- ...

Dashboard:
- ...

Runbook:
- ...

Consumer impact:
- ...
```

---

# Definition of Done

- [ ] Existe consumer expectation.
- [ ] Se definieron SLIs.
- [ ] Los SLOs provienen del negocio/contrato.
- [ ] Execution y data freshness están separados.
- [ ] Se utiliza pipeline update timeline cuando aplica.
- [ ] Se utiliza event log para observabilidad detallada.
- [ ] Freshness se mide desde un indicador de datos válido.
- [ ] Se revisó backlog en streaming.
- [ ] Se monitorean expectations.
- [ ] Se evaluó Data Quality Monitoring.
- [ ] Cada alerta tiene owner.
- [ ] Existe runbook.
- [ ] Se conoce downstream impact.
- [ ] Se contempla Genie como consumidor cuando aplica.
- [ ] Documentación está en español.

# Gotchas

- SUCCESS no garantiza freshness.
- Metadata `last_altered` no es un SLA de datos universal.
- Freshness y event delay son métricas diferentes.
- Data Quality Monitoring detecta anomalías; no reemplaza contratos.
- Alertas sin acción generan ruido.
- Un pipeline puede estar healthy mientras su source está atrasado.
