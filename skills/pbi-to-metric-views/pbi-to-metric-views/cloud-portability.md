# Running on any cloud (AWS, Azure, GCP) and any workspace

* **Paths**: resolve with `default_paths()` (uses `current_user()`); skill, repo and outputs live
  under `/Workspace/Users/<user>/`. Input files: UC Volumes (`/Volumes/c/s/v/...`) - same syntax on
  every cloud. Do not use cloud URIs (s3://, abfss://, gs://) unless the user gives one and an
  external location already covers it.
* **Engine**: cloned from GitHub into the user's home on demand (`runGit` clone). If GitHub is not
  reachable (private network), ask the user to import the repo into the workspace and pass
  `repo_path=`.
* **Compute**: serverless notebooks/SQL where available; otherwise any UC-enabled cluster
  (DBR 15.4+ for metric views / row filters; metric-view window measures need a recent DBR) or a
  SQL warehouse for the DDL.
* **LLM**: `list_frontier_models()` discovers what the region offers; `system.ai` is absent on
  Azure Gov/China and AWS GovCloud/DoD -> serving endpoints fallback; some models are routed
  cross-geo only - if `smoke_test` fails for that reason, use the next candidate.
* **Identity / RLS**: `is_account_group_member` and `current_user()` work the same everywhere;
  Power BI uses Entra ID UPNs - on AWS/GCP make sure users are SCIM-synced with the same emails.
* **Power BI API**: always Azure-hosted (api.powerbi.com); reachable from any Databricks cloud
  with outbound internet. Credentials only via secret scopes.
* **Workspace policies**: never assume a specific org policy. Read workspace instructions; if
  they require tags (e.g. `RemoveAfter`), per-user schemas or naming prefixes, apply them.
* **Naming**: objects created by the skill use descriptive names (`<fact>_metric_view`,
  `rls_<table>`, `<model> refresh`); scratch objects use the `_mv_tmp` / `tmp_` prefixes and are
  dropped at the end.
