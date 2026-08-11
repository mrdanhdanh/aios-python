# TASK-002 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Package core (config, logging, metadata, healthcheck) | `backend/src/aios_core/` |
| Build config | `backend/pyproject.toml`, `backend/config.yaml`, `backend/README.md` |
| Tests (32) | `backend/tests/` |
| SDK stubs | `sdk/python/README.md`, `sdk/typescript/README.md` |
| Workspace | `.vscode/settings.json`, `.vscode/tasks.json` |
| Docs | `docs/README.md`; note quy ước layout trong `docs/PLAN.md` |
| Cây monorepo (25 thư mục .gitkeep) | `backend/*`, `dashboard/`, `extension/`, `skills/`, `docker/` |

## Quyết định kỹ thuật (đã qua critique/review)

- **Config**: search order `AIOS_CONFIG_PATH` → `<CWD>/config.yaml` → model defaults; env `AIOS_*` với `__` delimiter; env lạ → ValueError (validate tường minh, whitelist `AIOS_CONFIG_PATH`); YAML extra key → ValidationError.
- **Logging**: JSON field set ổn định (`ts, level, logger, message, correlation_id`); correlation id qua `contextvars`; setup idempotent; mkdir log dir.
- **Metadata**: `AiOSMetadata` pydantic, semver regex chuẩn semver.org (pre-release + build), timestamps aware UTC; `make_component_metadata` với defaults (checksum/health luôn None).
- **Healthcheck**: worst-wins; registry rỗng → degraded; exception trong check → degraded; `timestamp` dùng `default_factory` (tránh bẫy import-time).
- **Layout M1**: src layout `backend/src/<package>/`; `backend/core/` ≡ `aios_core`; DI container TASK-003 → `backend/src/aios_core/container.py`.
