"""
process_migrate.py - Migrate the PROCESSES that live in a Power BI model (not only measures):

  * Power Query (M) partitions / dataflows -> Lakeflow Spark Declarative Pipeline SQL
    (one materialized view per PBI table, CTE per M step)
  * Calculated columns (DAX row context)  -> extra SELECT expressions in that MV
  * Calculated tables (partition = calculated, e.g. CALENDAR) -> MV SQL
  * RLS roles (tablePermission filters)    -> UC row-filter SQL functions + ALTER TABLE
  * Dataset refresh schedule              -> Lakeflow Job spec (pipeline task, Quartz cron)
  * Report pages/visuals (.pbix)          -> layout summary for the AI/BI dashboard hand-off

Rule-based first; everything the rules cannot convert is returned in `llm_todo` so the agent can
call llm_translate.llm_translate_text(...) (ai_query with a frontier model) and then re-validate.
Pure Python except where noted; it never executes DDL - the agent does, after validation.

Usage:
    exec(open(f"{SKILL_DIR}/scripts/process_migrate.py").read())
    tm   = parse_tmdl_processes("/Volumes/c/s/v/Model.zip")
    plan = build_process_plan(tm, catalog="main", schema="silver",
                              source_mappings={"dbo.Sales": "main.bronze.sales"},
                              role_groups={"Sales LATAM": "pbi_sales_latam"}, admin_group="pbi_admins")
    plan["pipeline_sql"], plan["rls_sql"], plan["llm_todo"], plan["unmapped_sources"]
    job = refresh_job_spec("PBI Sales refresh", pipeline_id="<id>", days=["Monday"], times=["07:00"], timezone="UTC")
"""
import io, json, os, re, zipfile


def _san(s):
    s = re.sub(r"[^a-zA-Z0-9_]", "_", str(s).strip().lower())
    return re.sub(r"_+", "_", s).strip("_")


def _unq(s):
    s = s.strip()
    if len(s) > 1 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    if s.startswith('#"') and s.endswith('"'):
        return s[2:-1]
    return s


# =============================================================== TMDL parsing
def _read_tmdl_texts(path):
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            return [z.read(n).decode("utf-8-sig") for n in z.namelist() if n.endswith(".tmdl")]
    if os.path.isdir(path):
        out = []
        for root, _, files in os.walk(path):
            out += [open(os.path.join(root, f), encoding="utf-8-sig").read() for f in files if f.endswith(".tmdl")]
        return out
    return [open(path, encoding="utf-8-sig").read()]


def _indent(line):
    raw = line[: len(line) - len(line.lstrip("\t "))]
    return raw.count("\t") + raw.count(" ") // 4


def _name_and_expr(rest):
    """"'My Col' = expr" -> ("My Col", "expr");  "Col" -> ("Col", None)"""
    m = re.match(r"\s*('(?:[^']|'')+'|\"[^\"]+\"|[^=\s]+)\s*(?:=\s*(.*))?$", rest)
    if not m:
        return rest.strip(), None
    return _unq(m.group(1)).replace("''", "'"), (m.group(2).strip() if m.group(2) is not None else None)


def _collect_block(lines, i, base_indent):
    """Collect continuation lines deeper than base_indent (multi-line expressions)."""
    buf = []
    while i < len(lines) and (not lines[i].strip() or _indent(lines[i]) > base_indent):
        buf.append(lines[i].strip("\r"))
        i += 1
    txt = "\n".join(l.strip() for l in buf).strip()
    txt = re.sub(r"^```|```$", "", txt).strip()
    return txt, i


