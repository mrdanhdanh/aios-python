# TASK-047 — Critique v1 + v2

## Critique v1
- **P1-01 No-overwrite**: tồn tại file → `EcosystemError` (tránh ghi đè mất code).
- **P1-02 Name sanitize**: name phải identifier hợp lệ (regex `[a-z][a-z0-9_]*`).
- **P2-01 Deterministic**: không timestamp/random trong scaffold output.
- **P2-02 Manifest**: `aios: {min: 1.0.0, max: 2.x}` theo PluginManifest convention.
## Resolution v1
- ✅ no-overwrite; ✅ regex; ✅ deterministic; ✅ aios range chuẩn.

## Critique v2
- **P1-01 Stub phải compile** được (python compile() trong test).
- **P1-02 Kind map**: agent → `Agent` stub, tool → `Tool` stub (SDK classes) — không hard-code import aios_core.
- **P2-01 README** mô tả quickstart ngắn.
- **P2-02 Tests stub** trống hợp lệ (pytest pass).
## Resolution v2
- ✅ compile check trong test; ✅ stub theo SDK public API; ✅ README; ✅ test stub đơn giản.
