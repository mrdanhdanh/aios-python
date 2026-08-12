# TASK-009 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Capability registry | `backend/src/aios_core/capabilities/` (Capability, CapabilityRegistry, CapabilityError) |
| Prompt registry | `prompts/` (PromptTemplate construct-validate, PromptRegistry render/evaluate/evaluations) |
| System catalog | `catalog/` (SystemCatalog, CatalogError) |
| Knowledge graph | `knowledge_graph/` (KnowledgeGraph, GraphError) |
| PLAN amend | `docs/PLAN.md` (Knowledge Graph in-memory, M1-P2 thủ công, Prompt str.format v1) |
| Tests (5 file mới) | `test_capabilities.py`, `test_prompts.py`, `test_catalog.py`, `test_knowledge_graph.py`, `test_integration.py` |

## Quyết định kỹ thuật (qua critique ×2)
- **Prompt v1**: str.format subset — `{identifier}` thuần; regex `(?<!\{)\{([A-Za-z_]\w*)\}(?!\})`; scan escape-first; validate lúc CONSTRUCT; render bọc KeyError → PromptError; evaluations history append; "mới nhất" theo semver.compare
- **Catalog**: search đệ quy scalar (bỏ None, key không search), kind exact, sorted (kind, id)
- **Graph**: in-memory; neighbors tách 2 chiều (out → target_id, in → source_id) + dedup; add_edge missing node → GraphError; delete cascade
- **Capability**: canonical registry (nguồn sự thật cho M2 graph populate); agents_using set idempotent