def parse_tmdl_processes(path_or_text):
    """Returns {tables: {name: {columns:[{name,dataType,sourceColumn,expression}], partitions:[{name,kind,source}]}},
                roles: [{name, members:[], filters:{table: dax}}], expressions: {name: m}}"""
    texts = [path_or_text] if "\n" in path_or_text else _read_tmdl_texts(path_or_text)
    model = {"tables": {}, "roles": [], "expressions": {}}
    for text in texts:
        lines = text.split("\n")
        i, table, role, col, part = 0, None, None, None, None
        while i < len(lines):
            line = lines[i]
            s = line.strip()
            ind = _indent(line)
            i += 1
            if not s or s.startswith("///"):
                continue
            kw, _, rest = s.partition(" ")
            if ind == 0:
                table = role = col = part = None
                if kw == "table":
                    name, _ = _name_and_expr(rest)
                    table = model["tables"].setdefault(name, {"columns": [], "partitions": []})
                elif kw == "role":
                    name, _ = _name_and_expr(rest)
                    role = {"name": name, "members": [], "filters": {}}
                    model["roles"].append(role)
                elif kw == "expression":  # shared M expressions / parameters
                    name, expr = _name_and_expr(rest)
                    if expr in (None, ""):
                        expr, i = _collect_block(lines, i, 0)
                    model["expressions"][name] = expr
                continue
            if table is not None and ind == 1:
                col = part = None
                if kw in ("column", "calculatedColumn"):
                    name, expr = _name_and_expr(rest)
                    if expr == "":
                        expr, i = _collect_block(lines, i, 1)
                    col = {"name": name, "dataType": "", "sourceColumn": name, "expression": expr}
                    table["columns"].append(col)
                elif kw == "partition":
                    name, kind = _name_and_expr(rest)
                    part = {"name": name, "kind": (kind or "").lower(), "source": ""}
                    table["partitions"].append(part)
                continue
            if table is not None and ind >= 2:
                if col is not None and kw.rstrip(":") == "dataType":
                    col["dataType"] = rest.strip()
                elif col is not None and kw.rstrip(":") == "sourceColumn":
                    col["sourceColumn"] = _unq(rest)
                elif part is not None and s.startswith("source"):
                    inline = s.split("=", 1)[1].strip() if "=" in s else ""
                    block, i = _collect_block(lines, i, ind)
                    part["source"] = (inline + "\n" + block).strip()
                continue
            if role is not None and ind >= 1:
                if kw == "member":
                    role["members"].append(_unq(rest))
                elif kw == "tablePermission":
                    tname, expr = _name_and_expr(rest)
                    if expr == "":
                        expr, i = _collect_block(lines, i, ind)
                    role["filters"][tname] = expr
    return model


# =============================================================== M (Power Query) -> SQL
M_TYPES = {"int64.type": "BIGINT", "type number": "DOUBLE", "number.type": "DOUBLE", "type text": "STRING",
           "text.type": "STRING", "type date": "DATE", "date.type": "DATE", "type datetime": "TIMESTAMP",
           "datetime.type": "TIMESTAMP", "type datetimezone": "TIMESTAMP", "type logical": "BOOLEAN",
           "logical.type": "BOOLEAN", "currency.type": "DECIMAL(19,4)", "percentage.type": "DOUBLE",
           "int32.type": "INT", "type time": "STRING"}


def _split_top(s, sep=","):
    out, depth, cur, q = [], 0, "", None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch == '"':
            q = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _m_steps(m):
    mm = re.search(r"\blet\b(.*)\bin\b\s*(.+?)\s*$", m, re.S)
    if not mm:
        return [], None
    steps = []
    for part in _split_top(mm.group(1)):
        k, _, v = part.partition("=")
        steps.append((_unq(k.strip()), v.strip()))
    return steps, _unq(mm.group(2).strip())


def _m_list(s):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
    return [x.strip() for x in _split_top(s)]


def _q(c):
    return "`" + _unq(c).replace("`", "``") + "`"


