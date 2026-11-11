---
name: pbi-to-metric-views
description: End-to-end, cloud-agnostic Power BI to Databricks migration inside Genie Code - semantic model (DAX measures, relationships) to Unity Catalog Metric Views, Power Query (M)/dataflows to Lakeflow Spark Declarative Pipelines, calculated columns/tables, RLS roles to UC row filters, dataset refresh to a Lakeflow Job, and report pages to an AI/BI dashboard, with LLM fallback and semantic review via ai_query on a frontier system.ai model. Use when the user asks to migrate/convert Power BI, PBI, PBIX, TMDL, .bim, DAX, Power Query, dataflows, PBI RLS or PBI refreshes to Databricks, or mentions the pbi-metrics-migration-tool.
---

# Power BI -> Databricks: semantic model + processes (any cloud)

Migrates everything a Power BI solution contains, directly from Genie Code (no app deploy):

| Power BI | Databricks | Script |
|---|---|---|
| DAX measures + relationships | UC Metric Views (YAML v1.1) | `scripts/pbi_migrate.py` |
| Power Query (M) partitions / dataflows | Lakeflow SDP materialized views | `scripts/process_migrate.py` |
| Calculated columns / tables | SDP columns / MVs | `scripts/process_migrate.py` |
| RLS roles | UC row-filter functions | `scripts/process_migrate.py` |
| Dataset refresh schedule | Lakeflow Job (pipeline task) | `scripts/process_migrate.py` |
| Report pages / visuals (.pbix) | AI/BI dashboard | dashboard page hand-off |
| Anything rules cannot convert + review of every measure | `ai_query` on a frontier model | `scripts/llm_models.py`, `scripts/llm_translate.py` |

References: [questions.md](questions.md) (the question round), [process-migration.md](process-migration.md),
[llm-translation.md](llm-translation.md), [cloud-portability.md](cloud-portability.md),
[overrides-and-dax-reference.md](overrides-and-dax-reference.md).
Also load the built-in skills when you reach their phase: `metric-views` (YAML by hand),
`spark-declarative-pipelines` (pipeline), `edit-job-settings` (job), `sql-functions` (ai_query).

## Operating rules

* **Ask questions only at the start** (Phase 0, one `askUserQuestions` round, max 5 questions,
  plus a `volumeUpload` question if a file is needed). The answers include WHICH objects may be
  created. After that, run every phase without further prompts. Ask again only if a required
  value is genuinely missing (e.g. a UC table cannot be found) or a write would overwrite an
  existing object the user did not list.
* **Never** hard-code workspace URLs, user names, catalogs or model endpoints - resolve them at
  runtime (see [cloud-portability.md](cloud-portability.md)).
* Secrets (Power BI service principal) only via `dbutils.secrets.get`; never print or store them.
* Prove every generated object with a real CREATE in a scratch schema + a query before deploying.

## Setup (every run)

```python
user = spark.sql("SELECT current_user()").first()[0]
SKILL = f"/Workspace/Users/{user}/.assistant/skills/pbi-to-metric-views"
for f in ("pbi_migrate", "process_migrate", "llm_models", "llm_translate"):
    exec(open(f"{SKILL}/scripts/{f}.py").read())
P = default_paths()   # repo_path, repo_exists, user_schema_guess
```
If `P["repo_exists"]` is False, clone the engine with `runGit` (operation `clone`,
url `https://github.com/suryasai87/pbi-metrics-migration-tool`, provider `gitHub`,
path `P["repo_path"]`). The repo has no explicit license, so it is cloned, not copied.
`pyyaml` is preinstalled on serverless; `%pip install msal` only for live Power BI extraction.

## Phase 0 - Single question round

Before asking, discover what you can: `list_frontier_models()` (LLM candidates),
warehouses/catalogs via `databricksApi`, current user schema. Then ask the round in
[questions.md](questions.md): model source, target catalog/schema (+ scratch schema), which
artifacts to migrate/create, LLM model, RLS group mapping/admin group, refresh schedule.
Details of what to collect (recommended defaults pre-selected):
1. **Model source** (one of):
   * TMDL export: `.zip`, single `.tmdl`, or a TMDL folder - in a UC Volume or workspace path.
     If the user has the file locally, use `askUserQuestions` with `type: volumeUpload`.
   * Live Power BI dataset: `workspace_id`, `dataset_id`, plus a service principal whose
     `tenant_id`/`client_id`/`client_secret` live in a **Databricks secret scope**
     (never accept or write plaintext secrets).
   * Demo: sample ids `sales`, `healthcare`, `finance`.
   * A JSON model file with `{name, tables[{name, columns[{name,dataType}], measures[{name,expression,description}]}], relationships[{from:"Fact.Col", to:"Dim.Col"}]}`.
