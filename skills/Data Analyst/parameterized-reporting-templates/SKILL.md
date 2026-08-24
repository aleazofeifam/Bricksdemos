---
name: parameterized-reporting-templates
description: Diseña reporting reutilizable y parametrizado en Databricks SQL y AI/BI Dashboards, incluyendo filtros, parámetros y distribución programada. Se usa cuando distintas audiencias necesitan variantes controladas del mismo reporte sin duplicar queries, dashboards o lógica de negocio.
---

# Parameterized Reporting Templates

Construye reporting reutilizable sin proliferar copias del mismo análisis.

## Principio

Antes de crear un reporte recurrente, decidir si el usuario necesita:

```text
explorar → Genie Agent

monitorear → AI/BI Dashboard

recibir → Dashboard subscription

extraer/intercambiar datos → workflow específico
```

No convertir toda pregunta recurrente en un email programado.

---

## 1. Discover

Identificar:

```text
Audiencia:
Decisión:
Frecuencia:
Canal:
Parámetros:
KPIs:
Periodo:
Frescura:
Necesidad de interacción:
Necesidad de archivo adjunto:
```

Preguntar también:

- ¿el destinatario realmente necesita recibir el reporte?
- ¿puede consultar el dato directamente?
- ¿requiere investigación posterior?

---

## 2. Validate semantic reuse

Antes de crear la query:

- buscar Metric Views;
- verificar KPIs;
- evitar duplicar fórmulas;
- utilizar dimensiones gobernadas.

Si cuatro reportes calculan `revenue` independientemente, el problema probablemente está en la capa semántica.

---

## 3. Parameterize the dataset

Ejemplo:

```sql
-- Reporte regional reutilizable.
SELECT
    DATE_TRUNC('WEEK', order_date) AS semana,
    region,
    MEASURE(total_revenue) AS ingreso_total,
    MEASURE(order_count) AS pedidos
FROM production.metrics.sales
WHERE region = :region
  AND order_date >= :start_date
  AND order_date < :end_date
GROUP BY
    DATE_TRUNC('WEEK', order_date),
    region
ORDER BY semana DESC;
```

Usar parámetros cuando el valor realmente cambia la consulta.

Usar field filters cuando sólo se necesita interacción sobre campos ya retornados.

No construir SQL mediante concatenación de strings con input del usuario.

---

## 4. Reuse instead of cloning

Default:

```text
1 dataset parametrizado
        ↓
1 dashboard/report reusable
        ↓
varios consumidores
```

Evitar:

```text
dashboard_latam
dashboard_emea
dashboard_apac
dashboard_nam
```

salvo que las audiencias tengan necesidades verdaderamente distintas.

---

## 5. Choose push vs pull

### Pull

El usuario entra a consultar.

Preferir:

- Genie;
- dashboard interactivo;
- link compartido.

### Push

El usuario necesita recibir información en un momento determinado.

Preferir las subscriptions nativas de AI/BI Dashboards cuando satisfagan el requerimiento.

No construir un notebook de email, webhook o exportación personalizada sin demostrar primero que las capacidades nativas son insuficientes.

---

## 6. Design each scheduled report

Definir:

```text
Owner:
Audiencia:
Motivo:
Schedule:
Timezone:
Dataset:
Parámetros:
Frescura esperada:
Canal:
Criterio de retiro:
```

Todo schedule debe tener owner.

Los reportes sin uso deben poder retirarse.

---

## 7. Validate recipient access

Antes de distribuir:

- revisar sensibilidad;
- revisar permisos;
- revisar datos visibles;
- revisar parámetros;
- comprobar que el resultado corresponde a la audiencia correcta.

No asumir que el hecho de poder generar un archivo implica que deba distribuirse.

---

## 8. Add conversational follow-up

Si el reporte genera recurrentemente preguntas como:

```text
¿Por qué cambió?
¿qué región explica esto?
¿qué clientes están detrás?
¿qué pasó la semana anterior?
```

evaluar proporcionar acceso al Genie Agent del mismo dominio.

Push para informar.

Genie para investigar.

---

## Output

```text
Reporte:
Owner:

Audiencia:
Canal:

KPIs:
- ...

Metric Views:
- ...

Parámetros:
- ...

Schedule:
- ...

Permisos:
- ...

Alternativa Genie:
- ...

Criterio de retiro:
- ...
```

---

## Databricks decision gates

### AI/BI Dashboards

Core.

### Metric Views

Aplicable para mantener KPIs consistentes.

### Genie Agents

Aplicable cuando los consumidores requieren follow-up analítico.

### Custom notebook/report pipeline

Sólo si las capacidades administradas no satisfacen el caso.

### Spark Declarative Pipelines

No usar para distribuir reportes. Delegar sólo si falta la transformación upstream.

### AI Functions

Aplicable si el reporte requiere enriquecimiento de texto o datos no estructurados.

### Lakebase

No forzar.

### Unity AI Gateway

No forzar.

---

## Definition of Done

- [ ] Está claro por qué el reporte debe existir.
- [ ] Existe owner.
- [ ] Los KPIs fueron verificados.
- [ ] Se revisaron Metric Views.
- [ ] La query reutiliza parámetros de forma segura.
- [ ] Se evitó duplicar dashboards innecesariamente.
- [ ] Se eligió conscientemente push o pull.
- [ ] Se evaluaron subscriptions nativas.
- [ ] Se revisaron permisos.
- [ ] Se evaluó Genie para preguntas posteriores.
- [ ] La documentación está en español.

## Gotchas

- No construir un sistema de distribución custom cuando existe una capacidad administrada suficiente.
- No duplicar lógica al personalizar por audiencia.
- No confundir refresh del dashboard con frecuencia de actualización del dato fuente.
- No mantener reportes sin owner.
- No enviar información sensible a destinatarios no autorizados.
