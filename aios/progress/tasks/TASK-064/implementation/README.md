# TASK-064 — Implementation (Contract 1.0)

| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/contracts/catalog.py` | ContractLifecycle (STABLE/FROZEN/DEPRECATED/REMOVED) + ContractDefinition (7 trường, extra=forbid, model_validator cross-field) + ContractCatalog (10 contract: agent/capability/tool/workflow/runtime/event/artifact/plugin/model/memory) + verify_schema_refs |
| `backend/src/aios_core/contracts/check.py` | ContractChecker — check_all() matrix (✓/⚠/✗ + breaking_count + warning_count + blocking) + check_deprecated_usage + format_matrix (CLI render) |
| `backend/src/aios_core/workflow/cli.py` | +`aiagent contract list` / `contract check` / `contract check-full`; stdout reconfigure utf-8 |
| `backend/tests/test_contracts_catalog.py` | 20 tests (catalog, schema import thật, lifecycle validation, matrix, deprecation, CLI) |

## Chi tiết catalog (10 contract frozen 1.0.0)

| id | lifecycle | schema_ref thật |
|----|-----------|-----------------|
| agent | stable | agents.base.Assistant |
| capability | stable | capabilities.registry.Capability |
| tool | stable | tools.base.Tool |
| workflow | stable | workflow.definition.WorkflowDefinition |
| runtime | frozen | kernel.runtime_kernel.RuntimeKernel |
| event | stable | kernel.events.EventType |
| artifact | frozen | contracts.artifact.ArtifactContract |
| plugin | deprecated (v1 → Ecosystem Entry) | plugins.contracts.PluginManifest |
| model | stable | models.base.ModelContract |
| memory | stable | memory.contracts.MemoryContext |
