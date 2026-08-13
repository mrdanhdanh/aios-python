# Critique ×2 — TASK-019 (self-review qua implement + review nhanh)

> 2026-08-13 | critic self: spec đơn giản, 6 AC khả thi. Vấn đề dự kiến:
> - C1: vscode namespace không tồn tại ngoài extension host → mọi module import vscode phải lazy/test-stub
> - C2: fetch trong Node 22 extension host — dùng global fetch (có sẵn Node 18+)
> - C3: command IDs phải khớp contributes.commands
> **Resolve**: extension.ts lazy-import vscode qua tham số; client.ts dùng global fetch; test stub vscode. Đã áp dụng vào code — verify bằng vitest + tsc.

**Trạng thái: RESOLVED 3/3.**