def m_condition_to_sql(cond):
    """`each [Amount] > 0 and [Region] <> "X"` -> `Amount` > 0 AND `Region` <> 'X'. None if unsupported."""
    c = re.sub(r"^\s*each\s+", "", cond.strip())
    c = re.sub(r"\[([^\]]+)\]\s*=\s*null", lambda m: f"{_q(m.group(1))} IS NULL", c)
    c = re.sub(r"\[([^\]]+)\]\s*<>\s*null", lambda m: f"{_q(m.group(1))} IS NOT NULL", c)
    c = re.sub(r"Text\.Contains\(\s*\[([^\]]+)\]\s*,\s*\"([^\"]*)\"\s*\)",
               lambda m: f"contains({_q(m.group(1))}, '{m.group(2)}')", c)
    c = re.sub(r"Text\.StartsWith\(\s*\[([^\]]+)\]\s*,\s*\"([^\"]*)\"\s*\)",
               lambda m: f"startswith({_q(m.group(1))}, '{m.group(2)}')", c)
    c = re.sub(r"Date\.(Year|Month|Day)\(\s*\[([^\]]+)\]\s*\)", lambda m: f"{m.group(1).lower()}({_q(m.group(2))})", c)
    c = re.sub(r"#date\((\d+),\s*(\d+),\s*(\d+)\)", lambda m: f"DATE'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'", c)
    c = re.sub(r"\[([^\]]+)\]", lambda m: _q(m.group(1)), c)
    c = re.sub(r"\"([^\"]*)\"", lambda m: "'" + m.group(1).replace("'", "''") + "'", c)
    c = re.sub(r"\band\b", "AND", c)
    c = re.sub(r"\bor\b", "OR", c)
    c = re.sub(r"\bnot\b", "NOT", c)
    c = re.sub(r"\bnull\b", "NULL", c)
    c = re.sub(r"\btrue\b", "TRUE", c)
    c = re.sub(r"\bfalse\b", "FALSE", c)
    if re.search(r"\b[A-Z][a-zA-Z]+\.[A-Z][a-zA-Z]+\(", c) or "each" in c or "=>" in c:
        return None  # remaining M library calls / lambdas -> LLM
    return c


