# Review — TASK-030 (Execution Verification) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-15

## Kết luận
- [x] **APPROVED có điều kiện** — 0 R1; 2 R2 (bắt buộc) + 7 R3.

## Kiểm chứng trọng tâm (đối chiếu code thật)
- (a) update_state merge shallow — verification key sống sót qua H1 _persist ✓
- (b) verdict.json convention khớp _evidence_contract H1; get_evidence fallback tìm thấy ✓
- (c) query_audit(limit, event_type); payload có execution_id (execution.py 124-247); Event là dataclass → cần to_dict() (R3-2) ✓
- (d) **R2-1**: _HARNESS_ALLOWED_EXTERNAL thiếu pathlib → FILE_EXISTS/CONTAINS fail allow-list
- (e) replay tamper: dict-level (disk tamper vướng checksum ArtifactCorruptedError — R3-4)
- Graph/plan namespaces verified: graph không emit event; plan có WORKFLOW_STARTED ✓

## Vấn đề
### R2 (major)
- **R2-1**: Thêm `pathlib` vào `_HARNESS_ALLOWED_EXTERNAL` (MOD external — AIOS list KHÔNG MOD).
- **R2-2**: Wiring services phải là **object** (SimpleNamespace: state/events/artifacts) — không phải dict literal (EventService không có __call__).

### R3 (minor)
- **R3-1**: Chốt execution_ref resolution P3-08 (3 bước).
- **R3-2**: Event serialization qua `to_dict()` (dataclass — không model_dump).
- **R3-3**: Truncation heuristic — filtered_count==limit; note cửa sổ 10k.
- **R3-4**: Tamper test ở mức dict (không disk — checksum).
- **R3-5**: AC5 PASS test dùng FILE_EXISTS/CONTAINS (TEST_RUN/COVERAGE runner None → INCONCLUSIVE).
- **R3-6**: compute_verdict thêm param `truncated: bool = False`.
- **R3-7**: metrics deterministic (per-check counts) — loại trừ timing.

## Resolution ghi nhận (phản ánh trong implement)
- R2-1/R2-2 + R3-1..07 → implement + tests
