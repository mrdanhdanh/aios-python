# TASK-014 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Tool base (template `run` 1-6, fail-closed gate) | `backend/src/aios_core/tools/base.py` |
| Python tool (`ast.parse` no-exec) | `backend/src/aios_core/tools/python_tool.py` |
| Docker tool (mock) | `backend/src/aios_core/tools/docker_tool.py` |
| REST tool (validate) | `backend/src/aios_core/tools/rest_tool.py` |
| MCP tool (registry stub) | `backend/src/aios_core/tools/mcp_tool.py` |
| Shell tool (no-exec, `shell` scope bắt buộc) | `backend/src/aios_core/tools/shell_tool.py` |
| Git tool (mock) | `backend/src/aios_core/tools/git_tool.py` |
| Tool Registry (`bind_capabilities`) | `backend/src/aios_core/tools/registry.py` |
| Tests | `test_tools_base.py`, `test_tool_stubs.py`, `test_tool_registry.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- Allow-list cứng: `tools/` KHÔNG import kernel/capabilities/agents/orchestrator.
- Mọi runtime interaction qua `ToolContext` injectable (`permission_gate`, `event_sink`).
- Capability-first: Agent gọi Capability, Tool chỉ được chọn bởi Capability Router
  (Agent không import Tool trực tiếp — INV-002).