def m_to_sql(m_expr, source_mappings, shared_expressions=None):
    """Translate a Power Query `let ... in` into a Databricks SQL query (CTE per step).
    Returns (sql_or_None, unsupported_steps, unmapped_sources)."""
    shared_expressions = shared_expressions or {}
    steps, final = _m_steps(m_expr)
    if not steps:
        return None, ["not a let..in expression"], []
    ctes, kinds, unsupported, unmapped = {}, {}, [], []
    db_ctx = {}

    def ref(name):
        return _san(_unq(name)) or "step"

    for name, e in steps:
        n = ref(name)
        mm = None
        if re.match(r"^(Sql\.Databases?|Snowflake\.Databases|PostgreSQL\.Database|MySQL\.Database|Oracle\.Database|"
                    r"Databricks\.Catalogs|DatabricksMultiCloud\.Catalogs|GoogleBigQuery\.Database|AmazonRedshift\.Database|"
                    r"Odbc\.DataSource|Sql\.Database)\b", e):
            args = re.findall(r'"([^"]*)"', e)
            db_ctx[n] = "/".join(args)
            kinds[n] = "connector"
            continue
        mm = re.match(r"^(\w+)\s*\{\s*\[(.*?)\]\s*\}\s*\[Data\]\s*$", e, re.S)
        if mm and (ref(mm.group(1)) in db_ctx or ref(mm.group(1)) in kinds):
            parts = dict((k.strip(), _unq(v)) for k, v in re.findall(r'(\w+)\s*=\s*("[^"]*")', mm.group(2)))
            key = ".".join(x for x in (parts.get("Schema"), parts.get("Item") or parts.get("Name")) if x)
            full = f"{db_ctx.get(ref(mm.group(1)), '')}/{key}"
            target = source_mappings.get(key) or source_mappings.get(full) or source_mappings.get(parts.get("Item", ""))
            if not target:
                unmapped.append(key or full)
                target = f"__UNMAPPED__{_san(key or full)}"
            ctes[n] = f"SELECT * FROM {target}"
            kinds[n] = "table"
            continue
        mm = re.match(r"^Csv\.Document\(\s*File\.Contents\(\s*\"([^\"]+)\"\s*\)", e)
        if mm:
            path = source_mappings.get(mm.group(1))
            if not path:
                unmapped.append(mm.group(1))
                path = "/Volumes/__UNMAPPED__/" + os.path.basename(mm.group(1).replace("\\", "/"))
            ctes[n] = f"SELECT * FROM read_files('{path}', format => 'csv', header => true)"
            kinds[n] = "table"
            continue
        mm = re.match(r"^Table\.PromoteHeaders\(\s*([^,\)]+)", e)
        if mm:
            ctes[n] = f"SELECT * FROM {ref(mm.group(1))}"
            continue
        mm = re.match(r"^Table\.SelectRows\(\s*([^,]+?)\s*,\s*(each .*)\)\s*$", e, re.S)
        if mm:
            cond = m_condition_to_sql(mm.group(2))
            if cond:
                ctes[n] = f"SELECT * FROM {ref(mm.group(1))} WHERE {cond}"
                continue
        mm = re.match(r"^Table\.(RemoveColumns|SelectColumns)\(\s*([^,]+?)\s*,\s*(\{.*\})\s*(?:,.*)?\)\s*$", e, re.S)
        if mm:
            cols = ", ".join(_q(c) for c in _m_list(mm.group(3)))
            ctes[n] = (f"SELECT * EXCEPT ({cols}) FROM {ref(mm.group(2))}" if mm.group(1) == "RemoveColumns"
                       else f"SELECT {cols} FROM {ref(mm.group(2))}")
            continue
        mm = re.match(r"^Table\.RenameColumns\(\s*([^,]+?)\s*,\s*(\{.*\})\s*(?:,.*)?\)\s*$", e, re.S)
        if mm:
            pairs = [_m_list(p) for p in _m_list(mm.group(2))]
            ex = ", ".join(_q(a) for a, b in pairs)
            al = ", ".join(f"{_q(a)} AS {_q(b)}" for a, b in pairs)
            ctes[n] = f"SELECT * EXCEPT ({ex}), {al} FROM {ref(mm.group(1))}"
            continue
        mm = re.match(r"^Table\.TransformColumnTypes\(\s*([^,]+?)\s*,\s*(\{.*\})\s*(?:,.*)?\)\s*$", e, re.S)
        if mm:
            pairs = [_m_list(p) for p in _m_list(mm.group(2))]
            if all(len(p) == 2 and p[1].lower() in M_TYPES for p in pairs):
                ex = ", ".join(_q(a) for a, _ in pairs)
                casts = ", ".join(f"CAST({_q(a)} AS {M_TYPES[t.lower()]}) AS {_q(a)}" for a, t in pairs)
                ctes[n] = f"SELECT * EXCEPT ({ex}), {casts} FROM {ref(mm.group(1))}"
                continue
        mm = re.match(r"^Table\.Distinct\(\s*([^,\)]+)\s*\)\s*$", e)
        if mm:
            ctes[n] = f"SELECT DISTINCT * FROM {ref(mm.group(1))}"
            continue
        mm = re.match(r"^Table\.AddColumn\(\s*([^,]+?)\s*,\s*\"([^\"]+)\"\s*,\s*(each .*?)(?:,\s*(type \w+|\w+\.Type))?\)\s*$", e, re.S)
        if mm:
            ex = m_condition_to_sql(mm.group(3))
            if ex:
                t = M_TYPES.get((mm.group(4) or "").lower())
                ex = f"CAST({ex} AS {t})" if t else ex
                ctes[n] = f"SELECT *, {ex} AS {_q(mm.group(2))} FROM {ref(mm.group(1))}"
                continue
        mm = re.match(r"^Table\.Group\(\s*([^,]+?)\s*,\s*(\{[^}]*\})\s*,\s*(\{.*\})\s*\)\s*$", e, re.S)
        if mm:
            keys = [_q(k) for k in _m_list(mm.group(2))]
            aggs, ok = [], True
            for a in _m_list(mm.group(3)):
                p = _m_list(a)
                fm = re.match(r"each\s+List\.(Sum|Average|Min|Max|Count|DistinctCount)\(\s*\[([^\]]+)\]\s*\)", p[1]) if len(p) > 1 else None
                if fm:
                    fn = {"Sum": "SUM", "Average": "AVG", "Min": "MIN", "Max": "MAX", "Count": "COUNT"}.get(fm.group(1))
                    aggs.append(f"COUNT(DISTINCT {_q(fm.group(2))})" if fm.group(1) == "DistinctCount"
                                else f"{fn}({_q(fm.group(2))})")
                    aggs[-1] += f" AS {_q(p[0])}"
                elif len(p) > 1 and re.match(r"each\s+Table\.RowCount\(\s*_\s*\)", p[1]):
                    aggs.append(f"COUNT(*) AS {_q(p[0])}")
                else:
                    ok = False
            if ok:
                ctes[n] = f"SELECT {', '.join(keys + aggs)} FROM {ref(mm.group(1))} GROUP BY {', '.join(keys)}"
                continue
        if re.match(r"^\w+$", e) and (ref(e) in ctes):
            ctes[n] = f"SELECT * FROM {ref(e)}"
            continue
        if e in shared_expressions:
            unsupported.append(f"{name}: references shared expression {e}")
            continue
        unsupported.append(f"{name} = {e[:300]}")
    if unsupported:
        return None, unsupported, unmapped
    names = list(ctes)
    last = ref(final) if ref(final) in ctes else names[-1]
    sql = "WITH " + ",\n".join(f"{k} AS ({v})" for k, v in ctes.items() if k != last)
    body = ctes[last]
    sql = (sql + "\n" + body) if len(ctes) > 1 else body
    return sql, [], unmapped


