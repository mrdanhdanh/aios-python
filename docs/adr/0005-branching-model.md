# ADR-0005: Branching Model — feature → verify → master

- **Status**: accepted
- **Date**: 2026-08-15

## Context

Dự án có nhánh `verify` được tạo để kiểm thử (operation test). Người dùng yêu cầu:
"từ nay, mọi nhánh chức năng đều phải đi từ nhánh verify; verify kiểm tra thay đổi
sau đó mới update về master". Trước đây mọi thay đổi commit trực tiếp lên `master`,
không có trạm kiểm tra trung gian — rủi ro đưa thay đổi chưa kiểm chứng vào nhánh ổn định.

## Decision

Branching model bắt buộc:

```
master (ổn định, chỉ nhận từ verify)
   ▲
   │ merge (chỉ khi verify PASS: test + hard gate + review)
   │
verify (trạm kiểm tra bắt buộc)
   ▲
   │ merge
   │
nhánh chức năng (feature/, fix/, docs/, operation/, refactor/, test/...) — tạo TỪ verify
```

1. **`master`** — nhánh ổn định duy nhất. KHÔNG commit trực tiếp, KHÔNG nhận merge
   trực tiếp từ nhánh chức năng. Chỉ nhận từ `verify`.
2. **`verify`** — trạm kiểm tra. Mọi thay đổi phải đi qua đây trước khi về `master`.
   Trên `verify` chạy: full test suite, đối chiếu hard gate (spec + critique ×2 +
   review + test + evaluate), review thay đổi. Chỉ khi PASS mới merge `verify` → `master`.
3. **Nhánh chức năng** — tạo TỪ `verify` (KHÔNG từ `master`). Tên có tiền tố loại:
   `feature/`, `fix/`, `docs/`, `operation/`, `refactor/`, `test/`, ...
   Sau khi hoàn thành → merge vào `verify`.

## Consequences

- Positive: `master` luôn ổn định; thay đổi được kiểm chứng ít nhất 1 lần trên `verify`
  trước khi phát hành; quy trình dễ đào tạo agent (deterministic, offline-first).
- Negative: thêm 1 bước merge trung gian; `verify` cần được giữ gần `master`
  (rebase/merge thường xuyên để tránh drift).
- Operations (chạy thử nghiệm, bypass nhỏ ghi LOG.md) vẫn theo quy tắc cũ nhưng
  commit phải nằm trên nhánh đi qua `verify`, không commit thẳng `master`.
