# Critique vòng 1 — TASK-029 (Harness Kernel, H1)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v1

## Đánh giá chung
Spec khá tốt (đối chiếu PLAN §M6-2/7/9 đầy đủ, D1–D8 mở tường minh). Đã kiểm chứng: PrivateAttr OK (pydantic v2.10), D4 không phá PLAN, D1 không vi phạm INV-006, wiring khả thi. 3 P1 + 5 P2 + 7 P3.

## P1 — Blockers
- **C1-01**: run_id chứa `:` → storage_path `harness/harness:xxx/` → OSError WinError 123 trên Windows (môi trường hiện tại) — mọi run mặc định fail khi lưu evidence.
  → **Resolution**: `storage_path = f"harness/{run_id.replace(':', '_')}/events.json"` + test run mặc định tạo được file.
- **C1-02**: `complete()` hook raise → transition(COMPLETED, FAILED) không có → HarnessLifecycleError thoát giữa chừng, mất evidence.
  → **Resolution (a)**: thêm `COMPLETED: {FAILED}` vào TRANSITIONS — nhất quán "mọi hook fail → FAILED → DIAGNOSED".
- **C1-03**: Evidence không nằm trong finally — on_failure/diagnose raise phá INV-018.
  → **Resolution**: `execute()` = `try: <lifecycle> finally: <build evidence + report + persist>`; bọc on_failure/diagnose trong try/except (log warning, tiếp tục). Test: on_failure raise → vẫn trả report đủ 2 artifact, status FAILED.

## P2 — Major
- **C2-01**: ArtifactContract thiếu 7 field bắt buộc (id/name/version semver/author/license/contract_version/schema_version) — không constructible.
  → **Resolution**: pin giá trị: `id=f"harness:{run_id}:{kind}"`, `name=f"harness-{kind}"`, `version="1.0.0"`, `author="aios-core"`, `license="proprietary"`, `contract_version="1.0.0"`, `schema_version="1.0.0"` — helper `_evidence_contract(run_id, kind)`.
- **C2-02**: HarnessArtifact.id = uuid4 → AC10 determinism fail.
  → **Resolution (a)**: artifact id deterministic `f"{run_id}:{kind}"`.
- **C2-03**: Duplicate run_id — risk hứa nhưng không YC/AC/test.
  → **Resolution**: `_executed: set[str]` + RLock; execute raise HarnessError nếu run_id đã chạy; test.
- **C2-04**: `test_inv017_harness_no_god_object` substring tự phá (comment "runner tự sinh" trong contracts.py).
  → **Resolution (a)**: dùng import-based (`dir_imports`), contracts.py leaf = không import package khác.
- **C2-05**: external_sink raise → phá lifecycle.
  → **Resolution**: emit_event bọc try/except (log warning, tiếp tục); test sink raise → run vẫn COMPLETED.

## P3 — Minor
- **C3-01**: Dẫn chứng _resolve_relative 2-dots không khớp (harness 2-level resolve đúng) → sửa lý do: "tránh phụ thuộc resolver (đã từng sai) + đồng nhất convention".
- **C3-02**: Double prefix `harness:harness:{uuid}` → chọn (b): run_id giữ prefix `harness:` + state key = run_id trực tiếp.
- **C3-03**: duration_ms gồm thời gian chờ — document semantics (started_at = tạo ctx) + pin UTC.
- **C3-04**: `@property @abstractmethod` cho id/name/version; ghi chú version policy (cùng id khác version → error v1).
- **C3-05**: Bỏ entry `aios_core.kernel.events` v1 (chưa dùng — diện tích cho phép > dùng).
- **C3-06**: Collector sink runner-owned (attach đầu execute) — evidence không phụ thuộc ai tạo ctx.
- **C3-07**: INV-017 test viết rglob loop ngay từ v1 (phủ subdir H2–H5 tương lai).

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C1-01..C1-03 (P1) + C2-01..C2-05 (P2) + P3 → spec v2, rồi critique vòng 2.