# =============================================================== DAX row context (calc columns, RLS)
_DAX_LEFT = re.compile(r"\b(RELATED|RELATEDTABLE|LOOKUPVALUE|CALCULATE|FILTER|ALL|EARLIER|SUMX|COUNTROWS|PATH\w*|USERPRINCIPALNAME|USERNAME|USEROBJECTID|SELECTEDVALUE|VALUES|LOOKUP\w*)\s*\(", re.I)


def dax_row_to_sql(expr, table_name="", rls=False):
    """Row-level DAX (calculated column / RLS filter) -> SQL on snake_case columns. None if not rule-convertible."""
    if not expr:
        return None
    e = expr.strip()
    if rls:
        e = re.sub(r"\b(USERPRINCIPALNAME|USERNAME)\s*\(\s*\)", "current_user()", e, flags=re.I)
    e = re.sub(r"'?([\w ]+?)'?\[([^\]]+)\]",
               lambda m: _san(m.group(2)) if _san(m.group(1)) == _san(table_name) or not table_name else f"__OTHER__{_san(m.group(1))}.{_san(m.group(2))}", e)
    e = re.sub(r"\[([^\]]+)\]", lambda m: _san(m.group(1)), e)
    e = re.sub(r"\bDIVIDE\s*\(", "try_divide(", e, flags=re.I)
    e = re.sub(r"\bBLANK\s*\(\s*\)", "NULL", e, flags=re.I)
    e = re.sub(r"\bTRUE\s*\(\s*\)", "TRUE", e, flags=re.I)
    e = re.sub(r"\bFALSE\s*\(\s*\)", "FALSE", e, flags=re.I)
    e = re.sub(r"\bISBLANK\s*\(([^()]*)\)", r"(\1 IS NULL)", e, flags=re.I)
    e = e.replace("&&", " AND ").replace("||", " OR ")
    e = re.sub(r"(?<![<>!])==?(?!=)", "=", e)
    e = re.sub(r'"([^"]*)"', lambda m: "'" + m.group(1).replace("'", "''") + "'", e)
    if "__OTHER__" in e or _DAX_LEFT.search(e.replace("current_user()", "")):
        return None
    return re.sub(r"\s+", " ", e).strip()


DAX_TYPES = {"int64": "BIGINT", "decimal": "DECIMAL(19,4)", "double": "DOUBLE", "string": "STRING",
             "datetime": "TIMESTAMP", "date": "DATE", "boolean": "BOOLEAN"}


