---
name: cost-attribution-chargeback
description: Diseña cost attribution, showback, chargeback y FinOps para workloads de Databricks usando system.billing, list prices, custom tags, serverless usage policies, budgets y Unity AI Gateway cost controls. Úsala para identificar quién consume qué, asignar costos por equipo/proyecto/producto, gobernar AI spend, construir budgets o reducir consumo no atribuible.
---

# Cost Attribution & Chargeback

Antes de chargeback se necesita attribution confiable.

# Maturity model

```text
Visibility
   ↓
Attribution
   ↓
Showback
   ↓
Budgeting
   ↓
Optimization
   ↓
Chargeback
```

No comenzar facturando internamente cuando los datos de attribution son incompletos.

---

# 1. Define cost dimensions

Determinar qué necesita Finance/Platform:

```text
business unit
team
project
product
environment
cost center
customer
workload
application
AI use case
```

No crear tags porque "pueden ser útiles".

Cada dimensión debe tener consumer.

---

# 2. Tag taxonomy

Definir vocabulario.

Ejemplo:

```text
cost_center
business_unit
project
environment
product
```

Determinar:

```text
required
optional
allowed values
owner
source of truth
```

No utilizar información sensible en tags.

---

# 3. Default vs custom tags

Distinguir:

```text
Databricks default tags
custom tags
serverless usage-policy tags
AI Gateway service/request tags
```

No asumir que todos los workloads reciben tags de la misma manera.

---

# 4. Serverless attribution

Para serverless notebooks, jobs, pipelines o apps:

evaluar **serverless usage policies**.

Estas policies pueden aplicar custom tags que luego aparecen en:

```text
system.billing.usage.custom_tags
```

Usarlas cuando se necesita atribución consistente.

---

# 5. Billing source of truth

Utilizar:

```text
system.billing.usage
```

para billable usage.

Campos útiles incluyen:

```text
workspace_id
sku_name
usage_quantity
usage_unit
billing_origin_product
usage_type
custom_tags
usage_metadata
identity_metadata
product_features
```

No reducir la tabla a cluster_id + DBUs.

---

# 6. Pricing

Utilizar:

```text
system.billing.list_prices
```

para list-price analysis.

Ejemplo conceptual:

```sql
SELECT
    u.workspace_id,
    u.billing_origin_product,
    u.sku_name,
    u.custom_tags['cost_center'] AS cost_center,
    SUM(
        u.usage_quantity *
        p.pricing.effective_list.default
    ) AS list_cost_usd
FROM system.billing.usage AS u
JOIN system.billing.list_prices AS p
    ON u.sku_name = p.sku_name
   AND u.usage_end_time >= p.price_start_time
   AND (
       p.price_end_time IS NULL
       OR u.usage_end_time < p.price_end_time
   )
WHERE u.usage_date BETWEEN :start_date AND :end_date
GROUP BY
    u.workspace_id,
    u.billing_origin_product,
    u.sku_name,
    u.custom_tags['cost_center'];
```

Validar schema vigente antes de utilizarlo productivamente.

---

# 7. List price vs contractual cost

Etiquetar claramente:

```text
LIST COST
```

cuando se utiliza `system.billing.list_prices`.

Si Finance necesita net/contractual allocation:

incorporar:

```text
discounts
commit agreements
credits
currency
tax
cloud costs
```

desde las fuentes financieras apropiadas.

No llamar:

```text
actual_cost
```

a list price si no representa el invoice real.

---

# 8. Attribution confidence

Para cada usage record clasificar:

```text
DIRECTLY ATTRIBUTED
INFERRED
SHARED
UNATTRIBUTED
```

Ejemplo:

```text
custom cost_center tag
→ direct

owner-derived team
→ inferred

shared SQL warehouse
→ shared

missing tags/metadata
→ unattributed
```

Esto permite comunicar calidad de chargeback.

---

# 9. Untagged workload

No establecer:

```text
<5%
```

como threshold universal.

Medir:

```text
unattributed spend
as % of total spend
```

y definir target según madurez.

Priorizar los mayores montos sin attribution.

---

# 10. Shared cost allocation

Para recursos compartidos elegir rule explícita:

```text
usage
queries
users
storage
revenue
equal split
central IT
```

No ocultar shared cost distribuyéndolo arbitrariamente.

Documentar allocation rule.

---

# 11. Showback

Antes de chargeback entregar:

```text
team
cost
drivers
top resources
trend
unattributed
forecast
```

y permitir que owners validen attribution.

Correcciones durante showback mejoran la calidad antes de internal billing.

---

# 12. Budgets

Utilizar Databricks budgets cuando corresponda.

Pueden filtrarse por:

```text
workspace
product/resource type
custom tags
```

Definir:

```text
budget owner
amount
thresholds
recipients
response action
```

No considerar un budget como hard enforcement para todos los workload types.

---

# 13. Governance Hub

Evaluar Governance Hub para:

```text
cost overview
spend drivers
tagged spend
budgets
```

