# TASK-048 — Critique v2 (đầy đủ)

## Phản biện độc lập vòng 2
- **P1-01**: sign phải bọc toàn bộ manifest JSON canonical (json.dumps sort_keys, ensure_ascii).
- **P1-02**: Publisher.signing_key không bao giờ serialize ra record (chỉ lưu key id/hash).
- **P2-01**: TrustChain nhận `aios_version` + `entry_resolver` injectable; default resolver trả None → dependency fail.
- **P2-02**: `install_flow` trả về InstallResult kể cả fail (step + reason), không raise ngoài marketplace error khi policy cho phép warning.
- **P3-01**: CLI `aiagent marketplace publish/install` tối thiểu (publish đủ để test trust chain).
## Resolution v2
- ✅ canonical JSON; ✅ key không serialize; ✅ injectable; ✅ InstallResult luôn trả; ✅ CLI tối thiểu.