# =============================================================== plan builder
def build_process_plan(tm, catalog, schema, source_mappings=None, role_groups=None, admin_group=None,
                       uc_table_for=None):
    """tm: output of parse_tmdl_processes. source_mappings: M source key ('dbo.Sales', 'srv/db/dbo.Sales',
    file path) -> UC table / Volume path. role_groups: PBI role -> UC account group. uc_table_for:
    PBI table -> UC table the row filter is attached to (default catalog.schema.<table>)."""
    source_mappings, role_groups, uc_table_for = source_mappings or {}, role_groups or {}, uc_table_for or {}
    pipeline_sql, llm_todo, unmapped, notes = [], [], [], []
    for tname, t in tm["tables"].items():
        target = f"{catalog}.{schema}.{_san(tname)}"
        base_cols = [c for c in t["columns"] if not c.get("expression")]
        calc_cols = [c for c in t["columns"] if c.get("expression")]
        for p in t["partitions"]:
            if p["kind"] in ("m", "entity", "") and p["source"]:
                sql, unsup, um = m_to_sql(p["source"], source_mappings, tm.get("expressions"))
                unmapped += um
                if sql is None:
                    llm_todo.append({"id": f"m::{tname}", "kind": "power_query_m", "table": tname,
                                     "source": p["source"], "unsupported_steps": unsup})
                    continue
                proj = [f"{_q(c['sourceColumn'])} AS {_san(c['name'])}" for c in base_cols] or ["*"]
                calc = []
                for c in calc_cols:
                    s = dax_row_to_sql(c["expression"], tname)
                    if s is None:
                        llm_todo.append({"id": f"calc::{tname}::{c['name']}", "kind": "dax_calculated_column",
                                         "table": tname, "source": c["expression"]})
                    else:
                        calc.append(f"{s} AS {_san(c['name'])}")
                # calculated columns reference the snake_case names -> compute in an outer SELECT
                inner = f"SELECT {', '.join(proj)} FROM (\n{sql}\n)"
                body = f"SELECT *{', ' + ', '.join(calc) if calc else ''} FROM ({inner})" if calc else inner
                pipeline_sql.append({"table": tname, "target": target,
                                     "sql": f"CREATE OR REFRESH MATERIALIZED VIEW {target}\nCOMMENT 'Migrated from Power BI partition {p['name']} (Power Query)'\nAS {body}"})
            elif p["kind"] == "calculated":
                cal = re.match(r"^\s*CALENDAR\s*\(\s*DATE\s*\((\d+),\s*(\d+),\s*(\d+)\)\s*,\s*DATE\s*\((\d+),\s*(\d+),\s*(\d+)\)\s*\)\s*$",
                               p["source"], re.I)
                if cal:
                    a = "-".join(f"{int(x):02d}" if i else f"{int(x):04d}" for i, x in enumerate(cal.groups()[:3]))
                    b = "-".join(f"{int(x):02d}" if i else f"{int(x):04d}" for i, x in enumerate(cal.groups()[3:]))
                    pipeline_sql.append({"table": tname, "target": target, "sql":
                        f"CREATE OR REFRESH MATERIALIZED VIEW {target}\nCOMMENT 'Migrated from Power BI calculated table'\n"
                        f"AS SELECT d AS date, year(d) AS year, quarter(d) AS quarter, month(d) AS month, "
                        f"date_format(d, 'MMM') AS month_name FROM (SELECT explode(sequence(DATE'{a}', DATE'{b}', INTERVAL 1 DAY)) AS d)"})
                else:
                    llm_todo.append({"id": f"calctable::{tname}", "kind": "dax_calculated_table",
                                     "table": tname, "source": p["source"]})
    # ---- RLS -> one row-filter function per table, OR-ing every role that filters it
    rls_sql = []
    by_table = {}
    for r in tm["roles"]:
        for tname, f in r["filters"].items():
            by_table.setdefault(tname, []).append((r, f))
    for tname, entries in by_table.items():
        tcols = {_san(c["name"]): DAX_TYPES.get(c.get("dataType", "").lower(), "STRING")
                 for c in tm["tables"].get(tname, {}).get("columns", [])}
        clauses, used = [], []
        for r, f in entries:
            s = dax_row_to_sql(f, tname, rls=True)
            if s is None:
                llm_todo.append({"id": f"rls::{r['name']}::{tname}", "kind": "dax_rls_filter", "table": tname,
                                 "source": f, "role": r["name"]})
                continue
            grp = role_groups.get(r["name"], f"pbi_role_{_san(r['name'])}")
            clauses.append(f"(is_account_group_member('{grp}') AND ({s}))")
            used += [c for c in tcols if re.search(rf"\b{re.escape(c)}\b", s)]
            if r["members"]:
                notes.append(f"Role '{r['name']}' members {r['members']} -> add them to UC group '{grp}'")
        if not clauses:
            continue
        used = sorted(set(used))
        fn = f"{catalog}.{schema}.rls_{_san(tname)}"
        params = ", ".join(f"{c} {tcols[c]}" for c in used)
        admin = f"is_account_group_member('{admin_group}') OR " if admin_group else ""
        uc_t = uc_table_for.get(tname, f"{catalog}.{schema}.{_san(tname)}")
        rls_sql.append({"table": tname, "function": fn, "columns": used,
                        "create_function": f"CREATE OR REPLACE FUNCTION {fn}({params})\nRETURNS BOOLEAN\n"
                                           f"COMMENT 'Migrated from Power BI RLS roles'\nRETURN {admin}" + " OR ".join(clauses),
                        "apply": f"ALTER TABLE {uc_t} SET ROW FILTER {fn} ON ({', '.join(used)})",
                        "sdp_clause": f"WITH ROW FILTER {fn} ON ({', '.join(used)})"})
    if tm["roles"] and not admin_group:
        notes.append("No admin_group given: users outside every role will see NO rows (same as PBI viewers without a role).")
    return {"pipeline_sql": pipeline_sql, "rls_sql": rls_sql, "llm_todo": llm_todo,
            "unmapped_sources": sorted(set(unmapped)), "notes": notes}


