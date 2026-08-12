# TASK-010 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Normalizer | `backend/src/aios_core/orchestrator/normalizer.py` (alias/macro/params, #/!skill) |
| Rule engine | `rule_engine.py` (word-boundary, priority→longest→insertion, default_rules 8 rule) |
| Workflow matcher | `workflow_matcher.py` (macro → full → token + stopword, confidence re-check) |
| Planner | `planner.py` (Planner + PlannerStub, _calls counter, ModelError catch) |
| Agent selector | `agent_selector.py` (intent → agent) |
| System knowledge | `system_knowledge.py` (catalog/graph/library queries, catch errors) |
| Orchestrator | `orchestrator.py` (pipeline 4 tầng, stats/reset, rule+workflow_name) |
| Tests (7 file) | `test_normalizer.py`, `test_rule_engine.py`, `test_workflow_matcher.py`, `test_planner.py`, `test_orchestrator.py`, `test_agent_selector.py`, `test_system_knowledge.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- **Offline-first**: Normalizer/RuleEngine/Matcher 0 token; Planner chỉ khi không resolve; AC6 verify 90% deterministic
- **Rule-vs-matcher**: rule có agent → matcher VẪN chạy (workflow_name phụ, resolved_by="rule"); rule "crud" agent=None → matcher path
- **Thứ tự match**: priority desc → longest pattern → insertion asc; word-boundary `\b` chống false positive
- **Stats**: Planner._calls (đếm cả raise), Orchestrator.stats() copy + reset() gọi planner.reset_calls(); lock chỉ bao counter
- **SystemKnowledge**: plural→singular mapping; catch GraphError/CatalogError/WorkflowError → None
