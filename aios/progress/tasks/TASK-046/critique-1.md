# TASK-046 — Critique v1 + v2

## Critique v1
- **P1-01 Search deterministic**: sort theo (kind, id) luôn.
- **P1-02 Signature field**: lưu signature string + signing_key id trong publisher; không verify ở registry (verify ở marketplace).
- **P2-01 Persist**: SQLite, JSON serialize entry; rebuild không cần scan registry cũ.
- **P2-02 Remove kind**: remove_entry(kind, id) phân biệt với update.
- **P3-01 Count**: `count()` cho doctor/health.
## Resolution v1
- ✅ sort (kind,id); ✅ signature metadata-only; ✅ SQLite JSON; ✅ remove riêng; ✅ count.

## Critique v2
- **P1-01 Không God Object**: registry chỉ index/search; không nhúng logic certification/marketplace.
- **P1-02 Extra=forbid** trên entry; version bắt buộc semver.
- **P2-01 Search case-insensitive**; keyword rỗng → danh sách toàn bộ (giới hạn).
- **P2-02 Namespace filter** tái dùng `extension.ApiNamespace`? — KHÔNG import extension (giữ allow-list ecosystem độc lập) → filter bằng string.
## Resolution v2
- ✅ registry thuần index/search; ✅ semver validate + forbid; ✅ lower-case search; ✅ kind filter string.
