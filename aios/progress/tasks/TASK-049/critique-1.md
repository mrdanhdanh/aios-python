# TASK-049 — Critique v1 + v2

## Critique v1
- **P1-01 Evidence**: mỗi check phải có evidence string (INV-018 spirit — dù M8 không thêm invariant, giữ chuẩn Harness).
- **P1-02 Threshold**: CERTIFIED cần threshold; nếu threshold > 1.0 → clamp/error.
- **P2-01 Security fail** luôn chặn CERTIFIED+.
- **P2-02 Checks rỗng** → không thể VERIFIED (cần ≥ 1 check).
## Resolution v1
- ✅ evidence bắt buộc; ✅ threshold validate 0..1; ✅ security fail hard block; ✅ ≥1 check.

## Critique v2
- **P1-01 Không God Object**: CertificationEngine chỉ orchestrates; check registry injectable.
- **P1-02 Deterministic**: sort checks theo tên, cùng input → cùng report.
- **P2-01 Manifest validate**: manifest dict phải có id/version hợp lệ → nếu không, báo check fail cụ thể.
- **P2-02 Report** có passed/failed counts + level.
## Resolution v2
- ✅ engine thuần orchestrate; ✅ sort + deterministic; ✅ validate manifest trong check; ✅ counts + level.
