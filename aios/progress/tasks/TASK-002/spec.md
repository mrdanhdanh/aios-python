# TASK-002 — M1/P0: Scaffold Monorepo + Backend Core Infrastructure

## Mục tiêu
Khởi tạo cấu trúc monorepo AIOS theo `docs/PLAN.md` (M1-P0) và xây dựng `aios_core` — package nền tảng đầu tiên của backend: config, logging, AIOS metadata, healthcheck. Đây là nền cho mọi module sau (kernel, contracts, models...) — cấu trúc package và config phải đúng ngay từ đầu để không refactor.

## Phạm vi
- **In**:
  1. **Scaffold toàn bộ cây monorepo theo PLAN.md** (P2-6): `backend/{core,contracts,kernel,orchestrator,catalog,policy,goals,models,memory,knowledge,workflow,agents,capabilities,tools,skills,sandbox,evaluation,prompts,observability,api,cli}/` + `dashboard/`, `extension/`, `skills/`, `docker/` — mỗi thư mục có `.gitkeep` (trống, chờ task tương ứng)
  2. `backend/` — Python package `aios_core` (src layout; **quy ước M1: code gom vào `backend/src/<package>/`** — `backend/core/` theo PLAN chính là `aios_core`, placeholder `.gitkeep` giữ nguyên; DI container TASK-003 thêm vào `backend/src/aios_core/container.py`, không tạo package thứ 2):
     - `config.py` — loader config từ YAML + ENV override (pydantic-settings): search order `AIOS_CONFIG_PATH` (env) → `<CWD>/config.yaml` → **defaults nhúng trong code**; precedence **env > YAML > model defaults**; `env_nested_delimiter="__"`; `extra="forbid"` (chặn key không khai báo trong YAML — KHÔNG phải để bắt typo env); **validate env tường minh**: scan `os.environ` prefix `AIOS_` so với field names → env lạ raise `ValueError` liệt kê tên
     - `logging.py` — setup chuẩn: console (human) + file (JSON lines, utf-8, pathlib), level từ config, **contextvars.ContextVar** correlation id + `logging.Filter` → field `correlation_id` trong JSON; setup **idempotent**; `mkdir(parents=True, exist_ok=True)` cho log dir; **JSON field set tối thiểu ổn định**: `ts`, `level`, `logger`, `message`, `correlation_id` (nếu có) — để P8 không phải đổi format phá file log
     - `metadata.py` — `AiOSMetadata` **pydantic BaseModel**: `id: str`, `name: str`, `version: str` (validator semver — **regex chuẩn semver.org**, cho phép pre-release + build metadata), `author: str`, `created/updated: datetime` (ISO 8601, `default_factory=datetime.now(timezone.utc)` — aware; helper override `created` khi truyền vào, `updated >= created`), `license: str`, `dependencies: list[str] = []`, `permissions: list[str] = []`, `tags: list[str] = []`, `health: HealthStatus | None = None`, `checksum: str | None = None` (sha256, component tự tính); helper `make_component_metadata(*, id: str, name: str, version: str, author: str = "AIOS", license: str = "MIT", dependencies: list[str] = [], permissions: list[str] = [], tags: list[str] = [], created: datetime | None = None)` — `checksum`/`health` luôn `None`
     - `healthcheck.py` — `HealthStatus` enum (healthy/degraded/unhealthy), `HealthReport` dataclass (`name: str`, `status: HealthStatus`, `message: str = ""`, `timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))` — aware, KHÔNG dùng default `now()` trực tiếp — bẫy import-time), `HealthCheck` ABC (`check() -> HealthReport`), `HealthRegistry` — `register` (trùng name → `ValueError`), `get_all() -> list[HealthReport]`, `report() -> HealthReport` tổng hợp **worst-wins** (unhealthy > degraded > healthy); registry rỗng → `degraded` + message "no checks registered"; `check()` ném exception → bắt → report degraded thay vì crash
     - `__init__.py` — `__version__` (semver), exports: `get_logger`, `setup_logging`, `AiOSMetadata`, `make_component_metadata`, `HealthStatus`, `HealthReport`, `HealthCheck`, `HealthRegistry`
  3. `backend/pyproject.toml` — `[build-system] requires = ["hatchling"]`, `build-backend = "hatchling.build"`; `[project]` `name = "aios-core"`, `description`, **`dynamic = ["version"]`**, `license = "MIT"`, `readme`, `authors`, `requires-python >=3.11`; deps: `pydantic>=2.10`, `pydantic-settings>=2.4`, `pyyaml>=6.0`; dev: `pytest>=8`, `pytest-cov>=5`; `[tool.hatch.version] path = "src/aios_core/__init__.py"`; `[tool.pytest.ini_options]` `testpaths = ["tests"]`, `pythonpath = ["src"]`, **`addopts = "--cov=aios_core --cov-report=term-missing --cov-fail-under=80"`**
  4. `backend/config.yaml` — bảng field tối thiểu: `app: {name: "aios", env: "dev"}`; `logging: {level: "INFO", console: true, file: true, file_path: "aios/logs/aios.jsonl"}`
  5. `backend/tests/` — test_config (load default CWD-independent, thiếu file, thiếu key, env override nested, **env typo → ValueError**, `AIOS_CONFIG_PATH` hợp lệ / không tồn tại, **YAML extra key → ValidationError**, spike thực tế), test_metadata (semver + pre-release + **build metadata**, fields, `make_component_metadata`), test_healthcheck (registry, worst-wins, trùng name, **registry rỗng, exception trong check**), test_logging (JSON + correlation_id, idempotent, mkdir — **mọi test dùng `tmp_path` + `monkeypatch.chdir(tmp_path)`, không ghi log vào default path**), test_import (import + `__version__` regex + **đủ exports pin**) — **mọi test config dùng `monkeypatch.chdir(tmp_path)` + setenv/delenv → CWD-independent**
  6. `sdk/python/` + `sdk/typescript/` — stub: mỗi bên 1 README.md (mục đích + roadmap trỏ PLAN + trạng thái "chưa code")
  7. `.gitignore` — **bỏ dòng `.vscode/settings.json`** (track cả settings.json + tasks.json; settings chỉ dùng `${workspaceFolder}` tương đối, verify trước commit)
  8. `.vscode/settings.json` (python, test config — tương đối, không đường dẫn máy) + `.vscode/tasks.json` (1 task "Test: run pytest backend": type shell, `cd backend && pytest`)
  9. `docs/README.md` — tổng quan dự án + lệnh chạy test (từ `backend/` và từ root) + ghi chú log rotation chờ P8
