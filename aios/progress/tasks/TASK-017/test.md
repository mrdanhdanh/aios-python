# Test — TASK-017 (M3-P5: Backend API server)

> Ngày chạy: 2026-08-13 | Môi trường: backend/.venv, Windows PowerShell

## Lệnh chạy

```powershell
cd backend; .venv/Scripts/python -m pytest tests/test_api.py tests/test_api_chat_serve.py -q
```

## Kết quả

```
689 passed, 0 skipped  (baseline 669 + 20 mới: test_api.py 14 + test_api_chat_serve.py 6)
coverage: 95.10%  (api/ ≥ 80% ✓)
```

## Chi tiết AC test (12/12)

| AC | Test | Kết quả |
|----|------|---------|
| AC1 | `test_api.py::test_openapi` | ✅ /openapi.json 200 |
| AC2 | `test_health_*` | ✅ components + score |
| AC3 | `test_events_*` | ✅ audit + filter |
| AC4 | `test_ws_events_realtime` | ✅ cross-thread publish → receive |
| AC5 | `test_catalog_*` | ✅ list + search |
| AC6 | `test_goals_*` | ✅ list + detail |
| AC7 | `test_skills_*` | ✅ list + detail |
| AC8 | `test_tools_*` | ✅ list + detail (6 tools) |
| AC9 | `test_artifacts_and_conversations` | ✅ |
| AC10 | `test_prompts_models` | ✅ |
| AC11 | `test_chat_coding_intent` / `test_chat_extra_field_forbidden` | ✅ intent coding + 422 |
| AC12 | `test_cli_serve_parser` / `test_serve_run_importable` | ✅ |

## Ghi chú

- Full backend suite tại thời điểm M3 = 689 pass (commit `16c998f`).
- WS test không block publish thread (queue + `call_soon_threadsafe`).
