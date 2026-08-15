# TASK-043 — Public AIOS SDK (M8-E1)

## Mục tiêu
Cung cấp Python SDK công khai, contract-first, độc lập backend, để developer viết `Agent`, `Tool`, `Capability`, `Workflow` và gọi AIOS qua client injectable.

## Phạm vi
- SDK Python v1 tại `sdk/python/src/aios/`.
- Public DTO/model: agent request/response, tool input/output, chat message/response.
- Public base classes: `Agent`, `Tool`, `Capability`, `Workflow`.
- `Client` với transport Protocol injectable, chỉ facade operations; không import `aios_core`.
- README quickstart và package metadata.
- Không làm plugin loader, ecosystem registry, marketplace, CLI scaffold, signing hoặc backend refactor.

## Input/Output
- Input: public DTO và developer implementations.
- Output: validated DTO, declarative workflow payload, client transport calls.
- Serialization dùng JSON-compatible dict; schema version `1.0`.

## Tiêu chí chấp nhận
1. SDK cài độc lập và `from aios import Agent, Tool, Capability, Workflow, Client` hoạt động.
2. SDK source không import `aios_core` hoặc backend internal modules.
3. Agent/Tool/Capability/Workflow có metadata và validation deterministic.
4. Tool bắt buộc khai báo capability; permissions được giữ trong metadata.
5. Workflow declarative, validate node/edge DAG, không phụ thuộc engine.
6. Client dùng transport injection, hỗ trợ `run_agent`, `run_workflow`, `call_tool`, `get_capabilities`.
7. DTO reject unknown fields và round-trip serialization ổn định.
8. Tests độc lập offline bao phủ import boundary, validation, serialization, client mock và DAG.
9. README có quickstart chạy được.
10. Backend regression không bị ảnh hưởng.