- **Out (không làm)**:
  - DI container, event bus, 9 services, contracts → TASK-003 (P0.5)
  - Model providers, memory, knowledge → P1
  - Workflow engine, capability → P2
  - Code SDK thật sự (chỉ stub README)

## Yêu cầu chi tiết
1. Cấu trúc package theo src layout: `backend/src/aios_core/` + `backend/tests/`; toàn bộ cây monorepo theo PLAN có `.gitkeep`
2. Config: search order `AIOS_CONFIG_PATH` (env) → `<CWD>/config.yaml` → defaults nhúng trong `config.py` (model defaults pydantic); precedence **env > YAML > model defaults**; `env_nested_delimiter="__"` (VD `AIOS_LOGGING__LEVEL=DEBUG`); `extra="forbid"` chặn key không khai báo trong `config.yaml`; **validate env tường minh**: scan `os.environ` prefix `AIOS_` so với field names → env lạ raise `ValueError` liệt kê tên (vì `extra="forbid"` KHÔNG bắt typo env trong pydantic-settings v2 — đã xác minh qua critique-2); **env validator phải whitelist `AIOS_CONFIG_PATH`** (env điều khiển search order, không phải field — nếu không AC13/AC14 fail); thiếu file hoặc thiếu key → dùng default, không crash
3. Logging: `get_logger(name)` trả logger đã setup; console human-readable, file JSON lines (utf-8, pathlib); level từ config; correlation id qua `contextvars.ContextVar[str | None]` + `logging.Filter` → field `correlation_id` trong JSON khi có; setup idempotent (không nhân đôi handler); log dir tự tạo `mkdir(parents=True, exist_ok=True)`
4. Metadata: pydantic BaseModel, bảng field-type như Phạm vi In mục 2; version validator regex chuẩn semver.org (pre-release + build metadata hợp lệ); `make_component_metadata()` signature đã pin (id bắt buộc, checksum/health luôn None)
5. Healthcheck: đúng định nghĩa Phạm vi In mục 2 — `HealthReport`, worst-wins, register trùng → `ValueError`
6. `pyproject.toml` đúng chuẩn (build-system + dynamic version theo Phạm vi In mục 3), install được (`pip install -e ".[dev]"`), python >=3.11 (máy 3.13.14)
7. Test: pytest pass với **coverage ≥ 80% trên `aios_core/`** — pin trong `addopts` (cả 2 cách chạy tự đồng nhất); 2 lệnh chính xác: từ `backend/` = `pytest`; từ root = `pytest backend/tests`; mọi test config/logging dùng `tmp_path` + `monkeypatch.chdir(tmp_path)` — CWD-independent, không ghi vào default path
8. Tất cả code + docs tiếng Anh (trừ tài liệu progress tiếng Việt theo AGENTS.md)

