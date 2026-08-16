# TASK-081 — Critique vòng 2 (spec)

> **Critic**: AIOS Orchestrator (vòng 2 — sau resolve vòng 1)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved

## P1 — Phải sửa

### C2-01. `AssetSpec.seed` — nếu spec giống hệt nhau nhưng muốn output khác?
→ **Resolve**: spec mang `seed` (bắt buộc default 0); pipeline deterministic theo seed;
worker muốn output khác → đổi seed/params. Không có "random mode" trong P3 (determinism-first).

### C2-02. `match` request string parsing — ai chuẩn hóa (lowercase, strip)?
→ **Resolve**: matcher tự normalize (lower, strip, tách token theo khoảng trắng) — không cần
Normalizer riêng. Ghi rõ trong matcher docstring.

### C2-03. Registry singleton có thread-safe không?
→ **Resolve**: có — dùng `threading.Lock` (mirror VisualMetrics P2). Ghi rõ.

## P2 — Nên sửa

### C2-04. `produce` có cần record metrics (visual metrics P2)?
→ **Resolve**: có — ghi `visual_probe_count` analog: asset_produce_count + asset_failures
(đếm trong registry module, không bắt buộc). Đơn giản: counter trong AssetCapabilityRegistry.

### C2-05. CLI produce — mock pipeline thế nào?
→ **Resolve**: `--kind/--name/--params-json/--seed` + mock pipeline (sinh bytes deterministic
từ seed → sha256). `--list-pipelines` in các pipeline đã đăng ký.

### C2-06. Capability `source` — path tương đối hay tuyệt đối?
→ **Resolve**: tương đối repo (`skills/agent-sprite-forge/`) — di động.

## P3 — Ghi nhận

### C2-07. Matcher có nên đề xuất skill chưa đăng ký (quét skills/)?
→ Resolve: P3 chỉ gợi ý capability ĐÃ đăng ký; quét skills/ tự động → P4/R5 (SkillDistiller).

## Kết luận
Spec v2 sau resolve C2-01..06 → **APPROVED — được phép implement** (đủ 2 vòng critique).
