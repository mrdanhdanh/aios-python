# Migration Guide: AIOS 1.0 → 1.1

> Áp dụng cho AIOS 1.1 Compatibility (M12, Issue #7). Chính sách chi tiết: [ADR-0007](../adr/0007-compatibility-migration-policy.md).
> Yêu cầu: AIOS 1.0 (M10) hoặc M11 đã cài. Mọi lệnh chạy từ thư mục `backend/` (hoặc `aiagent` trong PATH).

## Tổng quan

| Bước | Lệnh | Mục đích |
|------|------|----------|
| 1 | `aiagent compat verify` | Kiểm tra tương thích cũ→mới (9/9) |
| 2 | `aiagent migrate <kind> 1.0.0 1.1.0 --dry-run` | Xem trước, không side effect |
| 3 | `aiagent migrate <kind> 1.0.0 1.1.0 --apply` | Nâng cấp dữ liệu từng kind |
| 4 | (nếu cần) rollback | Khôi phục từ backup_id |
| 5 | `aiagent conformance` | Xác nhận **AIOS 1.1 READY** |

---

## Bước 1 — Kiểm tra tương thích

```bash
aiagent compat verify
```

- Chạy 9 check chéo (workflow v0 / plugin v0+v1 / contract v0 / extension / dữ liệu đã migrate).
- **Fail-closed**: chỉ cần 1 check fail → exit 1 → **DỪNG, không nâng cấp**.
- Xem matrix hiện tại: `aiagent compat list` (≥ 14 entry).

## Bước 2 — Dry-run (không side effect)

```bash
aiagent migrate config 1.0.0 1.1.0 --dry-run --journal aios/data/migrations.db
aiagent migrate plugin 1.0.0 1.1.0 --dry-run --journal aios/data/migrations.db
aiagent migrate workflow 1.0.0 1.1.0 --dry-run --journal aios/data/migrations.db
aiagent migrate contract 1.0.0 1.1.0 --dry-run --journal aios/data/migrations.db
```

- Output: `dry_run: true` + steps sẽ chạy + matrix pre-check.
- KHÔNG thay đổi dữ liệu, KHÔNG ghi journal.

## Bước 3 — Apply (nâng cấp thật)

```bash
aiagent migrate config 1.0.0 1.1.0 --apply --journal aios/data/migrations.db
aiagent migrate plugin 1.0.0 1.1.0 --apply --journal aios/data/migrations.db
aiagent migrate workflow 1.0.0 1.1.0 --apply --journal aios/data/migrations.db
aiagent migrate contract 1.0.0 1.1.0 --apply --journal aios/data/migrations.db
```

> ⚠️ **QUAN TRỌNG — dữ liệu thật phải dùng `--input`**:
> Không có `--input`, CLI dùng **dữ liệu mẫu (stub)**: plugin `demo`, workflow `demo_flow`, contract `agent`. Với dữ liệu thật của bạn:
>
> ```bash
> aiagent migrate plugin 1.0.0 1.1.0 --apply --input my-plugin.json --journal aios/data/migrations.db
> ```

Output thành công gồm: `applied: true`, `migration_id`, `backup_id` (ghi lại để rollback), `journal: completed`, `matrix: {pre, post}`.

### Điều gì thay đổi trên dữ liệu

| Kind | Thay đổi |
|------|----------|
| `plugin` | thêm `aios.compatible` (append `"1.1.0"` — giữ phần tử cũ) |
| `workflow` | bump `version` 1.0.0 → 1.1.0 |
| `contract` | bump `version` 1.0.0 → 1.1.0 |
| `config` | thêm marker `migration: {from, to}` (không đổi cấu hình) |

## Bước 4 — Rollback (nếu cần)

- Mỗi migration đã ghi `backup_id` (BackupStore) + journal status (`completed`/`failed`/`rolled_back`).
- Apply lần 2 cùng component → bị chặn (idempotent per component): *"migration đã applied"*.
- Nếu migration fail giữa chừng → **auto-rollback** tự động (journal `rolled_back`, payload khôi phục).
- Rollback thủ công: khôi phục payload từ backup (BackupStore) theo `backup_id`.

## Bước 5 — Xác nhận

```bash
aiagent conformance
```

- Kết quả mong đợi: **11 areas + 20/20 Golden Scenarios + 7 gates (A–G) → `Result: AIOS 1.1 READY`** (exit 0).
- Kiểm tra version: `aiagent system status` → `"version": "1.1.0"`.

---

## Lưu ý

1. **Journal/backup path**: `--journal` đổi → backup db đổi theo (`<journal>` thay `migrations.db` → `backups.db`). Mặc định: `aios/data/migrations.db`.
2. **Config bỏ qua matrix check** (không có version) — vẫn cần dry-run/apply như các kind khác.
3. **Dữ liệu v0 (plugin không có `aios.compatible`)** vẫn hoạt động trên 1.1 — backward compatible (đã verify bởi `aiagent compat verify`).
4. `check_upgrade("0.1.0", "1.1.0")` là breaking — đường hỗ trợ chính thức chỉ từ `1.0.0` (xem ADR-0007 §1).
