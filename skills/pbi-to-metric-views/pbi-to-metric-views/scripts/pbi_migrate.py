"""
pbi_migrate.py - Driver for the `pbi-to-metric-views` Genie Code skill.

Wraps the engine of github.com/suryasai87/pbi-metrics-migration-tool (backend/*)
and fixes gaps found in that repo's pipeline:
  * applies ALL overrides (table/column mappings, extra/excluded joins, excluded
    columns, glob measure exclusions, measure/dimension overrides) - the repo
    pipeline only applies exclusions
  * PyYAML parses the `on:` join key as boolean True - restored as "on"
  * converts the engine's invalid `window: {order_by, group_by}` (TOTALYTD) into
    valid Metric View v1.1 window lists, or drops it and flags the measure
  * prefixes join aliases with `j_` (aliases such as `date` collide with dimension
    names and fail at CREATE time)
  * validates the YAML body (the repo's validate_ddl() mis-parses its own DDL)
  * emits a per-measure evaluation report

Cloud-agnostic: no hard-coded workspace paths. The engine repo is resolved at
runtime (`default_paths()`); if it is missing, clone it with the agent's `runGit`
tool (operation clone) into `default_paths()["repo_path"]`.

Usage (Python session on Databricks, any cloud):
    exec(open(f"/Workspace/Users/{user}/.assistant/skills/pbi-to-metric-views/scripts/pbi_migrate.py").read())
    P = default_paths()          # user, skill_dir, repo_path, repo_exists, user_schema_guess
    report = run_migration(source="sales", catalog="main", schema="gold", overrides={...})
    report["views"][i]["ddl"]   -> CREATE OR REPLACE VIEW ... WITH METRICS
    report["summary"]           -> conversion rate, confidence, needs_review
"""
import copy, fnmatch, json, os, re, sys


REPO_URL = "https://github.com/suryasai87/pbi-metrics-migration-tool"


def default_paths():
    """Resolve per-user paths at runtime (works on AWS, Azure, GCP)."""
    try:
        user = spark.sql("SELECT current_user()").first()[0]  # noqa: F821 (Databricks global)
    except Exception:
        user = os.environ.get("USER", "unknown")
    home = f"/Workspace/Users/{user}"
    repo = f"{home}/pbi-metrics-migration-tool"
    return {"user": user,
            "skill_dir": f"{home}/.assistant/skills/pbi-to-metric-views",
            "repo_path": repo,
            "repo_exists": os.path.isfile(os.path.join(repo, "backend", "dax_translator.py")),
            "user_schema_guess": re.sub(r"[^a-z0-9_]", "_", user.split("@")[0].lower())}


def _resolve_repo(repo_path):
    repo_path = repo_path or default_paths()["repo_path"]
    if not os.path.isfile(os.path.join(repo_path, "backend", "dax_translator.py")):
        raise FileNotFoundError(
            f"Engine repo not found at {repo_path}. Clone {REPO_URL} there (runGit clone, provider gitHub).")
    return repo_path


def _import_engine(repo_path=None):
    repo_path = _resolve_repo(repo_path)
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    from backend.dax_translator import DAXTranslator
    from backend.yaml_generator import MetricViewYAMLGenerator
    from backend.validator import MetricViewValidator
    from backend.overrides import OverridesManager
    from backend.tmdl_parser import TMDLParser
    return DAXTranslator, MetricViewYAMLGenerator, MetricViewValidator, OverridesManager, TMDLParser


def _san(s):
    s = re.sub(r"[^a-zA-Z0-9_]", "_", str(s).strip().lower())
    return re.sub(r"_+", "_", s).strip("_")


def _fqn(name, catalog, schema):
    n = name.count(".")
    return name if n == 2 else (f"{catalog}.{name}" if n == 1 else f"{catalog}.{schema}.{name}")


# ------------------------------------------------------------------ Phase 1: extract
def load_model(source, repo_path=None):
    """source: sample id ('sales'|'healthcare'|'finance'), a dict, a .json model
    file, or a TMDL .zip / .tmdl / directory path (workspace path or /Volumes)."""
    if isinstance(source, dict):
        return copy.deepcopy(source)
    if source in ("sales", "healthcare", "finance"):
        repo_path = _resolve_repo(repo_path)
        src = open(os.path.join(repo_path, "main.py")).read()
        a = src.index("SAMPLE_MODELS = [")
        b = src.index("\n]\n", a) + 3
        ns = {}
        exec(src[a:b], ns)
        return copy.deepcopy(next(m for m in ns["SAMPLE_MODELS"] if m["id"] == source))
    if source.endswith(".json"):
        return json.load(open(source))
    TMDLParser = _import_engine(repo_path)[4]
    return TMDLParser().parse(source).to_dict()


