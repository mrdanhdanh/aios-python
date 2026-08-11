# TASK-002 — Breakdown checklist

> Quy ước: `[x]` = đã làm XONG VÀ đã verify (chạy được / kiểm chứng thấy kết quả).

## C1 — Scaffold cây monorepo
- [ ] C1.1 Tạo toàn bộ thư mục theo PLAN + `.gitkeep`: `backend/{core,contracts,kernel,orchestrator,catalog,policy,goals,models,memory,knowledge,workflow,agents,capabilities,tools,skills,sandbox,evaluation,prompts,observability,api,cli}` + `dashboard/`, `extension/`, `skills/`, `docker/` (chỉ .gitkeep)
- [ ] C1.2 `sdk/python/README.md` + `sdk/typescript/README.md` (mục đích + roadmap + trạng thái "chưa code")

## C2 — Package `aios_core`
- [ ] C2.1 `backend/pyproject.toml` (build-system, dynamic version, pins, pytest addopts)
- [ ] C2.2 `backend/src/aios_core/__init__.py` (`__version__` + exports pin)
- [ ] C2.3 `config.py` — Settings model (app, logging), search order 3 bậc, env validate tường minh, delimiter `__`, extra forbid
- [ ] C2.4 `logging.py` — setup_logging idempotent + get_logger + JSON formatter + ContextVar correlation id + mkdir
- [ ] C2.5 `metadata.py` — AiOSMetadata + semver validator (regex semver.org) + make_component_metadata
- [ ] C2.6 `healthcheck.py` — HealthStatus, HealthReport, HealthCheck ABC, HealthRegistry (worst-wins, rỗng → degraded, exception → degraded)
- [ ] C2.7 `backend/config.yaml` — app + logging (bảng field đã pin)
- [ ] C2.8 Tạo `backend/.venv` + `pip install -e ".[dev]"` (verify AC1; kiểm tra network theo R4 — nếu offline báo blocked sớm)

## C3 — Tests
- [ ] C3.1 `tests/test_import.py` — import + __version__ regex + exports
- [ ] C3.2 `tests/test_config.py` — default CWD-independent, thiếu file, thiếu key, env nested, env typo → ValueError, **whitelist AIOS_CONFIG_PATH**, AIOS_CONFIG_PATH (2 case), YAML extra key, env sai type
- [ ] C3.3 `tests/test_metadata.py` — semver 4 case, fields, make_component_metadata (updated >= created)
- [ ] C3.4 `tests/test_healthcheck.py` — registry, worst-wins, trùng name, rỗng, exception, timestamp khác nhau giữa 2 report
- [ ] C3.5 `tests/test_logging.py` — JSON field set (ts/level/logger/message/correlation_id), idempotent, mkdir (tmp_path)
- [ ] C3.6 Chạy pytest từ `backend/` + từ root → pass, coverage ≥ 80%
- [ ] C3.7 Ghi `test.md` (kết quả pytest thật: số test pass, coverage %)

## C4 — Workspace & docs
- [ ] C4.1 `.gitignore` — bỏ ignore `.vscode/settings.json` + thêm `backend/aios/logs/` (chặn rác khi chạy tay)
- [ ] C4.2 `.vscode/settings.json` (tương đối, `${workspaceFolder}`) + `.vscode/tasks.json` (task "Test: run pytest backend": `.venv/Scripts/python -m pytest` — chạy được cả khi chưa activate venv)
- [ ] C4.3 `docs/README.md` — tổng quan + 2 lệnh test + lưu ý activate venv + ghi chú log path CWD-relative + log rotation (P8)
- [ ] C4.4 Note quy ước layout M1 vào `docs/PLAN.md` (backend/core ≡ aios_core, code tại backend/src/, container.py TASK-003)

## C5 — Commit
- [ ] C5.1 Commit từng nhóm (C1 → C2 → C3 → C4), message tiền tố `M1-P0: ...`; verify `.gitkeep` có trong git status (git add tường minh)
- [ ] C5.2 Working tree sạch cuối task
- [ ] C5.3 Ghi `evaluation.md` (đối chiếu 16 AC) + cập nhật PROGRESS.md/LOG.md/STATS.md + commit cuối
