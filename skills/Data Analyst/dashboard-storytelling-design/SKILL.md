---
name: dashboard-storytelling-design
description: Principios de diseño de dashboards orientados a storytelling — jerarquía visual, KPI trees, drill-down patterns, y cómo estructurar un dashboard para que un ejecutivo lo entienda en <30 segundos. Úsala cuando el analista tenga los datos pero no sepa cómo presentarlos efectivamente.
---

# Dashboard Storytelling & Design

Principios para crear dashboards que comuniquen insights, no solo datos.

## Estructura recomendada (top-down)

```
┌─────────────────────────────────────────────────┐
│ Row 1: KPIs principales (2-3 counters)          │
│ [Revenue Total] [vs Target %] [Trend arrow]     │
├─────────────────────────────────────────────────┤
│ Row 2: Contexto temporal (line chart)           │
│ [Revenue trend 12M con annotation de eventos]   │
├─────────────────────────────────────────────────┤
│ Row 3: Breakdown (bar + table)                  │
│ [Revenue by Region] [Top 10 Products table]     │
├─────────────────────────────────────────────────┤
│ Row 4: Filtros globales                         │
│ [Date range] [Region dropdown] [Category]       │
└─────────────────────────────────────────────────┘
```

## Reglas de diseño

1. **Un dashboard = una pregunta de negocio.** No mezclar "revenue" con "customer satisfaction".
2. **Máximo 6-8 widgets por página.** Más = cognitive overload.
3. **Jerarquía: Summary → Trend → Detail.** El ojo va de arriba-izquierda a abajo-derecha.
4. **Color con significado:** verde=positivo, rojo=negativo, gris=contexto. Nunca decorativo.
5. **Títulos descriptivos:** "Revenue creció 12% vs Q2" > "sum_revenue_chart".
6. **Conditional formatting** en counters: verde si ≥ target, rojo si < target.

## Anti-patterns

* ❌ Pie chart con >5 categorías (ilegible). Usar bar chart sorted.
* ❌ Tabla como primer widget (no es summary, es detalle).
* ❌ >3 KPIs en primera fila (overload visual).
* ❌ Colores inconsistentes entre páginas (misma dimensión = mismo color).
* ❌ Refresh automático <12h en este workspace (policy violation).

## Gotchas

* En AI/BI Lakeview: los counters soportan conditional formatting (target comparison con delta %).
* Los filtros globales deben estar ARRIBA o al LADO, nunca al final.
* Para drill-down: usar filtros interactivos (click on bar → filter other widgets).
* Width 6 = full page. Counters: width 2, height 3. Charts: width 3-4, height 5-6.
* Dashboard debe cargar en <5 segundos. Si tarda más: materializar queries o reducir scope.