def extract_from_powerbi(workspace_id, dataset_id, tenant_id, client_id, client_secret, repo_path=None):
    """Live extraction via Power BI REST (INFO.* DAX queries, Scanner API fallback).
    Pass secrets from dbutils.secrets.get(...) - never hard-code them."""
    repo_path = _resolve_repo(repo_path)
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    from backend.pbi_client import PowerBIClient
    c = PowerBIClient(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    if not c.authenticate_service_principal():
        raise RuntimeError("Power BI service principal authentication failed")
    return c.extract_semantic_model(workspace_id, dataset_id).to_dict()


# ------------------------------------------------------------------ Phase 2: overrides (filtering)
def _filter_model(model, ov, mgr):
    tables = [copy.deepcopy(t) for t in model.get("tables", [])
              if not mgr.should_exclude_table(ov, t.get("name", ""))]
    keep = {t["name"].lower() for t in tables}
    for t in tables:
        t["measures"] = [m for m in t.get("measures", [])
                         if not any(fnmatch.fnmatch(m["name"].lower(), p.lower()) for p in ov.exclude_measures)]
        t["columns"] = [c for c in t.get("columns", [])
                        if not mgr.should_exclude_column(ov, t["name"], c.get("name", ""))]
    rels = []
    for r in model.get("relationships", []):
        ft, tt = r.get("from", ".").split(".")[0], r.get("to", ".").split(".")[0]
        if ft.lower() in keep and tt.lower() in keep and not mgr.should_exclude_join(ov, ft, tt):
            rels.append(r)
    return {"name": model.get("name", "Model"), "tables": tables, "relationships": rels}


def _fix_windows(doc, fact, measures_report):
    """Engine emits `window: {range, order_by, group_by}` (invalid). Convert TOTALYTD /
    DATESYTD to v1.1 list form (cumulative on DATE dim + current on YEAR dim), or drop
    the window and flag the measure for review."""
    dax_by_name = {m["name"]: m.get("expression", "") for m in fact.get("measures", [])}
    dims = doc.setdefault("dimensions", [])
    for m in doc.get("measures", []):
        if "window" not in m or isinstance(m["window"], list):
            continue
        m.pop("window")
        dax = dax_by_name.get(m["name"], "")
        ref = re.search(r"(?:TOTALYTD|DATESYTD)\s*\(.*?,\s*'?([\w ]+?)'?\[([\w ]+)\]", dax, re.I | re.S)
        target = None
        if ref:
            tbl, col = _san(ref.group(1)), _san(ref.group(2))
            alias = "source" if tbl == _san(fact["name"]) else tbl
            if alias == "source" or any(j["name"] == alias for j in doc.get("joins", [])):
                target = f"{alias}.{col}"
        rep = next(r for r in measures_report
                   if r["measure"] == m["name"] and r["fact_table"] == fact["name"])
        if not target:
            rep["status"] = "partial"
            rep["confidence"] = min(rep["confidence"], 50)
            rep["issues"].append("Time-intelligence window dropped: date column not reachable from this metric view")
            continue
        if not any(d["name"] == "ytd_date" for d in dims):
            dims.append({"name": "ytd_date", "expr": f"DATE({target})"})
            dims.append({"name": "ytd_year", "expr": f"YEAR({target})"})
        m["window"] = [{"order": "ytd_date", "range": "cumulative"},
                       {"order": "ytd_year", "range": "current"}]
        rep["sql"] = m["expr"] + "  [window: cumulative ytd_date, current ytd_year]"


# ------------------------------------------------------------------ Phases 2-6
def run_migration(source, catalog, schema, repo_path=None, overrides=None, view_suffix="_metric_view"):
    """Extract -> overrides -> translate -> generate -> validate (static) -> evaluate.
    Deploy (CREATE VIEW) and dashboard creation are done by the agent afterwards."""
    import yaml
    DAXTranslator, Gen, Validator, Mgr, _ = _import_engine(repo_path)
    mgr = Mgr()
    ov = mgr.load_from_dict(overrides or {})
    catalog = ov.target.catalog or catalog
    schema = ov.target.schema or schema

    raw = load_model(source, repo_path)
    report = {"model": raw.get("name"), "catalog": catalog, "schema": schema,
              "extract": {"tables": len(raw.get("tables", [])),
                          "measures": sum(len(t.get("measures", [])) for t in raw.get("tables", [])),
                          "relationships": len(raw.get("relationships", []))}}
    model = _filter_model(raw, ov, mgr)
    tables_by_lower = {t["name"].lower(): t for t in model["tables"]}

    colmap = {}
    for t in model["tables"]:
        for c in t.get("columns", []):
            colmap[(_san(t["name"]), _san(c["name"]))] = mgr.apply_column_mapping(ov, t["name"], c["name"])

    views, measures_report = [], []
    for fact in [t for t in model["tables"] if t.get("measures")]:
        # Phase 3: translate DAX -> SQL (+ manual measure overrides)
        tr = DAXTranslator(relationships=model["relationships"]).translate_batch(fact["measures"], fact["name"])
        for m, r in zip(fact["measures"], tr):
            mo = ov.measure_overrides.get(m["name"])
            status = "manual_override" if mo else r.status
            m["translated_sql"] = mo.expr if mo else r.translated_sql
            m["status"] = status
            if mo and mo.comment:
                m["description"] = mo.comment
            if r.window_spec and not mo:
                m["window"] = r.window_spec
            measures_report.append({"fact_table": fact["name"], "measure": m["name"],
                                    "dax": m.get("expression", ""), "sql": m["translated_sql"],
                                    "status": status, "confidence": 100 if mo else r.confidence,
                                    "issues": [] if mo else list(r.issues),
                                    "warnings": [] if mo else list(r.warnings)})

        # Phase 4: generate YAML with the engine, then post-process with overrides
        rels = [r for r in model["relationships"] if r["from"].split(".")[0].lower() == fact["name"].lower()]
        sub = {"name": model["name"],
               "tables": [fact] + [tables_by_lower[r["to"].split(".")[0].lower()] for r in rels
                                   if r["to"].split(".")[0].lower() in tables_by_lower],
               "relationships": rels}
        _, y, _ = Gen().generate_from_model(sub, catalog, schema)[0]
        doc = yaml.safe_load(y)
        for j in doc.get("joins", []) or []:
            if True in j:
                j["on"] = j.pop(True)  # PyYAML (YAML 1.1) parses `on:` as boolean
        doc["version"] = 1.1
        doc["source"] = _fqn(mgr.apply_table_mapping(ov, fact["name"]), catalog, schema)
        for j in doc.get("joins", []) or []:
            pbi = next((t["name"] for t in sub["tables"] if _san(t["name"]) == j["name"]), j["name"])
            j["source"] = _fqn(mgr.apply_table_mapping(ov, pbi), catalog, schema)
        for ej in ov.extra_joins:
            if ej.from_table.lower() == fact["name"].lower():
                al = _san(ej.to_table)
                doc.setdefault("joins", []).append({
                    "name": al, "source": _fqn(mgr.apply_table_mapping(ov, ej.to_table), catalog, schema),
                    "on": f"source.{ej.from_column} = {al}.{ej.to_column}"})
        fact_alias = _san(fact["name"])

        def remap(expr):
            def rep(mt):
                al, col = mt.group(1), mt.group(2)
                return f"{al}.{colmap.get((fact_alias if al == 'source' else al, col), col)}"
            return re.sub(r"\b(source|[a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", rep, str(expr))

        for j in doc.get("joins", []) or []:
            j["on"] = remap(j["on"])
        for d in doc.get("dimensions", []) or []:
            d["expr"] = remap(d["expr"])
            do = ov.dimension_overrides.get(d["name"])
            if do:
                if do.display_name:
                    d["display_name"] = do.display_name
                if do.description:
                    d["comment"] = do.description
        for m in doc.get("measures", []) or []:
            mo = ov.measure_overrides.get(m["name"])
            if not mo:
                m["expr"] = remap(m["expr"])
            elif isinstance(mo.window, list) and mo.window:
                m["window"] = mo.window  # v1.1 window list from overrides / LLM
        _fix_windows(doc, fact, measures_report)

        # Join aliases like `date` collide with dimension names -> prefix with j_
        amap = {j["name"]: "j_" + j["name"] for j in doc.get("joins", []) or []}

        def realias(expr):
            return re.sub(r"\b([a-z_][a-z0-9_]*)\.", lambda mt: amap.get(mt.group(1), mt.group(1)) + ".", str(expr))

        for j in doc.get("joins", []) or []:
            j["on"] = realias(j["on"])
            j["name"] = amap[j["name"]]
        for d in doc.get("dimensions", []) or []:
            d["expr"] = realias(d["expr"])
        for m in doc.get("measures", []) or []:
            m["expr"] = realias(m["expr"])

        view_name = f"{catalog}.{schema}.{fact_alias}{view_suffix}"
        yaml_body = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=1000)
        comment = str(doc.get("comment", "")).replace("'", "''")
        ddl = (f"CREATE OR REPLACE VIEW {view_name}\nCOMMENT '{comment}'\nWITH METRICS\n"
               f"LANGUAGE YAML\nAS $$\n{yaml_body}$$")
        # Phase 5 (static): validate the YAML body with the repo validator
        vr = Validator().validate_yaml(yaml_body).to_dict()
        views.append({"fact_table": fact["name"], "view_name": view_name, "source": doc["source"],
                      "joins": [j["source"] for j in doc.get("joins", []) or []],
                      "yaml": yaml_body, "ddl": ddl, "static_validation": vr})

    # Phase 6: evaluate
    total = len(measures_report)
    by = {}
    for r in measures_report:
        by[r["status"]] = by.get(r["status"], 0) + 1
    ok = by.get("converted", 0) + by.get("manual_override", 0)
    report.update({
        "views": views, "measures": measures_report,
        "summary": {"views": len(views), "measures": total, "by_status": by,
                    "conversion_rate_pct": round(100 * ok / total, 1) if total else 0,
                    "avg_confidence": round(sum(r["confidence"] for r in measures_report) / total, 1) if total else 0,
                    "needs_review": [r["measure"] for r in measures_report
                                     if r["status"] not in ("converted", "manual_override") or r["confidence"] < 80]}})
    return report
