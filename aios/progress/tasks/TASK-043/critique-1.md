# TASK-043 — Critique v1

## Phản biện
- **P1-01 Import boundary**: SDK phải chạy độc lập; không import backend hoặc dùng path hack.
- **P1-02 Tool safety**: SDK không được tự thực thi side effect; Tool.run là developer hook, Client mới gọi transport.
- **P2-01 Contract drift**: DTO cần version cố định, extra fields bị từ chối và serialization deterministic.
- **P2-02 DAG**: Workflow phải phát hiện duplicate node, edge tới node thiếu và cycle.
- **P2-03 Capability metadata**: capability/permission cần immutable hoặc copy an toàn để tránh mutate ngoài ý muốn.
- **P3-01 Client errors**: transport lỗi phải giữ nguyên exception hoặc bọc lỗi SDK có nguyên nhân.

## Resolution
- ✅ Dùng package SDK độc lập, không import `aios_core`.
- ✅ Client chỉ gọi Protocol transport; không chứa runtime implementation.
- ✅ DTO frozen/extra-forbid, schema version `1.0`, JSON-compatible dump.
- ✅ Workflow validate deterministic DAG.
- ✅ Metadata chuẩn hóa tuple và validate id/version.
- ✅ Client truyền exception transport, chỉ reject response sai shape qua SDKError.
