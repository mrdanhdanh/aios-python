# TASK-064 — Evaluation (Contract 1.0)

## Đối chiếu AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | Đủ 10 contract | ✅ |
| AC2 | Đủ 7 trường + schema_ref import được thật | ✅ |
| AC3 | Semantic versioning (patch/minor compatible, major breaking) | ✅ |
| AC4 | Lifecycle validation fail-closed (DEPRECATED bắt buộc migration) | ✅ |
| AC5 | Matrix ✓/⚠/✗ + breaking/warning count + blocking | ✅ |
| AC6 | Deprecated API detector | ✅ |
| AC7 | CLI contract-check (matrix + exit code) | ✅ |
| AC8 | CLI contract list (10 contract) | ✅ |
| AC9 | Không breaking M1–M9 (1815 pass) | ✅ |
| AC10 | DoD | ✅ |

**ĐẠT 10/10 AC — TASK-064 DONE.**

## Giá trị
- **Contract 1.0** = nền tảng cho Certification Suite (TASK-073 Gate C) + Migration 1.0 (TASK-074) + contract-check CLI.
- Plugin v1 DEPRECATED với migration path rõ — ví dụ chuẩn cho vòng đời contract.

## Bài học
1. **Pydantic field-validator không dùng được cho cross-field validation** (thứ tự field) → `model_validator(mode="after")` — lỗi thực tế đã gặp.
2. **Console cp1252 (Windows) không in được ✓/⚠** → `sys.stdout.reconfigure(encoding="utf-8")` trong CLI main; test dùng capsys không phát hiện (pytest chạy utf-8) — cần chạy CLI thật để bắt.
3. `warning_count` nên tính cả matrix + usage warnings (đồng nhất với output "Warnings: N").
