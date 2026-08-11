# Critique vòng 1 — TASK-002

## Đánh giá chung
Spec khung tốt, phạm vi In/Out tách P0 khỏi P0.5/P1/P2 đúng. Nhưng có 3 P1 (AC9 mâu thuẫn .gitignore, HealthReport không định nghĩa, config path mơ hồ) + 6 P2 + 5 P3. **Sẵn sàng: 3/5 — cần sửa trước khi implement.**

## Các vấn đề + Resolution

### P1-1 — AC9 mâu thuẫn `.gitignore`: settings.json đang bị ignore
- Vấn đề: Spec nói track `.vscode/settings.json` nhưng .gitignore vẫn ignore nó (quyết định M0).
- **Resolution — CHỌN (a) track cả settings.json**: bỏ dòng `.vscode/settings.json` khỏi .gitignore; cam kết settings chỉ dùng `${workspaceFolder}` tương đối, không đường dẫn máy (verify trước commit). Đưa bước sửa .gitignore vào In TASK-002.

### P1-2 — `HealthReport` không định nghĩa, AC7 không kiểm chứng được
- Vấn đề: Không có field của HealthReport, không có rule tổng hợp trạng thái.
- **Resolution**: Định nghĩa tối thiểu trong spec: `HealthReport` dataclass (`name: str`, `status: HealthStatus`, `message: str = ""`, `timestamp: datetime = now`); rule **worst-wins** (`unhealthy > degraded > healthy`); `register` trùng name → `ValueError`; `get_all() -> list[HealthReport]`; `report() -> HealthReport` tổng hợp. AC7 sửa thành case cụ thể (1 healthy + 1 degraded → degraded; 1 healthy + 1 unhealthy → unhealthy).

### P1-3 — Đường dẫn tìm `config.yaml` + định nghĩa "default" mơ hồ
- Vấn đề: src layout → config.yaml ngoài package; CWD khác nhau khi chạy test từ root vs backend/; "default" không định nghĩa.
- **Resolution**: Search order tường minh: `AIOS_CONFIG_PATH` (env) → `<CWD>/config.yaml` → **defaults nhúng trong code** (dict mặc định trong `config.py`). "Default" = model defaults pydantic; YAML override field có mặt; **precedence: env > YAML > model defaults**. Test tách: thiếu file → dùng default; thiếu key trong file → dùng default cho key đó.

### P2-1 — Env override nested fields + extra
- Vấn đề: `AIOS_LOG_LEVEL` không override được field nested; typo env bị nuốt im.
- **Resolution**: `env_nested_delimiter="__"` (VD `AIOS_LOGGING__LEVEL=DEBUG`), `extra="forbid"` cho Settings (typo → ValidationError rõ ràng). Thêm test: env nested override + env sai type → lỗi rõ.

### P2-2 — Correlation id: thread-safe dict kém, thiếu test + idempotent
- Vấn đề: dict theo thread rò rỉ + không async-safe; setup 2 lần nhân đôi handler; log dir thiếu crash.
- **Resolution**: dùng `contextvars.ContextVar[str | None]` + `logging.Filter` set field `correlation_id`; JSON formatter in field khi tồn tại. Setup **idempotent** (guard handler đã tồn tại), `mkdir(parents=True, exist_ok=True)` cho log dir. Thêm 3 test: JSON field có correlation_id; setup 2 lần không nhân đôi; log dir tự tạo.

### P2-3 — Metadata: "dataclass/pydantic" mơ hồ, type field chưa định nghĩa
- Vấn đề: phải chọn 1; type checksum/permissions/health/dependencies không rõ.
- **Resolution**: **pydantic BaseModel** (validator semver); bảng field-type đầy đủ: `id: str`, `name: str`, `version: str` (validator semver — regex chuẩn cho phép pre-release + build metadata), `author: str`, `created/updated: datetime` (ISO 8601, default now), `license: str`, `dependencies: list[str] = []`, `permissions: list[str] = []`, `tags: list[str] = []`, `health: HealthStatus | None = None`, `checksum: str | None = None` (sha256 — do component tự tính khi tạo artifact, helper không tự tính). `make_component_metadata()` nhận field cơ bản + defaults.

### P2-4 — pytest từ root + coverage threshold
- Vấn đề: src layout → `pytest backend/tests` từ root lỗi ModuleNotFoundError; coverage ghi nhưng không có ngưỡng.
- **Resolution**: pyproject `[tool.pytest.ini_options]` `testpaths = ["tests"]`, `pythonpath = ["src"]`; AC2 sửa: pytest pass + coverage ≥ **80%** trên `aios_core/` (`--cov-fail-under=80`). README ghi rõ 2 lệnh (từ backend/ và từ root).

### P2-5 — pyproject metadata + pin version + single source version
- Vấn đề: chưa pin con số; thiếu license/readme/authors; version 2 nơi dễ lệch.
- **Resolution**: version **dynamic** từ `src/aios_core/__init__.py` (hatchling `[tool.hatch.version] path`); `license = "MIT"`, `readme`, `authors`; pin: `pydantic>=2.10`, `pydantic-settings>=2.4`, `pyyaml>=6.0`; dev: `pytest>=8`, `pytest-cov>=5`.

### P2-6 — Scaffold monorepo: toàn bộ cây theo PLAN hay tạo dần?
- Vấn đề: Mục tiêu nói "scaffold theo PLAN" nhưng In chỉ tạo aios_core + sdk stubs.
- **Resolution — CHỌN (a) tạo toàn bộ cây**: tạo đầy đủ `backend/{core,contracts,kernel,orchestrator,catalog,policy,goals,models,memory,knowledge,workflow,agents,capabilities,tools,skills,sandbox,evaluation,prompts,observability,api,cli}/` + `dashboard/`, `extension/`, `skills/`, `docker/` với `.gitkeep` — cấu trúc nằm trong repo từ đầu, PROGRESS đối chiếu được với PLAN. Thêm AC tương ứng.

### P3-1 — sdk stub không định nghĩa → 2 README stub (mục đích + trạng thái "chưa code")
### P3-2 — AC3 thiếu test tự động → thêm `tests/test_import.py` (import + `__version__` regex + exports)
### P3-3 — Semver pre-release → regex chuẩn cho phép pre-release/build metadata + 1 test case
### P3-4 — pip install cần network lần đầu → thêm R4; ghi chú log rotation để P8
### P3-5 — tasks.json nội dung → 1 task "Test: run pytest backend" (label, type shell, `cd backend && pytest`)

## Kết luận
- [x] **Đã resolve toàn bộ (3 P1 + 6 P2 + 5 P3)** — spec sẽ được cập nhật theo resolution trên, chuyển sang critique vòng 2.

*(Nội dung phản biện gốc do subagent critic sinh ra; resolution bởi AIOS Orchestrator.)*
