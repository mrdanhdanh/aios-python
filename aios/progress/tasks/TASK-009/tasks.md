# TASK-009 — Breakdown checklist

## J1 — Capabilities + Prompts
- [ ] J1.1 `capabilities/registry.py` + errors + __init__ (Capability, CapabilityRegistry, CapabilityError)
- [ ] J1.2 `prompts/registry.py` + errors + __init__ (PromptTemplate construct-validate, PromptRegistry render/evaluate/evaluations)
- [ ] J1.3 test_capabilities.py (10 case), test_prompts.py (12 case: extract edge, render, evaluations)

## J2 — Catalog + Graph
- [ ] J2.1 `catalog/catalog.py` + errors + __init__ (SystemCatalog, CatalogError)
- [ ] J2.2 `knowledge_graph/graph.py` + errors + __init__ (KnowledgeGraph, GraphError)
- [ ] J2.3 test_catalog.py (8 case), test_knowledge_graph.py (10 case)
- [ ] J2.4 re-export 4 module ở aios_core/__init__ + test_import cập nhật

## J3 — Verify + Commit
- [ ] J3.1 test_integration (AC8 scenario) + pytest pass, coverage ≥ 80%, git sạch
- [ ] J3.2 Commit code + progress files + commit cuối → **M1 done**
