# LLM usage (Databricks AI Functions)

The user chose: **rule engine first, LLM as fallback, plus an LLM semantic review of every
measure**. All LLM calls go through `ai_query` (SQL AI Function) so they run on any cloud,
are governed by Unity Catalog / AI Gateway, and are billed to the workspace.

## 1. Pick the model (never guess names)
```python
cands = list_frontier_models()        # scripts/llm_models.py
MODEL = cands[0]["endpoint"]          # e.g. system.ai.claude-opus-<latest>; confirmed in Phase 0
assert smoke_test(MODEL)
```
* Public clouds: `system.ai.<model>` from the UC model-services listing.
* Azure Gov/China, AWS GovCloud/DoD: falls back to `databricks-<model>` serving endpoints.
* Ranking: claude-opus > gpt (sol/terra/pro) > gemini-*-pro > claude-sonnet, newest version first;
  mini/nano/flash/lite/haiku/embedding models are excluded.
* If `smoke_test` fails (no EXECUTE / CAN QUERY), try the next candidate; if none works, continue
  rules-only and report it.

## 2. Calls
`ai_batch(items, model, response_format, log_table)`:
* inputs passed as a DataFrame column (no SQL string building with user text)
* `responseFormat` STRUCT, `temperature 0` (retried without it if the model rejects the param),
  `failOnError => false`
* one call per input; every prompt/response/error appended to `log_table` (audit + reproducibility;
  do not call the model twice for the same input in one run).

| Function | Input | Output |
|---|---|---|
| `llm_fallback_measures(report, MODEL, LOG, threshold=80)` | measures partial/unsupported or confidence < 80 | `measure_overrides` (expr + optional v1.1 `window` list) |
| `llm_review_measures(report, MODEL, LOG)` | EVERY measure (DAX + translated SQL + metric view YAML) | review list (`equivalent` / `not_equivalent` / `uncertain`) + corrections as `measure_overrides` |
| `llm_translate_text(items, MODEL, LOG, instructions)` | M scripts, calc columns, calc tables, RLS filters from `plan["llm_todo"]` | `{id: {sql, confidence, notes}}` |

For process items use `LLM_PROCESS_INSTRUCTIONS[item["kind"]].format(table=..., mappings=SRC_MAP)`.

## 3. Trust nothing until Databricks accepts it
1. Merge LLM overrides under the user's manual overrides (manual always wins).
2. Re-run `run_migration` into the scratch schema, CREATE each view, run `MEASURE()` for each
   LLM-touched measure and compare at least one total with a direct aggregate.
3. If the CREATE fails or results are wrong, drop that LLM override, keep the rules output and
   mark the measure `needs_review`.
4. `uncertain` review verdicts are reported (with the model's notes), not auto-applied.
5. In the final report show, per measure: origin (rules / LLM fallback / LLM correction / manual),
   verdict, confidence, and the log table name.

## Cost note
The review touches every measure once per run; for very large models (> ~500 measures) tell the
user the call count before running it.
