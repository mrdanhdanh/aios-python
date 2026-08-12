# TASK-010 — Breakdown checklist

## K1 — Pipeline modules
- [ ] K1.1 `errors.py` + `normalizer.py` (Normalizer: alias/macro/params, #/!skill intents)
- [ ] K1.2 `rule_engine.py` (word-boundary, priority→longest→insertion, default_rules 8 rule)
- [ ] K1.3 `workflow_matcher.py` (macro → full → token search + stopword filter, confidence re-check)
- [ ] K1.4 `planner.py` (Planner + PlannerStub, _calls counter, error handling)
- [ ] K1.5 `agent_selector.py` + `system_knowledge.py` (catch GraphError/CatalogError)
- [ ] K1.6 `orchestrator.py` (pipeline 4 tầng, stats, reset) + __init__ exports + aios_core/__init__

## K2 — Tests
- [ ] K2.1 test_normalizer (6 case), test_rule_engine (8 case), test_workflow_matcher (5 case)
- [ ] K2.2 test_planner (5 case: stub, thật + fake model, timeout, parse fail), test_agent_selector (2)
- [ ] K2.3 test_orchestrator (6 case + AC6 100 requests MockModel + stats/reset), test_system_knowledge (4)
- [ ] K2.4 test_import cập nhật

## K3 — Verify + Commit
- [ ] K3.1 pytest pass, coverage ≥ 80%, git sạch
- [ ] K3.2 Commit code + progress files + commit cuối
