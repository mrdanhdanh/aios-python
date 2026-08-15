# TASK-035 — Evaluation

**Đạt**: 8/8 AC. INV-022 enforced (identity first). RBAC/ABAC deterministic, offline-first, fail-closed. Delegation + attenuation hoạt động.

**Bài học**: identity phải là hard entry-point của mọi execution — đặt tại `EnterpriseManager` facade. ABAC resource dict cần key `type` chuẩn hóa.

**Đề xuất cải tiến**: tích hợp với M4 PolicyService để `authorize` query policy thực tế thay vì chỉ RBAC/ABAC local.