2. **Target** `catalog.schema` for the metric views and pipeline output, plus a **scratch**
   schema for validation. Discover candidates (catalogs the user can write to). If the workspace
   has a per-user schema convention (e.g. a `users` catalog), offer it as the scratch default.
   Apply org tagging conventions (e.g. a `RemoveAfter` tag) only if workspace instructions
   require them.
3. **Overrides** (optional dict, same schema as the repo's `overrides.example.yaml`):
   map PBI tables/columns to the real UC tables/columns, exclusions, manual SQL for measures.
4. **Artifacts to create** (multi-select, recommended = all found in the model): metric views,
   SDP pipeline, row filters, refresh job, dashboard. Unselected ones are generated as specs only.
5. **LLM**: confirm the frontier model (top candidate from `list_frontier_models()`); `smoke_test()` it.

## Phase 1 - Extract the semantic model

```python
model = load_model("/Volumes/cat/sch/vol/Model.zip")      # TMDL zip / .tmdl / dir / .json / sample id
tm    = parse_tmdl_processes("/Volumes/cat/sch/vol/Model.zip")   # partitions(M), calc cols, roles
# or live (measures/relationships only; M/RLS need the TMDL or .bim export):
model = extract_from_powerbi(ws_id, ds_id,
    tenant_id=dbutils.secrets.get("scope","pbi_tenant"),
    client_id=dbutils.secrets.get("scope","pbi_client_id"),
    client_secret=dbutils.secrets.get("scope","pbi_secret"))
```
Report an inventory: tables, measures, relationships, fact tables (tables with measures ->
one metric view each), M partitions, calculated columns/tables, roles.

## Phase 1b - Map PBI tables to real UC tables (critical)

The generated `source`/`joins` default to `catalog.schema.<pbi_table_lowercase>`. Before
generating, verify the real tables exist:
* Use `tableSearch` / `readTable` (or `information_schema.tables` scoped to the schema) to find
  the UC table for each PBI table and confirm column names.
* Put every mismatch into `overrides["table_mappings"]` and `overrides["column_mappings"]`.
* Columns are referenced lowercase with spaces -> `_` (e.g. `Sales Amount` -> `sales_amount`).

## Phases 2-6 - Overrides, translate, generate, validate, evaluate

```python
report = run_migration(source=model, catalog=CAT, schema=SCH, overrides=overrides)
# view_suffix="_metric_view" by default; use "_mv_tmp" + the scratch schema for validation
```
What each phase does:
* **Overrides**: drops `exclude_tables`, glob `exclude_measures`, `exclude_columns`,
  `exclude_joins`; applies `table_mappings`, `column_mappings`, `extra_joins`,
  `measure_overrides` (status `manual_override`), `dimension_overrides`.
* **Translate**: 14-pass DAX->SQL (`converted` / `partial` / `unsupported` + confidence 0-100).
* **Generate**: one Metric View YAML v1.1 + `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`
  per fact table. Joins = LEFT from relationships (aliases prefixed `j_`), dimensions = non-key,
  non-hidden columns of joined dimension tables, measures = translated SQL. TOTALYTD becomes a
  window measure on generated `ytd_date`/`ytd_year` dimensions.
* **Validate (static)**: `report["views"][i]["static_validation"]` (YAML structure, residual DAX,
  circular refs).
* **Evaluate**: `report["summary"]` -> `conversion_rate_pct`, `avg_confidence`, `by_status`,
  `needs_review`; `report["measures"]` -> DAX, SQL, status, issues per measure.

## Phase 6b - LLM fallback + semantic review (ai_query)

Follow [llm-translation.md](llm-translation.md). Log table: `<scratch schema>.pbi_migration_llm_log`.
```python
fb = llm_fallback_measures(report, MODEL, LOG)          # partial/unsupported or confidence < 80
review, fixes = llm_review_measures(report, MODEL, LOG) # EVERY measure: equivalent / not_equivalent / uncertain
manual = overrides.get("measure_overrides", {})
overrides["measure_overrides"] = {**fb, **fixes, **manual}   # user's manual overrides always win
report = run_migration(model, CAT, SCRATCH, overrides=overrides, view_suffix="_mv_tmp")
```
An LLM expression is accepted only if the scratch CREATE + `MEASURE()` query succeeds; otherwise drop that override and list the measure as `needs_review`. Report a table
per measure: DAX, final SQL, origin (rules / LLM fallback / LLM correction / manual), review
verdict, confidence.

## Phase 6c - Validate against Databricks (mandatory before reporting success)

Static validation is not enough. Prove the DDL works:
1. Create the view in a scratch location first (e.g. `view_suffix="_mv_tmp"` in the personal
   schema) with `spark.sql(view["ddl"])`.
2. Query it: `SELECT <one dimension>, MEASURE(`<measure>`) ... GROUP BY ALL LIMIT 20` for every
   measure (backtick names with spaces).
3. Cross-check at least one measure against a direct aggregate on the source table
   (e.g. `SUM(sales_amount)` on the fact table) - totals must match.
4. On errors (`UNRESOLVED_COLUMN`, `TABLE_OR_VIEW_NOT_FOUND`, ambiguous names) fix via overrides
   and re-run; do not hand-edit around the driver unless needed.
5. Drop the scratch view when done.

## Phase 7 - Process migration (M, calculated columns/tables, RLS)

Follow [process-migration.md](process-migration.md).
```python
plan = build_process_plan(tm, CAT, SCH, source_mappings=SRC_MAP, role_groups=ROLE_GROUPS,
                          admin_group=ADMIN_GROUP)
```
* Resolve every `plan["unmapped_sources"]` (M connector sources) to a UC table / Volume path with
  `tableSearch`; if it does not exist in UC yet, say which ingestion is needed (Lakeflow Connect /
  Lakehouse Federation) instead of inventing a table.
* Send `plan["llm_todo"]` to `llm_translate_text(...)` with `LLM_PROCESS_INSTRUCTIONS[kind]`.
* Validate each pipeline query by running its SELECT (the part after `AS`) with `LIMIT 10` on
  the scratch schema; validate each row-filter function by creating it in scratch and calling it.
* Only for artifacts selected in Phase 0: create the SDP pipeline (load the
  `spark-declarative-pipelines` skill; one SQL file per table), the row-filter functions +
  `ALTER TABLE ... SET ROW FILTER`, and the job.

## Phase 8 - Refresh -> Lakeflow Job

Schedule from Phase 0 or `powerbi_refresh_schedule(...)`. `spec, crons = refresh_job_spec(name,
pipeline_id, days, times, timezone)`; create it with the `edit-job-settings` skill (one job per
cron if several). Metric views need no refresh - they are views over the pipeline output.

## Phase 9 - Deploy metric views and dashboard

* Metric views (if selected): run each `view["ddl"]` against the real target. `CREATE OR REPLACE`
  drops grants; for existing views where grants matter use `ALTER VIEW <name> AS $$<yaml>$$`.
  Rollback = `DROP VIEW IF EXISTS` (only on explicit request). Link views as `[c.s.v](#table)`.
* Dashboard (if selected): if a .pbix is available, `report_layout_brief(pbix, P["repo_path"])`
  for pages/visuals. Then `createAsset` (assetType `dashboard`, under the user's folder) and
  `openAsset` with a `continueMessage` describing the metric views, the pages and the visual
  mapping (bar/column->bar, line->line, area->area, pie/donut->pie, card/KPI->counter,
  table/matrix->table, scatter->scatter), `MEASURE()` queries, and any required tags.
  Do this last: the hand-off ends the turn.

## Final checklist

* Each fact table: metric view validated in scratch (rows returned, one total cross-checked
  against a direct aggregate on the source).
* Measures table with origin + LLM review verdicts; `needs_review` list.
* Pipeline SQL, row filters and job: created (if selected) or delivered as specs; unmapped
  sources and role-to-group mapping listed.
* LLM model used and log table named; scratch objects dropped; no secrets written.