cuando la organización administre FinOps desde UI.

Custom SQL sigue siendo útil para análisis específicos.

---

# 14. Serverless policy governance

Auditar:

```text
who manages policies
who is assigned
which tags apply
policy changes
unassigned workloads
```

Policy changes aplican al uso futuro.

No esperar retroactive tagging.

---

# 15. Jobs

Para cost attribution de jobs utilizar:

```text
usage_metadata
job metadata
identity_metadata
tags
```

Correlacionar con system tables cuando se necesita contexto adicional.

---

# 16. SQL

Para SQL warehouses analizar:

```text
warehouse
query workload
users
teams
```

Shared warehouse allocation debe tener regla explícita.

---

# 17. Model Serving

Model Serving puede atribuirse mediante:

```text
endpoint metadata
custom tags
billing usage
```

Separar:

```text
CPU/GPU serving
foundation models
pay-per-token
```

según SKU/product.

---

# 18. Unity AI Gateway

AI Gateway debe convertirse en una dimensión importante de FinOps.

Analizar:

```text
model service
destination model
principal
team
project
request/service tags
token usage
cost
MCP usage where applicable
```

El objetivo es poder responder:

```text
¿Quién está gastando?
¿Con qué modelo?
¿Para qué use case?
¿A través de qué servicio?
```

---

# 19. AI Gateway budgets

Evaluar budgets específicos de Unity AI Gateway.

Pueden proporcionar:

```text
monthly spend tracking
per-user thresholds
per-user overrides
hard blocking when configured
```

Esto es governance activo, no sólo reporting.

---

# 20. AI cost policy

Definir:

```text
approved models
high-cost models
rate limits
user thresholds
team budgets
exceptions
```

No utilizar cost control para impedir workflows críticos sin fallback/process.

---

# 21. MCP cost/usage

Para MCP Services monitorizar:

```text
who invokes
how often
which tools
downstream service cost
```

El costo fuera de Databricks puede no estar reflejado completamente en Databricks billing.

No declarar AI Gateway billing como costo total del SaaS externo.

---

# 22. Lakebase

Custom tags también pueden utilizarse para cost attribution de database instances/Lakebase resources donde la plataforma lo soporte.

Separar:

```text
operational DB cost
```

de:

```text
analytics cost
```

para evitar atribución engañosa.

---

# 23. Cost anomaly

Detectar cambios respecto de baseline:

```text
team
SKU
job
endpoint
model
project
```

Investigar:

```text
volume growth
schedule change
new model
retry loop
runaway query
new user
tag change
```

No marcar toda variación porcentual alta como anomalía si el baseline era pequeño.

---

# 24. Unit economics

Cuando sea útil calcular:

```text
cost per pipeline run
cost per TB processed
cost per query
cost per forecast
cost per model training
cost per AI request
cost per customer
```

Esto permite optimizar valor y no sólo gasto absoluto.

---

# 25. Chargeback rules

Para chargeback documentar:

```text
source of cost
price basis
allocation method
shared costs
credits
exceptions
currency
rounding
billing period
```

Finance debe poder reproducir el cálculo.

---

# Output

```text
Period:

Cost basis:
- list
- contractual
- blended

Taxonomy:
- ...

Attribution:
- direct:
- inferred:
- shared:
- unattributed:

Spend:
- BU:
- team:
- project:
- workload:

AI:
- model services:
- users:
- Gateway:
- budgets:

Shared-cost rule:
- ...

Budgets:
- ...

Anomalies:
- ...

Unit economics:
- ...

Actions:
P0:
P1:
P2:
```

# Definition of Done

- [ ] Cost dimensions están definidas.
- [ ] Tag taxonomy existe.
- [ ] Sensitive values no están en tags.
- [ ] system.billing.usage es source principal de usage.
- [ ] list_prices se utiliza para list-price analysis.
- [ ] List vs contract cost está claramente diferenciado.
- [ ] Attribution confidence está calculada.
- [ ] Shared cost tiene allocation rule.
- [ ] Unattributed cost está cuantificado.
- [ ] Serverless usage policies fueron evaluadas.
- [ ] Budgets fueron evaluados.
- [ ] Model Serving está incluido cuando aplica.
- [ ] Unity AI Gateway spend está incluido.
- [ ] Per-user AI budgets fueron evaluados.
- [ ] Lakebase está incluido cuando consume presupuesto.
- [ ] Chargeback es reproducible.
- [ ] Documentación está en español.

# Gotchas

- DBU no es USD.
- List price no necesariamente equivale al precio contractual.
- Tags no son retroactivos.
- Un resource shared necesita allocation rule.
- AI Gateway cost puede no incluir el costo externo total de una herramienta SaaS.
- Tags no deben contener PII o secretos.
- Chargeback con attribution incompleta crea falsa precisión.

system.billing.usage hoy incluso distingue tipos de uso como compute, storage, network, API operations, tokens y GPU time; system.billing.list_prices proporciona el pricing histórico para calcular list cost.
