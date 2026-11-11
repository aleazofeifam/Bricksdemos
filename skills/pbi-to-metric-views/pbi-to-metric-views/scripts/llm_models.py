"""
llm_models.py - Pick a frontier LLM available in THIS workspace (any cloud) for ai_query.

Never guess endpoint names. Discovery order:
  1. Unity Catalog model services in system.ai  (public AWS / Azure / GCP)
       GET /api/2.1/unity-catalog/model-services?parent=schemas/system.ai&view=BASIC
     -> endpoint argument for ai_query is the 3-part name `system.ai.<model>`
  2. Fallback (Azure Gov/China, AWS GovCloud/DoD, or when 1 is unavailable):
     Model Serving endpoints named `databricks-<model>` (GET /api/2.0/serving-endpoints)

Usage:
    exec(open(f"{SKILL_DIR}/scripts/llm_models.py").read())
    cands = list_frontier_models()      # ranked list of dicts {endpoint, family, version, source}
    model = cands[0]["endpoint"]        # CONFIRM with the user before using it
    smoke_test(model)                   # True if ai_query answers
"""
import re

# Frontier families, best first. Each entry: (family label, regex on the model name).
# Only large reasoning-grade models; mini / nano / flash / lite / haiku / embedding are excluded.
FRONTIER_FAMILIES = [
    ("claude-opus", r"^claude-opus-(\d+(?:-\d+)*)$"),
    ("gpt", r"^gpt-(\d+(?:-\d+)*)(?:-(?:sol|terra|pro))?$"),
    ("gemini-pro", r"^gemini-(\d+(?:-\d+)*)-pro$"),
    ("claude-sonnet", r"^claude-sonnet-(\d+(?:-\d+)*)$"),
]
_EXCLUDE = re.compile(r"(mini|nano|flash|lite|haiku|embed|image|codex|oss|gte|bge|llama|qwen|gemma)", re.I)


def _client():
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient()


def _version_key(v):
    return tuple(int(x) for x in v.split("-") if x.isdigit())


def _system_ai_names(w):
    names, token = [], None
    while True:
        q = {"parent": "schemas/system.ai", "view": "BASIC"}
        if token:
            q["page_token"] = token
        resp = w.api_client.do("GET", "/api/2.1/unity-catalog/model-services", query=q)
        for s in resp.get("model_services", []):
            n = s.get("name", "")
            names.append(n.split("system.ai.", 1)[-1])
        token = resp.get("next_page_token")
        if not token:
            return names


def _serving_names(w):
    out = []
    for e in w.serving_endpoints.list():
        if e.name and e.name.startswith("databricks-"):
            out.append(e.name[len("databricks-"):])
    return out


def _rank(model_names, prefix, source):
    ranked = []
    for name in model_names:
        if _EXCLUDE.search(name):
            continue
        for fam_rank, (fam, rx) in enumerate(FRONTIER_FAMILIES):
            m = re.match(rx, name)
            if m:
                ranked.append({"endpoint": f"{prefix}{name}", "family": fam, "version": m.group(1),
                               "source": source, "_k": (fam_rank, tuple(-x for x in _version_key(m.group(1))))})
                break
    ranked.sort(key=lambda r: r["_k"])
    for r in ranked:
        r.pop("_k")
    return ranked


def list_frontier_models(top_per_family=2):
    """Ranked frontier candidates available here. Present the top few to the user to confirm."""
    w = _client()
    try:
        ranked = _rank(_system_ai_names(w), "system.ai.", "uc_model_service")
    except Exception:
        ranked = []
    if not ranked:  # Gov / China clouds, or system.ai not enabled
        ranked = _rank(_serving_names(w), "databricks-", "serving_endpoint")
    out, seen = [], {}
    for r in ranked:
        seen[r["family"]] = seen.get(r["family"], 0) + 1
        if seen[r["family"]] <= top_per_family:
            out.append(r)
    return out


def smoke_test(endpoint):
    """Returns True if ai_query can call the endpoint (needs EXECUTE / CAN QUERY)."""
    if not re.fullmatch(r"[\w.\-]+", endpoint):
        raise ValueError("invalid endpoint name")
    r = spark.sql(f"SELECT ai_query('{endpoint}', 'Reply with the single word OK', failOnError => false) AS r").first()[0]  # noqa: F821
    d = r.asDict() if hasattr(r, "asDict") else {"result": r}
    return bool(d.get("result") or d.get("response")) and not (d.get("errorMessage") or d.get("errorStatus"))
