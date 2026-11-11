"""
llm_translate.py - LLM steps of the pbi-to-metric-views skill, using Databricks AI Functions
(ai_query) with a frontier model chosen by llm_models.list_frontier_models().

Two uses (both chosen by the user):
  1. FALLBACK translation: DAX measures the rule engine leaves partial/unsupported or with
     confidence < threshold; also M (Power Query), RLS filters and calculated columns that the
     rules in process_migrate.py cannot convert.
  2. SEMANTIC REVIEW of EVERY translated measure: DAX vs SQL equivalence verdict with an
     optional corrected expression.

Rules enforced here:
  * one ai_query call per input, results persisted to a Delta table (reproducible, auditable)
  * structured output (responseFormat), temperature 0 (retried without it if the model rejects it)
  * inputs passed as DataFrame columns, never string-concatenated into SQL
  * nothing returned here is trusted: callers must re-run run_migration() with the proposed
    overrides and prove the DDL with a real CREATE + MEASURE() query in a scratch schema.

Usage:
    exec(open(f"{SKILL_DIR}/scripts/llm_translate.py").read())
    ov = llm_fallback_measures(report, MODEL, "cat.sch.pbi_migration_llm_log")
    rv = llm_review_measures(report, MODEL, "cat.sch.pbi_migration_llm_log")
"""
import json, re, uuid
from datetime import datetime, timezone

MEASURE_FMT = "STRUCT<sql:STRING, window_json:STRING, confidence:INT, notes:STRING>"
REVIEW_FMT = "STRUCT<verdict:STRING, corrected_sql:STRING, window_json:STRING, confidence:INT, notes:STRING>"
TEXT_FMT = "STRUCT<sql:STRING, confidence:INT, notes:STRING>"

MV_RULES = """Target: a Databricks Unity Catalog METRIC VIEW measure (YAML v1.1).
Rules:
- Return ONE aggregate SQL expression (Databricks SQL), not a SELECT statement.
- Fact table columns are `source.<col>`; joined dimension columns are `<join_name>.<col>` (join names given below).
- Use only columns that exist in the context. Lowercase identifiers.
- No nested aggregates. Ratios: SUM(a) / NULLIF(SUM(b), 0).
- CALCULATE(<agg>, <filter>) -> <agg> FILTER (WHERE <filter>).
- Reference another measure with MEASURE(`Measure Name`) (backticks).
- Time intelligence: keep the plain aggregate in `sql` and put the window in `window_json` as a JSON
  array of {"order": <dimension name>, "range": "current|cumulative|trailing N day|all", "offset": "-1 year" (optional),
  "semiadditive": "first|last" (optional)}. Only order by dimension names that exist in the context.
  YTD = [{"order":"ytd_date","range":"cumulative"},{"order":"ytd_year","range":"current"}].
  FIRSTNONBLANK/LASTNONBLANK/OPENINGBALANCE -> semiadditive window on a date dimension.
- If it cannot be expressed, return sql = "" and explain in notes. confidence is 0-100."""


def _check_model(model):
    if not re.fullmatch(r"[\w.\-]+", model or ""):
        raise ValueError(f"invalid model endpoint name: {model!r}")


def _check_table(fqn):
    if not re.fullmatch(r"`?[\w\-]+`?\.`?[\w\-]+`?\.`?[\w\-]+`?", fqn or ""):
        raise ValueError(f"results table must be catalog.schema.table: {fqn!r}")


def ai_batch(items, model, response_format, results_table, run_id=None):
    """items: list of {"id", "kind", "prompt"}. Returns {id: parsed_dict_or_None, ...}.
    Persists every call (prompt, raw response, error) to results_table."""
    _check_model(model)
    _check_table(results_table)
    if not items:
        return {}
    run_id = run_id or str(uuid.uuid4())
    view = f"pbi_llm_in_{uuid.uuid4().hex[:8]}"
    spark.createDataFrame([(str(i["id"]), i["kind"], i["prompt"]) for i in items],  # noqa: F821
                          "id STRING, kind STRING, prompt STRING").createOrReplaceTempView(view)
    fmt = response_format.replace("'", "")

    def _run(with_temp):
        params = ", modelParameters => named_struct('temperature', 0.0)" if with_temp else ""
        return spark.sql(  # noqa: F821
            f"SELECT id, kind, prompt, to_json(ai_query('{model}', prompt, responseFormat => '{fmt}'"
            f"{params}, failOnError => false)) AS raw FROM {view}").collect()

    rows = _run(True)
    if rows and all("temperature" in (r.raw or "").lower() and "error" in (r.raw or "").lower() for r in rows):
        rows = _run(False)

    out, log = {}, []
    for r in rows:
        parsed, err = None, None
        try:
            env = json.loads(r.raw or "{}")
            err = env.get("errorMessage") or env.get("errorStatus")
            val = env.get("result", env.get("response"))
            parsed = json.loads(val) if isinstance(val, str) else val
        except Exception as e:  # malformed model output
            err = f"parse error: {e}"
        out[r.id] = None if err else parsed
        log.append((run_id, datetime.now(timezone.utc), model, r.kind, r.id, r.prompt, r.raw, err))
    spark.createDataFrame(log, "run_id STRING, ts TIMESTAMP, model STRING, kind STRING, item_id STRING, "  # noqa: F821
                               "prompt STRING, raw_response STRING, error STRING") \
        .write.mode("append").option("mergeSchema", "true").saveAsTable(results_table)
    spark.catalog.dropTempView(view)  # noqa: F821
    return out