LLM_PROCESS_INSTRUCTIONS = {
    "power_query_m": "Translate this Power BI Power Query (M) script into ONE Databricks SQL SELECT (CTEs allowed) "
                     "for a Lakeflow Spark Declarative Pipeline materialized view. Source tables already exist in Unity "
                     "Catalog with these mappings: {mappings}. Output columns must be snake_case.",
    "dax_calculated_column": "Translate this DAX calculated column into ONE Databricks SQL scalar expression over the "
                             "snake_case columns of table {table}. If it uses RELATED/LOOKUPVALUE, reference the other "
                             "table as <table_snake>.<col> and explain the needed JOIN in notes.",
    "dax_calculated_table": "Translate this DAX calculated table into ONE Databricks SQL SELECT for a materialized view.",
    "dax_rls_filter": "Translate this Power BI RLS DAX filter for table {table} into ONE Databricks SQL boolean "
                      "expression over snake_case columns, usable inside a Unity Catalog row-filter function. "
                      "USERPRINCIPALNAME() -> current_user(). Lookups to other tables -> EXISTS subquery on catalog.schema.<table>.",
}


# =============================================================== refresh -> Job spec
_DAYS = {"monday": "MON", "tuesday": "TUE", "wednesday": "WED", "thursday": "THU", "friday": "FRI",
         "saturday": "SAT", "sunday": "SUN"}


def refresh_to_quartz(days, times):
    """PBI refreshSchedule (days ['Monday',..], times ['07:00','13:30']) -> list of Quartz crons.
    Times with the same minute share one cron."""
    dpart = ",".join(_DAYS[d.lower()] for d in days) if days else "*"
    by_min = {}
    for t in times or ["00:00"]:
        h, m = t.split(":")[:2]
        by_min.setdefault(int(m), []).append(int(h))
    return [f"0 {m} {','.join(str(h) for h in sorted(hs))} ? * {dpart}" for m, hs in sorted(by_min.items())]


def refresh_job_spec(job_name, pipeline_id, days, times, timezone="UTC", tags=None):
    """Jobs API 2.2 settings: one pipeline_task. If several crons are needed, create one job per cron
    (Jobs support a single schedule)."""
    crons = refresh_to_quartz(days, times)
    spec = {"name": job_name,
            "tasks": [{"task_key": "refresh_pipeline", "pipeline_task": {"pipeline_id": pipeline_id, "full_refresh": False}}],
            "schedule": {"quartz_cron_expression": crons[0], "timezone_id": timezone, "pause_status": "UNPAUSED"},
            "tags": tags or {}}
    return spec, crons


def powerbi_refresh_schedule(pbi_client, workspace_id, dataset_id):
    """Read the dataset refresh schedule with the repo's PowerBIClient (already authenticated)."""
    r = pbi_client._get(f"/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule")
    return {"days": r.get("days", []), "times": r.get("times", []), "timezone": r.get("localTimeZoneId", "UTC"),
            "enabled": r.get("enabled", False)}


# =============================================================== report -> dashboard brief
def report_layout_brief(pbix_path, repo_path=None):
    """Summarize .pbix report pages/visuals with the repo's ReportParser for the dashboard hand-off."""
    import sys
    if repo_path and repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    from backend.report_parser import ReportParser, PBI_VISUAL_TYPE_MAP
    rep = ReportParser().parse_pbix_file(pbix_path)
    d = rep.to_dict() if hasattr(rep, "to_dict") else rep
    return {"report": d, "visual_type_map": PBI_VISUAL_TYPE_MAP}
