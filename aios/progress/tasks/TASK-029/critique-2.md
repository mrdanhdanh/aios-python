# Critique vòng 2 — TASK-029 (Harness Kernel, H1)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
C1-01 ⚠️ (spec mâu thuẫn — YC-6 step 5 chưa replace) · C1-02 ✅ · C1-03 ⚠️ (bọc on_failure/diagnose + test thiếu) · C2-01 ✅ (9 field pin đủ) · C2-02 ⚠️ (ref checksum chứa timestamp → determinism fail — B2) · C2-03 ⚠️ (behavior có, test thiếu) · C2-04 ❌ (substring vẫn tự phá) · C2-05 ❌ (chưa wrap) · C3-01 ❌ (lý do sai) · C3-02 ⚠️ (5 chỗ double-prefix) · C3-03 ❌ · C3-04 ⚠️ (thiếu test TypeError) · C3-05 ✅ · C3-06 ❌ (attach tại create_context) · C3-07 ⚠️ (no_kernel_impl không đệ quy)

## Mục B — Vấn đề mới
- **B1 (P2)**: Exception NGOÀI hook → result.status non-terminal (VALIDATING) + exception trong finally → mất report.
  → **Resolution**: catch-all `except Exception` → run FAILED (transition từ phase hiện tại; thêm `CREATED: {FAILED}`) + run.error; lỗi trong finally (store fail) → log warning + trả report in-memory (path/ref None); execute chỉ raise 3 lỗi documented.
- **B2 (P2)**: `ref` = checksum events.json (chứa timestamp) → AC10 fail.
  → **Resolution**: thêm `artifacts[].ref` vào danh sách loại trừ determinism.
- **B3 (P2)**: get_evidence sau restart — StateService in-memory mất.
  → **Resolution (b)**: fallback `get_evidence` → `ArtifactService.list(JSON)` lọc `metadata.run_id` → reconstruct HarnessArtifact từ sidecar.
- **B4 (P2)**: Sanitize `[\\/:*?"<>|]` → `_` (regex) thay vì chỉ `:`; test run_id `harness:a?b`.
- **B5 (P3)**: Pin `result.artifacts = [harness_artifact.id]` = `f"{run_id}:{kind}"` + test.
- **B6 (P3)**: `ended_at` set ở CẢ 2 nhánh (success + failure).
- **B7 (P3)**: external allow-list dùng top-level (`collections` không phải `collections.abc`).
- **B8 (P3)**: get_evidence run_id không tồn tại → `[]` + test.
- **B9 (P3)**: persist `model_dump(mode="json")` dicts; get_run/get_result parse `model_validate`.
- **B10 (P3)**: Va chạm path sau replace — chấp nhận + note (uuid4().hex không có `_`).
- **B11 (P3)**: events/report encode UTF-8 — test đọc lại parse + checksum khớp.

## Kết luận
- [x] **Cần sửa trước khi implement**: 10 điểm (1-10) + P3 → spec v3. Sau vòng này **approve** (không cần vòng 3 — thiết kế lõi đã kiểm chứng khả thi).
