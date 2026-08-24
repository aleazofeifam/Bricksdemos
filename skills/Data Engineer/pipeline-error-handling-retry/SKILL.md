---
name: pipeline-error-handling-retry
description: Diseña resiliencia y recuperación para pipelines de datos clasificando fallos de datos, código, infraestructura, sources externos, rate limits, checkpoints y writes no idempotentes. Úsala cuando un pipeline falle intermitentemente, necesite retry, quarantine, dead-letter handling, circuit breaking o una estrategia explícita de recuperación.
---

# Pipeline Error Handling & Retry

Retry no es una estrategia de error handling.

Primero clasificar el fallo.

---

# Failure taxonomy

```text
DATA ERROR
→ expectation / quarantine

DETERMINISTIC CODE ERROR
→ fix; no retry infinito

TRANSIENT PLATFORM ERROR
→ managed retry

SOURCE UNAVAILABLE
→ retry/backoff + source SLA

RATE LIMIT
→ bounded concurrency / connector

CHECKPOINT ERROR
→ supported checkpoint recovery

EXTERNAL SIDE EFFECT
→ idempotency

AI/MODEL/MCP ERROR
→ Unity AI Gateway + service policy / retry strategy
```

---

## 1. Capture the failure

Registrar:

```text
pipeline
flow/table
update ID
timestamp
error
source
last successful run
data range
consumer impact
```

Consultar primero:

- Pipeline UI;
- event log;
- system tables cuando corresponda.

No reaccionar únicamente al stack trace visible en un notebook.

---

## 2. Classify retryability

### Retryable

Ejemplos:

- temporary network issue;
- service unavailable;
- throttling;
- recoverable platform failure.

### Non-retryable

Ejemplos:

- syntax error;
- missing column after schema change;
- invalid business logic;
- deterministic assertion;
- permissions incorrectly configured.

No gastar compute haciendo retry de un error determinístico.

---

# Data quality failures

## Warn

Utilizar cuando el registro puede permanecer.

```python
@dp.expect(...)
```

## Drop

Cuando el registro no debe contaminar output:

```python
@dp.expect_or_drop(...)
```

## Fail

Cuando cualquier violación invalida el flujo:

```python
@dp.expect_or_fail(...)
```

## Quarantine

Cuando el dato inválido debe preservarse.

Mantener:

```text
payload
reason
source
timestamp
context
```

---

## 3. Do not confuse quality with exceptions

Expectations no capturan:

- API timeout;
- lost credentials;
- code bugs;
- network failure;
- checkpoint corruption.

No intentar modelarlos como constraints de filas.

---

## 4. Prefer managed retries

Para jobs/tasks:

utilizar configuración de retries de Lakeflow Jobs cuando el error sea retryable a nivel de task.

Para Lakeflow pipelines:

entender el comportamiento de retry del tipo de ejecución.

No implementar un loop Python adicional si la plataforma ya realiza retry del mismo boundary.

---

## 5. External APIs

Antes de realizar HTTP requests desde procesamiento distribuido preguntar:

```text
¿Existe Lakeflow Connect?
¿Existe un connector administrado?
¿Existe AI Function?
¿Puede hacerse batch?
¿La API soporta bulk requests?
¿Tiene rate limit?
¿Existe idempotency key?
```

Evitar:

```text
1 Spark row
→
1 HTTP request
```

como default.

Puede causar:

- request storms;
- throttling;
- cost explosion;
- nondeterminism;
- partial side effects.

---

## 6. AI Functions gate

Si el "API externo" es realmente un workload de:

- classification;
- extraction;
- summarization;
- masking;
- model inference;

evaluar primero AI Functions.

No implementar `requests.post()` a un LLM directamente desde executors como default.

---

## 7. Unity AI Gateway gate

Cuando sea necesario llamar:

- external LLMs;
- model APIs;
- MCP services;
- AI tools;

enrutar mediante Unity AI Gateway cuando la arquitectura lo permita.

Beneficios esperados:

```text
access control
credentials
routing
rate limits
spend controls
request tracking
service policies
```

El pipeline debe manejar únicamente la semántica de éxito/fallo necesaria para su workflow.

---

## 8. Bounded retry

Si un retry custom sigue siendo necesario definir:

```text
max attempts
initial delay
backoff
maximum delay
timeout
jitter
retryable status codes
terminal status codes
```

No incluir números universales en la skill.

Derivarlos del SLA y del servicio.

---

## 9. Idempotency

Antes de hacer retry de una operación con side effects responder:

```text
¿qué pasa si la operación anterior sí terminó
pero nosotros no recibimos la confirmación?
```

Diseñar:

- natural keys;
- idempotency keys;
- batch IDs;
- upserts;
- deduplication.

---

## 10. Checkpoint failure

No arreglar mediante retry repetitivo.

Invocar el patrón de recovery/backfill.

Opciones soportadas pueden incluir:

- full refresh;
- backup + backfill;
- selective checkpoint reset.

No manipular archivos internos del checkpoint.

---

## 11. Quarantine lifecycle

Una quarantine sin proceso de resolución se convierte en cementerio.

Definir:

```text
owner
review
remediation
replay
retention
closure
```

Medir tendencia.

No utilizar un número fijo de registros como alerta universal.

---

## 12. Alerts

Alertar por impacto, no por existencia de cualquier error.

Clasificar:

```text
INFO
WARNING
ACTION REQUIRED
CRITICAL
```

Evitar alert fatigue.

---

## 13. Event hooks

Usar event hooks sólo cuando se necesita una acción custom sobre eventos del pipeline.

No utilizarlos como lógica de transformación.

Mantener callbacks:

- pequeños;
- rápidos;
- tolerantes a fallo.

---

## 14. Error budget

Para pipelines críticos definir:

```text
availability objective
freshness objective
allowed failures
recovery time
```

Utilizar estos objetivos para decidir cuándo escalar.

---

## Output

```text
Failure:
Classification:

Retryable:
- yes/no

Data impact:
- ...

Consumer impact:
- ...

Recovery:
- ...

Retry:
- ...

Idempotency:
- ...

Quarantine:
- ...

Alert:
- ...

Root cause:
- ...

Permanent prevention:
- ...
```

---

# Definition of Done

- [ ] El error fue clasificado.
- [ ] Se identificó si es retryable.
- [ ] No se hace retry infinito.
- [ ] Los errores de datos tienen policy explícita.
- [ ] Quarantine tiene lifecycle.
- [ ] Los side effects son idempotentes.
- [ ] Se utilizaron retries administrados cuando aplican.
- [ ] Se evitó request-per-row distribuido salvo justificación.
- [ ] Se evaluaron AI Functions para workloads IA compatibles.
- [ ] Se evaluó Unity AI Gateway para tráfico AI.
- [ ] Los checkpoint failures siguen recovery soportado.
- [ ] Existe monitoreo posterior.
- [ ] El runbook está documentado en español.

# Gotchas

- Retry puede amplificar una caída.
- `429` no significa que debamos añadir más executors.
- Una quarantine sin owner no resuelve nada.
- Un timeout no demuestra que el servicio remoto no procesó la solicitud.
- Exactly-once termina donde aparece un sink externo no idempotente.
- Expectation failure y infrastructure failure son problemas diferentes.
