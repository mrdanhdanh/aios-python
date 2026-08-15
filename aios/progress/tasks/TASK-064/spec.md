# TASK-064 — M10-F2: Contract 1.0 (Public Contract Freeze)

## Mục tiêu

PLAN §M10-6..9: freeze 10 public contracts thành **Contract 1.0** — mỗi contract có `name · version · schema · compatibility · lifecycle · deprecation · migration`; semantic versioning thật; `aiagent contract-check` in Contract Compatibility Matrix; deprecated API detector. Task **quan trọng nhất M10** — nền tảng cho Certification (TASK-073) và Migration (TASK-074).

## Bối cảnh / Lý do

M1 đã xây contract versioning (semver + CompatibilityChecker + AiOSMetadata) nhưng chưa có **catalog chính thức** liệt kê 10 contract công khai với trạng thái lifecycle + deprecation + migration path. M10 freeze để sau 1.0 chỉ cho phép backward-compatible thay đổi.

## Phạm vi

- `contracts/catalog.py`: `ContractLifecycle` (STABLE/FROZEN/DEPRECATED/REMOVED) + `ContractDefinition` (name, version, schema_ref, lifecycle, deprecated_in, migration_path, notes, extra=forbid) + `ContractCatalog` (registry 10 contract: Agent, Capability, Tool, Workflow, Runtime, Event, Artifact, Plugin, Model, Memory)
- `contracts/check.py`: `ContractChecker` — per-contract: compatibility (tái dùng CompatibilityChecker), deprecation detector (dùng API deprecated → warning), migration path check (DEPRECATED bắt buộc có migration_path); output `ContractMatrixReport` (per-contract ✓/⚠/✗ + breaking_count + warning_count)
- CLI: `aiagent contract-check` (matrix) + `aiagent contract list`
- Tests + wiring không bắt buộc (catalog là data-driven, không cần DI)

## Ngoài phạm vi

- KHÔNG đổi contract hiện có (freeze — không breaking change)
- Không renumber/đổi schema các contract M1–M9

## Input (nguồn sự thật)

- `contracts/compatibility.py` (CompatibilityChecker — tái dùng)
- `contracts/base.py` + `contracts/artifact.py` (ArtifactContract)
- `models/base.py` (ModelContract), `workflow/definition.py` (WorkflowDefinition/Contract), `tools/base.py` (ToolContract), `capabilities/registry.py`, `agents/base.py` (AgentContract), `memory/contracts.py`, `plugins/contracts.py` (PluginManifest + aios range), `kernel/events.py` (EventType)

## Output

- `backend/src/aios_core/contracts/catalog.py` + `contracts/check.py`
- CLI subcommand `contract-check`/`contract list` trong `workflow/cli.py`
- `tests/test_contracts_catalog.py`

## Tiêu chí chấp nhận (AC)

| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | `ContractCatalog` chứa ĐỦ 10 contract (agent, capability, tool, workflow, runtime, event, artifact, plugin, model, memory) — id chuẩn hóa | Unit test đếm + set compare |
| AC2 | Mỗi contract có đủ 7 trường: name, version, schema_ref (module:class thật), compatibility, lifecycle, deprecation, migration | ContractDefinition `extra=forbid` + test fixture |
| AC3 | Version semantic: patch/minor/major phân loại đúng (compatibility check: patch/minor bump = compatible, major = breaking) | Test dùng CompatibilityChecker trên version mẫu |
| AC4 | Lifecycle hợp lệ: Plugin = DEPRECATED (v1) kèm migration_path; Runtime/Event/Artifact/Model = STABLE hoặc FROZEN; DEPRECATED bắt buộc có migration_path + deprecated_in (validation) | Test validation fail-closed |
| AC5 | `ContractChecker.check_all()` trả matrix: mỗi contract ✓/⚠/✗ + `breaking_count` + `warning_count`; warning cho contract DEPRECATED; breaking cho version conflict | Unit test các kịch bản |
| AC6 | Deprecated API detector: checker phát hiện usage deprecated (vd schema_ref trỏ deprecated contract) → warning | Test |
| AC7 | CLI `aiagent contract-check` in matrix đúng định dạng (✓/⚠/✗, Breaking changes: N, Warnings: N) + exit code 0 khi breaking=0 | Chạy CLI thật |
| AC8 | CLI `aiagent contract list` in 10 contract (id, version, lifecycle) | Chạy CLI thật |
| AC9 | Không breaking change với M1–M9 (full suite vẫn pass) | pytest full |
| AC10 | Đóng DoD: LOG.md + PROGRESS.md + commit | Checklist AGENTS.md §3.1 |

## Ghi chú

- Data-driven: ContractDefinition khai báo tĩnh khớp code thật; test đảm bảo schema_ref import được (không tên ảo).
- Plugin v1 deprecated: migration_path = "plugin v2 (Ecosystem Entry)" — ghi chú, không implement migration ở task này (TASK-074).
