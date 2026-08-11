# TASK-004 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Context service | `backend/src/aios_core/kernel/services/context.py` |
| Event service (audit SQLite) | `backend/src/aios_core/kernel/services/events.py` |
| Artifact service (sidecar) | `backend/src/aios_core/kernel/services/artifacts.py` |
| Permission service | `backend/src/aios_core/kernel/services/permissions.py` |
| Policy service | `backend/src/aios_core/kernel/services/policy.py` |
| Config mở rộng | `config.py` (audit/artifacts), `config.yaml` |
| Tests (5 file mới) | `backend/tests/test_context.py`, `test_events.py`, `test_artifacts.py`, `test_permissions.py`, `test_policy.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- **Context**: frozen + `_created_mono` qua service clock (mọi fake clock hoạt động); `ttl_s=None` → vĩnh viễn; get_all → dict
- **EventService**: audit trước, publish sau; connection-per-call + busy_timeout; id = event.id (correlation); insert lỗi → warning, không crash
- **ArtifactService**: sidecar `.aios.json` (persist metadata); luôn tự tính checksum + refresh updated; path guard `is_relative_to` (store+load+delete); list skip corrupt sidecar
- **PermissionService**: pending CHỈ cho ASK; grant/deny id lạ → no-op; on_ask raise → fallback ASK; payload có service + request_id
- **PolicyService**: precedence deny > approval > allow; default-deny (scope không trong allow → ASK); max_concurrent/sandbox_required chở giá trị cho TASK-005
