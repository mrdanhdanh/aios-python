# Review — TASK-025 (Model Router) — spec v3 trước implement

**Reviewer**: AIOS Orchestrator (subagent reviewer không phản hồi 2 lần — review thực hiện bởi orchestrator với đối chiếu code thật) | **Ngày**: 2026-08-14

## Kết luận
- [x] **APPROVED có điều kiện** — 0 R1; 1 R2 (threading thiếu trong allow-list external) + 4 R3 (resolve trong implement).

## Kiểm chứng trọng tâm (đối chiếu code thật)
- (a) `register()` duck-typed `model.capability()`: MockModel KHÔNG có method capability (mock.py chỉ có name/is_available/metadata/_chat/calls) → default path `ModelCapability.default` ✓ — không phá; provider future-proof
- (b) `chat()` loop fallback: model fail → record_failure (COOLDOWN) → `fallback.next(all_candidates, rule, excluded)` — candidates raw từ registry chứa model failed (excluded) + COOLDOWN (can_use False) → next loại cả 2 ✓ không mâu thuẫn
- (c) `RouteDecision.health_snapshot: dict[str, HealthStatus]` — pydantic Enum value OK
- (d) Allow-list router/ external {pydantic, typing, datetime, enum, abc, dataclasses} — **thiếu `threading`** (ModelHealth dùng RLock pattern registry) → R2-1
- (e) config.yaml thêm models.routing: `_yaml_extra_keys_guard` chỉ top-level; ModelsSettings extra="forbid" (C2-04 v1) parse block models — field `routing` + `default` hợp lệ → không break test_config/workflow cli ✓
- (f) wiring register_instance(ModelRouter) → Container.resolve ✓ (pattern có sẵn)
- `MockModel.calls` tồn tại (mock.py:32) → test "select không gọi chat (calls==0)" khả thi ✓
- test_models.py registry tests (register 2 tham số) — backward compatible ✓

## Vấn đề
### R1 — Không có

### R2 — Major
- **R2-1**: Allow-list external `models/router/` thiếu `threading` — `ModelHealth` dùng `_lock = threading.RLock()` (pattern ModelRegistry) + `last_decision` lock trong router. → Resolution: thêm `"threading"` vào §5.2 external allowed + test allow-list.

### R3 — Minor
- **R3-1**: `models/__init__.py` re-export ModelRouter → runtime_kernel import `from ..models import ...` kéo router + 6 module — chấp nhận (composition root), ghi chú thứ tự import base→errors→capability→registry→router đã có (C3-04 v1).
- **R3-2**: `RouteRequest.policy` sai tên → RouterError — test thêm case policy name rỗng string `""` (treat như None → default).
- **R3-3**: `ModelSelector` rank `local` — spec nói "provider filter xong, rank balanced desc" — thực tế providers filter đã loại hết ngoài providers → rank luôn 1 candidate nếu chỉ 1 ollama; với nhiều ollama → balanced desc + tie-break name — deterministic ✓ ghi chú test.
- **R3-4**: `chat()` với `max_attempts=1` → chỉ thử model đầu — test đã có ✓.

## Resolution ghi nhận (phản ánh trong implement)
- R2-1 → spec v3 §5.2 external allowed thêm `threading`
- R3-2 → test policy="" → default
- R3-3 → test local với 2 ollama models
