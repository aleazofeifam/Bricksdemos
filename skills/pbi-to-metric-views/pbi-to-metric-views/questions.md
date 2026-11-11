# Phase 0 question round

Ask ONCE, at the start, in a single `askUserQuestions` call (max 5 multiple-choice questions;
a `volumeUpload` question must be sent alone, so send it first only if the user has a local file).
Pre-fill options from discovery, mark the best option `(Recommended)`, keep labels short.
After this round, do not ask again unless a required value is missing.

Discovery before asking (no writes):
* `default_paths()` -> user, repo status, per-user schema guess.
* Catalogs/schemas the user can write to (`databricksApi` GET `/api/2.1/unity-catalog/catalogs`,
  then schemas), SQL warehouses (`/api/2.0/sql/warehouses`).
* `list_frontier_models()` -> top 3 LLM candidates.
* If a TMDL/model is already given: `parse_tmdl_processes` + `load_model` inventory, so the
  artifacts question only offers what exists (e.g. no RLS question when there are no roles).

## Questions (adapt; drop the ones already answered)

1. **Source of the Power BI model** (single)
   * TMDL / .bim export in a Volume or workspace path (Recommended - includes M, RLS, calc columns)
   * Live Power BI dataset via service principal in a secret scope (measures + relationships only)
   * Upload a file now (then send a separate `volumeUpload` question)
   * Built-in demo sample (sales / healthcare / finance)
2. **Target location** (single): `<catalog>.<schema>` options discovered above for the final
   objects; the scratch schema for validation defaults to the user's personal schema when one
   exists, otherwise `<target>_scratch` (state it in the label).
3. **Artifacts to create** (multi-select; only those present in the model; all Recommended):
   Metric views, SDP pipeline from Power Query, Row filters from RLS, Refresh job, AI/BI dashboard.
   Not selected = delivered as SQL/JSON specs only.
4. **LLM model for fallback + semantic review** (single): the top 2-3 `system.ai.*` frontier
   candidates (first one Recommended) + "Do not use LLM (rules only)".
5. **Security / schedule details** (single, only if roles or refresh exist):
   * "Map each PBI role to UC group pbi_role_<role>, no admin bypass" (Recommended; the
     `build_process_plan` default)
   * "Use UC groups named exactly like the roles + an admin group" (pass `role_groups` and
     `admin_group`)
   * "Skip RLS and refresh migration"
   The refresh schedule itself is read from Power BI (live) or from the user's answer text;
   if neither, create the job PAUSED and say so.

Missing free-text values (e.g. a specific group or Volume path) can be captured through the
question's free-text answer. If the user skips the round, use the Recommended options, state
them explicitly as your defaults, and create nothing outside the scratch schema.
