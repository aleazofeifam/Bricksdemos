# Process migration (Power Query, calculated objects, RLS, refresh, report)

All functions live in `scripts/process_migrate.py`. They only generate SQL/specs; the agent
validates and creates objects.

## 1. Extract processes from TMDL
`tm = parse_tmdl_processes(path)` reads `.zip`, folder or single `.tmdl` and returns:
* `tables[name].columns` (`expression` set => calculated column), `tables[name].partitions`
  (`kind` = `m` | `calculated` | `entity`, `source` = M script or DAX table expression)
* `roles[]` (`members`, `filters[table] = DAX boolean`) and shared `expressions` (M parameters)

Live Power BI API extraction does not return M or RLS; ask for a TMDL export
(Power BI Desktop: File > Save as > .pbip, or Tabular Editor) when those are needed.

## 2. Power Query (M) / dataflows -> SDP materialized views
`m_to_sql(m, source_mappings)` converts a `let ... in` script into CTEs (one per step):

| M step | SQL |
|---|---|
| `Sql.Database / Snowflake / PostgreSQL / Databricks.Catalogs / ...` + `Source{[Schema=,Item=]}[Data]` | `SELECT * FROM <source_mappings["schema.item"]>` |
| `Csv.Document(File.Contents(path))` | `read_files('<mapped Volume path>', format => 'csv', header => true)` |
| `Table.SelectRows(t, each <cond>)` | `WHERE <cond>` (`and/or/not`, `= null`, `Text.Contains`, `Text.StartsWith`, `Date.Year/Month/Day`, `#date`) |
| `Table.RemoveColumns / SelectColumns` | `SELECT * EXCEPT (...)` / `SELECT a, b` |
| `Table.RenameColumns` | `SELECT * EXCEPT (a), a AS b` |
| `Table.TransformColumnTypes` | `CAST(col AS <type>)` (Int64, number, text, date, datetime, logical, Currency) |
| `Table.AddColumn(t, "c", each expr, type)` | `SELECT *, expr AS c` |
| `Table.Group(t, {keys}, {{n, each List.Sum([c])}})` | `GROUP BY` (Sum/Average/Min/Max/Count/DistinctCount/RowCount) |
| `Table.Distinct` | `SELECT DISTINCT *` |
| anything else (NestedJoin, Pivot, custom functions, `each` lambdas) | -> `llm_todo` (LLM fallback) |

Sources: M reads operational systems directly; on Databricks those must already be in UC
(Lakeflow Connect, Lakehouse Federation foreign catalog, or files in a Volume). Map each
`plan["unmapped_sources"]` key to a UC table with `tableSearch`; never invent a table. Unmapped
sources stay as `__UNMAPPED__...` and the query must not be deployed.

Each table becomes `CREATE OR REFRESH MATERIALIZED VIEW <cat>.<sch>.<table>` projecting the TMDL
columns to snake_case (so the metric views' `source` can point to it). Create the pipeline with
the `spark-declarative-pipelines` skill (one `.sql` file per table, catalog/schema = target).
Validate before creating: run the SELECT part with `LIMIT 10` in the scratch schema.

## 3. Calculated columns and tables
* Row-level DAX (`[Price] * [Qty]`, `IF`, `DIVIDE` -> `try_divide`, `BLANK()` -> NULL, `&&`/`||`)
  becomes an extra expression in the table's MV (outer SELECT over snake_case columns).
* `RELATED`/`LOOKUPVALUE`/`CALCULATE`/`EARLIER` -> LLM fallback (it must add the JOIN).
* Calculated table `CALENDAR(DATE(..), DATE(..))` -> date-dimension MV via `sequence()`;
  other DAX tables (SUMMARIZE, ADDCOLUMNS, CALENDARAUTO) -> LLM fallback.

## 4. RLS -> Unity Catalog row filters
For each table with role filters: one SQL UDF that ORs every role:
`RETURN [is_account_group_member('<admin>') OR] (is_account_group_member('<role group>') AND (<filter>)) OR ...`
* `USERPRINCIPALNAME()`/`USERNAME()` -> `current_user()`; lookups to other tables -> LLM
  (EXISTS subquery).
* PBI semantics: a viewer in no role sees no rows - same as the generated function without admin.
* Apply with `ALTER TABLE <uc table> SET ROW FILTER <fn> ON (<cols>)` or, for a pipeline MV,
  the `WITH ROW FILTER` clause (`plan["rls_sql"][i]["sdp_clause"]`). Row filters on the base
  tables also protect the metric views built on them.
* Role members -> tell the user which UC account groups to populate (`plan["notes"]`).
* Validate: create the function in scratch and call it with sample values, e.g.
  `SELECT fn('LATAM')` (user in group -> true, otherwise false).

## 5. Refresh schedule -> Lakeflow Job
`powerbi_refresh_schedule(pbi_client, ws, ds)` (live) or the user's answer -> `refresh_job_spec(...)`:
one `pipeline_task` with Quartz cron `0 <min> <hours> ? * <DAYS>` and the PBI time zone.
PBI allows several times per day with different minutes -> one job per distinct minute.
Create it with the `edit-job-settings` skill. Metric views need no refresh.

## 6. Report -> AI/BI dashboard
`report_layout_brief(pbix, repo_path)` (repo `ReportParser.parse_pbix_file`) lists pages, visuals,
types and fields. Hand off to the dashboard page with that brief (see SKILL.md Phase 9); the
mapping of visual types is in `visual_type_map`.
