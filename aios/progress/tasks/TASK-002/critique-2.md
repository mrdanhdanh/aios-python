# Critique vòng 2 — TASK-002

## Đánh giá chung
Spec sau vòng 1 cụ thể hơn nhiều. Vòng 2 phát hiện: **1 resolution vòng 1 áp dụng SAI cơ chế kỹ thuật** (P1-1: `extra="forbid"` không bắt typo env trong pydantic-settings v2) + 6 P2 + 3 P3. **Sẵn sàng: 3.5/5 — cần sửa trước khi implement.**

## Phần 1 — Kiểm tra resolution vòng 1
| # | Resolution | Trạng thái |
|---|-----------|------------|
| P1-1 track settings.json | ✅ OK | |
| P1-2 HealthReport + worst-wins | ✅ OK | 2 lỗ hổng nhỏ → P3-1 |
| P1-3 Search order + precedence | ⚠️ thiếu test AIOS_CONFIG_PATH | → P2-2 |
| P2-1 env delimiter + extra="forbid" | ❌ **SAI cơ chế** | → P1-1 mới |
| P2-2 ContextVar + idempotent + mkdir | ✅ OK | |
| P2-3 Metadata bảng field | ✅ OK | helper chưa có AC → P2-6 |
| P2-4 pythonpath + coverage | ⚠️ chưa pin addopts | → P2-3 |
| P2-5 Version dynamic + pin | ⚠️ thiếu build-system + dynamic=["version"] | → P2-4 |
| P2-6 Scaffold toàn cây | ⚠️ **tạo mâu thuẫn backend/core vs src/aios_core** | → P2-5 |
| P3-1→P3-5 | ✅ OK đầy đủ | |

## Phần 2 — Vấn đề mới + Resolution

### P1-1 — Claim `extra="forbid"` bắt typo env là SAI cơ chế
- Vấn đề: pydantic-settings v2 `EnvSettingsSource` chỉ đọc env khớp field khai báo; `extra="forbid"` chỉ hiệu lực với init kwargs + file sources. "typo env → ValidationError" không tự động đúng. Ngược lại `AIOS_CONFIG_PATH` (env điều khiển search order, không phải field) có thể bị coi là extra ở version quét prefix.
- **Resolution**: (a) giữ `extra="forbid"` nhưng claim ĐÚNG: chặn key không khai báo trong `config.yaml`; (b) thêm cơ chế tường minh trong `config.py`: scan `os.environ` theo prefix `AIOS_`, so với field names → env lạ raise `ValueError` liệt kê tên; (c) spike test ghi nhận thực tế (test env typo → ValueError; test `AIOS_CONFIG_PATH` hợp lệ → load OK); (d) thêm AC15: YAML chứa key không khai báo → ValidationError.

### P2-1 — Config schema chưa định nghĩa field
- **Resolution**: bảng field tối thiểu: `app.name: str = "aios"`, `app.env: str = "dev"`; `logging.level: str = "INFO"`, `logging.console: bool = True`, `logging.file: bool = True`, `logging.file_path: str = "aios/logs/aios.jsonl"`. Quy tắc bắt buộc: **mọi test logging/config dùng `tmp_path` + `monkeypatch.chdir(tmp_path)` — không ghi log vào default path khi test** (git status không bẩn).

### P2-2 — AIOS_CONFIG_PATH chưa có test + test config không isolate CWD
- **Resolution**: AC13: `AIOS_CONFIG_PATH` trỏ file custom → file đó thắng; AC14: trỏ file không tồn tại → fallback default không crash. Mọi test config: `monkeypatch.chdir(tmp_path)` + setenv/delenv → CWD-independent.

### P2-3 — Lệnh pytest từ root + addopts chưa pin
- **Resolution**: `addopts = "--cov=aios_core --cov-report=term-missing --cov-fail-under=80"` trong `[tool.pytest.ini_options]`; 2 lệnh chính xác: từ `backend/` = `pytest`; từ root = `pytest backend/tests` (ghi vào docs/README + test.md).

### P2-4 — pyproject thiếu build-system + dynamic version
- **Resolution**: bổ sung bảng đầy đủ: `[build-system] requires = ["hatchling"]`, `build-backend = "hatchling.build"`; `[project] name = "aios-core"`, `description`, `dynamic = ["version"]`; `[tool.hatch.version] path = "src/aios_core/__init__.py"`.

### P2-5 — `backend/core/` rỗng vs `backend/src/aios_core/` mâu thuẫn
- **Resolution**: ghi rõ: "`backend/core/` theo PLAN chính là package `aios_core`; src layout → code tại `backend/src/aios_core/`; placeholder `.gitkeep` theo cây PLAN giữ nguyên làm định hướng; **quy ước layout M1: toàn bộ code gom vào `backend/src/<package>/`, DI container (TASK-003) thêm vào `backend/src/aios_core/container.py`, không tạo package thứ 2**". Note 1 dòng vào PLAN.md.

### P2-6 — `make_component_metadata()` chưa có AC/test
- **Resolution**: pin signature: `make_component_metadata(*, id: str, name: str, version: str, author: str = "AIOS", license: str = "MIT", dependencies: list[str] = [], permissions: list[str] = [], tags: list[str] = [], created: datetime | None = None)` — `checksum`/`health` luôn `None`. AC16: defaults đúng + `checksum is None` + version invalid → ValidationError (có test).

### P3-1 — Healthcheck edge cases
- **Resolution**: `report()` registry rỗng → `degraded` + message "no checks registered"; `check()` ném exception → bắt → report degraded thay vì crash (ghi vào spec).

### P3-2 — Semver build metadata
- **Resolution**: regex chuẩn semver.org; AC6 thêm case `"1.0.0-beta.1+build.5"` hợp lệ.

### P3-3 — Datetime aware + exports pin + tasks.json venv
- **Resolution**: `created/updated` dùng `datetime.now(timezone.utc)` (aware); pin exports AC3: `get_logger`, `setup_logging`, `AiOSMetadata`, `make_component_metadata`, `HealthStatus`, `HealthReport`, `HealthCheck`, `HealthRegistry`, `__version__`; tasks.json ghi chú giả định venv (lệnh: `.venv/Scripts/python -m pytest` trên Windows).

## Kết luận
- [x] **Đã resolve toàn bộ (1 P1 + 6 P2 + 3 P3)** — spec cập nhật theo resolution trên, đạt sẵn sàng implement.

*(Nội dung phản biện gốc do subagent critic sinh ra; resolution bởi AIOS Orchestrator.)*