def _view_context(report, fact_table):
    v = next((x for x in report["views"] if x["fact_table"] == fact_table), None)
    return v["yaml"] if v else ""


def _window(js):
    if not js:
        return None
    try:
        w = json.loads(js)
        return w if isinstance(w, list) and w else None
    except Exception:
        return None


def llm_fallback_measures(report, model, results_table, threshold=80):
    """Translate measures the rules could not handle. Returns a `measure_overrides` dict
    (merge it into the overrides and re-run run_migration)."""
    todo = [m for m in report["measures"]
            if m["status"] not in ("converted", "manual_override") or m["confidence"] < threshold]
    items = [{"id": f"{m['fact_table']}::{m['measure']}", "kind": "dax_measure",
              "prompt": f"{MV_RULES}\n\nMetric view YAML (context):\n{_view_context(report, m['fact_table'])}\n\n"
                        f"Measure name: {m['measure']}\nDAX:\n{m['dax']}\n\n"
                        f"Rule-based attempt (may be wrong): {m['sql']}\nIssues: {m['issues'] + m['warnings']}"}
             for m in todo]
    res = ai_batch(items, model, MEASURE_FMT, results_table)
    overrides = {}
    for it in items:
        r = res.get(it["id"])
        if r and r.get("sql"):
            name = it["id"].split("::", 1)[1]
            overrides[name] = {"expr": r["sql"], "comment": f"LLM ({model}) conf={r.get('confidence')}: {r.get('notes', '')}"[:500]}
            if _window(r.get("window_json")):
                overrides[name]["window"] = _window(r["window_json"])
    return overrides


def llm_review_measures(report, model, results_table):
    """Semantic review of EVERY measure. Returns list of {measure, verdict, corrected_sql,
    window, confidence, notes} and a `measure_overrides` dict with the corrections the model
    proposes (verdict == not_equivalent and corrected_sql present)."""
    items = [{"id": f"{m['fact_table']}::{m['measure']}", "kind": "dax_review",
              "prompt": f"You are reviewing a Power BI DAX -> Databricks metric view migration.\n{MV_RULES}\n\n"
                        f"Metric view YAML (context):\n{_view_context(report, m['fact_table'])}\n\n"
                        f"Measure: {m['measure']}\nOriginal DAX:\n{m['dax']}\nTranslated SQL: {m['sql']}\n\n"
                        "Is the SQL semantically equivalent to the DAX under any GROUP BY of the metric view "
                        "dimensions (filter context, blanks vs NULL, DIVIDE semantics, distinct counts, time intelligence)? "
                        "verdict must be one of: equivalent, not_equivalent, uncertain. If not_equivalent give corrected_sql."}
             for m in report["measures"]]
    res = ai_batch(items, model, REVIEW_FMT, results_table)
    review, overrides = [], {}
    for it in items:
        r = res.get(it["id"]) or {}
        name = it["id"].split("::", 1)[1]
        verdict = (r.get("verdict") or "error").lower()
        review.append({"measure": name, "verdict": verdict, "corrected_sql": r.get("corrected_sql") or "",
                       "window": _window(r.get("window_json")), "confidence": r.get("confidence"),
                       "notes": r.get("notes", "")})
        if verdict == "not_equivalent" and r.get("corrected_sql"):
            overrides[name] = {"expr": r["corrected_sql"],
                               "comment": f"LLM review ({model}): {r.get('notes', '')}"[:500]}
            if _window(r.get("window_json")):
                overrides[name]["window"] = _window(r["window_json"])
    return review, overrides


def llm_translate_text(items, model, results_table, instructions):
    """Generic fallback for M steps, RLS filters, calculated columns.
    items: list of {"id", "kind", "source"}; returns {id: {sql, confidence, notes}}."""
    batch = [{"id": i["id"], "kind": i["kind"],
              "prompt": f"{instructions}\n\nInput ({i['kind']}):\n{i['source']}\n\n"
                        "Return Databricks SQL only in `sql` (empty if impossible), confidence 0-100, notes."}
             for i in items]
    return ai_batch(batch, model, TEXT_FMT, results_table)
