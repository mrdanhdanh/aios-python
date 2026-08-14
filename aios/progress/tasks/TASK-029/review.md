# Review — TASK-029 (Harness Kernel) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-15

## Kết luận
- [x] **CHANGES REQUESTED** — R1-1 (YC-6 step 5 stale — 3 defect) + R2-1/R2-2 + R3-1..05.

## Vấn đề
### R1 (blocking)
- **R1-1**: YC-6 step 5 còn block stale v1: (1) `storage_path=f"harness/{run_id}/..."` dùng run_id THÔ (không sanitize — mâu thuẫn §4/B4 → WinError 123); (2) `HarnessArtifact(id=uuid)` mâu thuẫn YC-1 C2-02 deterministic → AC10 fail; (3) `ArtifactContract(...)` thiếu 9 field bắt buộc → ValidationError — helper `_evidence_contract(run_id, kind)` + 9 giá trị pin chưa vào spec.
  → **Resolution**: sửa YC-6 step 5: `safe_run_id` trong storage_path; `id=f"{run_id}:{kind}"`; `_evidence_contract` 9 field (`id=f"harness:{run_id}:{kind}"`, name `harness-{kind}`, version/contract_version/schema_version "1.0.0", author "aios-core", license "proprietary").
### R2 (major)
- **R2-1**: no_god_object substring tự phá (comment "runner tự sinh" trong YC-1) → **Resolution**: import-based qua collect_imports (contracts leaf).
- **R2-2**: external `collections.abc` → scanner trả top-level `collections` → **Resolution**: sửa §6.1 thành `collections` (top-level).
### R3 (minor)
- **R3-1**: no_kernel_impl dùng rglob (H2–H5 subdir).
- **R3-2**: lý do import tuyệt đối sửa (bug chỉ ở subdir 4 cấp).
- **R3-3**: result dựng trong finally (từ run.status + phase_count).
- **R3-4**: get_evidence fallback sort theo (run_id, kind).
- **R3-5**: sanitize chặn segment rỗng/`..`.

## Resolution ghi nhận (phản ánh trong spec v4 + implement)
- R1-1, R2-1, R2-2 → spec v4 + tasks.md T6/T9
- R3-1..05 → spec + implement
