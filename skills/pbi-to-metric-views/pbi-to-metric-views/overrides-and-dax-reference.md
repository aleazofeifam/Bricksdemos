# Overrides schema and DAX coverage

Power Query (M), calculated columns/tables, RLS and refresh rules are in
[process-migration.md](process-migration.md); LLM fallback/review rules in
[llm-translation.md](llm-translation.md).

## Overrides (dict passed to `run_migration(overrides=...)`)

Same schema as the repo's `overrides.example.yaml`. All keys optional.

```python
overrides = {
  "target": {"catalog": "main", "schema": "gold"},          # overrides catalog/schema args
  "table_mappings": {                                         # PBI table -> UC table
      "FactSales": "gold.fact_sales",                         # schema.table or catalog.schema.table
      "DimProduct": "dim_product"},                           # bare name -> target catalog.schema
  "column_mappings": {"FactSales": {"SalesAmount": "sales_amount"}},
  "extra_joins": [{"from_table": "FactSales", "from_column": "region_code",
                   "to_table": "DimRegion", "to_column": "code"}],
  "exclude_joins": [{"from_table": "FactSales", "to_table": "DimTemp"}],
  "exclude_tables": ["TempTable"],
  "exclude_columns": {"FactSales": ["etl_batch_id"]},
  "exclude_measures": ["_Internal Calc", "Debug *"],         # glob patterns supported
  "measure_overrides": {                                      # hand-written SQL; alias fact table as `source`
      "Complex KPI": {"expr": "SUM(source.revenue) / NULLIF(COUNT(DISTINCT source.customer_id), 0)",
                      "comment": "Manual translation"},
      "Sales PY": {"expr": "SUM(source.amount)",                 # optional v1.1 window list
                   "window": [{"order": "ytd_date", "range": "current", "offset": "-1 year"}]}},
  "dimension_overrides": {"ProductName": {"display_name": "Product", "description": "..."}},
}
```

Notes:
* In `measure_overrides`, reference the fact table as `source.<col>` and joined tables as
  `j_<pbi_table_lowercase>.<col>` (the driver prefixes join aliases with `j_`). Override
  expressions are NOT column-remapped - use the real UC column names.
* `merge_fact_groups` from the repo schema is parsed but not implemented; build a combined
  source table/view first and point `table_mappings` at it.

## Translation status and confidence

* `converted` - fully translated; confidence starts at 100, -20 per issue, -5 per warning,
  -15 per residual DAX pattern.
* `partial` - some DAX remains or a time-intelligence window could not be placed -> review.
* `unsupported` - empty or untranslatable -> write a `measure_overrides` entry.
* `manual_override` - came from overrides.
* `needs_review` = not converted/manual OR confidence < 80.

## DAX coverage (repo engine)

| Category | Functions | Status |
|---|---|---|
| Aggregations | SUM, AVERAGE, MIN, MAX, COUNT, DISTINCTCOUNT, COUNTROWS, COUNTBLANK | Supported |
| Logical | IF, AND, OR, NOT, SWITCH, IFERROR, ISBLANK | Supported |
| Math | DIVIDE (2/3 args -> NULLIF/COALESCE) | Supported |
| Filter | CALCULATE, FILTER(ALL(...)), simple column filters | Supported (verify) |
| Relationship | RELATED, SELECTEDVALUE | Supported |
| Text | CONCATENATE, CONTAINSSTRING | Supported |
| Date | TODAY, EOMONTH, EDATE, DATEDIFF, DATEADD | Supported |
| Time intelligence | TOTALYTD / DATESYTD -> window measure (cumulative ytd_date + current ytd_year) | Supported by driver |
| Variables | VAR / RETURN inlining | Supported |
| Iterators | SUMX, COUNTX, AVERAGEX | Supported (verify row context) |
| Measure refs | [Measure] cross-references (resolved up to 5 passes) | Supported |
| Semi-additive | FIRSTNONBLANK, LASTNONBLANK, OPENINGBALANCE | Rules: unsupported -> LLM fallback (window `semiadditive`) |
| Path hierarchy | PATH, PATHITEM, PATHCONTAINS | Rules: unsupported -> LLM fallback or flatten the hierarchy in the pipeline |

Every measure (converted or not) also gets an LLM semantic review (see llm-translation.md).

Manual translation hints (Metric View idioms):
* `CALCULATE(SUM(x), T[c] = "v")` -> `SUM(x) FILTER (WHERE c = 'v')`
* `[A] / [B]` -> `MEASURE(`A`) / MEASURE(`B`)`
* `SAMEPERIODLASTYEAR` -> window `range: current` + `offset: -1 year` on a month/date dimension
* `ALL(T)` percent-of-total -> Fixed LOD dimension `SUM(x) OVER ()` + `ANY_VALUE()`

## Known repo gaps fixed by the driver

* Pipeline ignored table/column mappings, measure/dimension overrides, extra/excluded joins.
* `validate_ddl()` fails on its own generated DDL (indentation) - driver validates YAML body.
* Engine window `{range, order_by, group_by}` is invalid Metric View syntax.
* PyYAML reads `on:` as `True`.
* Join alias equal to a dimension name (e.g. `date`) fails with INVALID_EXTRACT_BASE_FIELD_TYPE.
* App UI bugs (validate sends `sql` instead of `ddl`; dashboard step depends on deploy and on an
  empty `fact_groups`) are avoided by not using the app.