## Input / Output
- Input: `docs/PLAN.md` (cấu trúc monorepo mục), Python 3.13.14, pip 26
- Output: cấu trúc `backend/` + `sdk/*` + `docs/README.md` + `.vscode/` workspace settings, test pass, commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: `pip install -e ".[dev]"` trong `backend/` thành công (venv)
- [ ] AC2: `pytest` pass với coverage ≥ 80% trên `aios_core/` (ghi số test + coverage thực tế) — chạy được từ `backend/` VÀ từ repo root
- [ ] AC3: test_import: `import aios_core` + `__version__` match regex semver + đủ exports pin: `get_logger`, `setup_logging`, `AiOSMetadata`, `make_component_metadata`, `HealthStatus`, `HealthReport`, `HealthCheck`, `HealthRegistry` — (có test)
- [ ] AC4: Env override nested: `AIOS_LOGGING__LEVEL=DEBUG` → logger level = DEBUG; **env typo `AIOS_LOGGNIG__LEVEL=DEBUG` → `ValueError` liệt kê tên env lạ**; `AIOS_LOGGING__LEVEL=foo` → ValidationError rõ ràng (có test)
- [ ] AC5: Config thiếu file → dùng default không crash; thiếu key trong file → default cho key đó (có test, tách 2 case, CWD-independent)
- [ ] AC6: Metadata version "1.0.0" ok, "1.0.0-beta.1" ok (pre-release), "1.0.0-beta.1+build.5" ok (build metadata), "1.0" → validation error (có test)
- [ ] AC7: Healthcheck: register 2 checks (healthy + degraded) → `report()` = degraded; (healthy + unhealthy) → unhealthy; register trùng name → ValueError; registry rỗng → degraded "no checks registered"; check ném exception → degraded (có test)
- [ ] AC8: `sdk/python/README.md` + `sdk/typescript/README.md` tồn tại, nêu mục đích + trạng thái "chưa code"
- [ ] AC9: `.vscode/settings.json` + `tasks.json` được track (git); settings không chứa đường dẫn máy (dùng `${workspaceFolder}`); .gitignore không còn ignore settings.json
- [ ] AC10: `docs/README.md` hướng dẫn chạy test được (ghi rõ 2 lệnh: `cd backend && pytest` / `pytest backend/tests`)
- [ ] AC11: Toàn bộ cây monorepo theo PLAN tồn tại với `.gitkeep` (backend/*, dashboard/, extension/, skills/, docker/)
- [ ] AC12: Correlation id: set ContextVar → JSON line trong file có field `correlation_id`; setup logger 2 lần không nhân đôi handler; log dir chưa tồn tại → tự tạo (có test, dùng tmp_path)
- [ ] AC13: `AIOS_CONFIG_PATH` trỏ file custom → file đó thắng `<CWD>/config.yaml` (có test)
- [ ] AC14: `AIOS_CONFIG_PATH` trỏ file không tồn tại → fallback default không crash (có test)
- [ ] AC15: `config.yaml` chứa key không khai báo → ValidationError (có test)
- [ ] AC16: `make_component_metadata()` defaults đúng (author="AIOS", license="MIT", checksum/health None) + version invalid → ValidationError (có test)

## Phụ thuộc
- M0 hoàn thành (agent + progress hệ thống) — done
- Python 3.13.14 + pip — đã xác nhận
- Network cho `pip install` lần đầu (PyPI) — xem R4
- Không phụ thuộc Docker/LLM

## Rủi ro
- R1: pydantic-settings cú pháp version mới khác docs cũ → pin version rõ (pydantic>=2.10, pydantic-settings>=2.4), test ngay từ đầu
- R2: Windows path/encoding (JSON log file) → pathlib + utf-8 explicit
- R3: Over-engineer healthcheck → giữ interface tối thiểu (định nghĩa đã chốt ở critique-1 P1-2)
- R4: `pip install` cần network lần đầu (PyPI) — nếu máy offline: kiểm tra pip cache/wheels trước; nếu vẫn blocked → báo blocked sớm, không phát hiện lúc implement
- R5: Log file không rotation ở M1 (chấp nhận) — ghi chú trong code + docs để P8 observability xử lý
