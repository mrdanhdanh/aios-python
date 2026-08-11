# Test — TASK-002

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Lệnh chạy 1 (từ backend/) | `.venv/Scripts/python -m pytest` → **32 passed** |
| Lệnh chạy 2 (từ repo root) | `backend/.venv/Scripts/python -m pytest backend/tests` → **32 passed** |
| Coverage | **96.14%** trên `aios_core` (ngưỡng 80% — pass) |
| Môi trường | Python 3.13.14, pytest 9.1.1, pytest-cov 7.1.0, pydantic 2.13.4 |

Phân bổ test:
- `test_config.py` — 10 tests (defaults, CWD config, thiếu key, env nested, env typo → ValueError, env sai type → ValidationError, AIOS_CONFIG_PATH 3 case, YAML extra key)
- `test_healthcheck.py` — 7 tests (rỗng → degraded, worst-wins ×2, trùng name, broken check, get_all, timestamp khác nhau)
- `test_import.py` — 2 tests (semver version, đủ exports pin)
- `test_logging.py` — 5 tests (JSON + correlation_id, idempotent, mkdir, get_logger, omit field khi không có cid)
- `test_metadata.py` — 8 tests (semver valid ×5/invalid ×6, updated>=created, timestamps aware, defaults, make_component_metadata ×3)

## Đối chiếu AC

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 pip install -e ".[dev]" | ✅ | aios-core 0.1.0 cài thành công vào backend/.venv |
| AC2 pytest pass + coverage ≥80%, chạy từ backend/ và root | ✅ | 32 passed ×2 nơi, 96.14% |
| AC3 test_import + exports pin | ✅ | test_import.py 2/2 pass |
| AC4 env nested + typo → ValueError + sai type | ✅ | test_config.py |
| AC5 thiếu file / thiếu key → default | ✅ | test_config.py |
| AC6 semver 4 case | ✅ | test_metadata.py |
| AC7 healthcheck 6 case | ✅ | test_healthcheck.py 7 tests |
| AC8 sdk READMEs | ✅ | sdk/python/README.md + sdk/typescript/README.md (commit 7a270ff) |
| AC9 settings + tasks.json track, không đường dẫn máy | ✅ | commit 486fb9f; settings dùng `${workspaceFolder}` |
| AC10 docs/README 2 lệnh | ✅ | docs/README.md |
| AC11 cây monorepo + .gitkeep | ✅ | 25 thư mục .gitkeep (commit 7a270ff) |
| AC12 correlation_id + idempotent + mkdir | ✅ | test_logging.py |
| AC13 AIOS_CONFIG_PATH thắng | ✅ | test_config.py |
| AC14 path không tồn tại → fallback | ✅ | test_config.py |
| AC15 YAML extra key → ValidationError | ✅ | test_config.py |
| AC16 make_component_metadata defaults + invalid | ✅ | test_metadata.py |

## Kết luận
- [x] **TẤT CẢ PASS (16/16 AC)** — task sẵn sàng đánh giá cuối.
