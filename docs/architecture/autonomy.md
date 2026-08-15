# Autonomy Layer — AIOS 1.0

> PLAN.md §M9: `Autonomous = Goal-driven + Bounded + Observable + Reversible + Evaluated`. Autonomy Layer KHÔNG thay Orchestrator — nó định hướng Orchestrator (`Autonomy → Orchestrator → Runtime`). Mọi autonomous action phải qua **Autonomy Governor** (INV-030).

## Kiến trúc (module thật — `backend/src/aios_core/autonomous/`)

```
                    AUTONOMY LAYER
   ┌──────────────┬──────────────┬───────────────┐
   ▼              ▼              ▼               ▼
Goal Engine    Planner       World Model      Governor
(goal.py)     (planner.py)   (world.py)      (governor.py)
   │              │              │               │
   └──────────────┴──────┬───────┴───────────────┘
                         ▼
                   Autonomous Loop (loop.py)
              Observe → Understand → Decide → Plan
              → Policy → Act → Verify → Learn
                         │
                         ▼
                    ORCHESTRATOR → Runtime
```

## Module & trách nhiệm

| Module | Trách nhiệm | INV |
|--------|-------------|-----|
| `goal.py` | Goal contract (objective/success/constraints/permissions/autonomy) + lifecycle 13 state | — |
| `planner.py` | Goal→World→Constraints→Capabilities→History→Plan; dynamic replanning | — |
| `world.py` | WorldState (System/Runtime/Goals/Tasks/Environment/Constraints/History) + Fact (source/timestamp/confidence) — World ≠ Memory | — |
| `loop.py` | Vòng lặp 8 bước; mọi action qua governor | INV-030 |
| `governor.py` | Quyết định CONTINUE/PAUSE/ASK_HUMAN/REPLAN/ROLLBACK/STOP + budget (steps/llm/cost/duration/tool/retries/parallel) + risk budget | INV-030, INV-031 |
| `recovery.py` | Detect→Classify→Diagnose→Strategies→Score→Policy→Execute→Verify; fingerprint + circuit breaker + cooldown | — |
| `long_horizon.py` | ExecutionSession + Checkpoint + context compaction + resume | INV-032 |
| `memory.py` | Working/Episodic/Semantic/Procedural/Failure/Goal + Learning Loop (candidate→dedup→validate→confidence→promote) | INV-034 |
| `stuck.py` | 7 signals: repeated tool/errors, no state change/progress, oscillation, budget burn, contradictory | — |
| `experimentation.py` | Hypothesis→Design→Sandbox→Execute→Evaluate→Compare→Accept/Reject (qua Harness) | INV-033 |
| `evaluation.py` | correctness/quality/cost/risk/progress/confidence → decision + ProgressEstimator | — |
| `multi_agent.py` | mode single/parallel/sequential/hierarchical + delegation (owner/deadline/budget/output) | — |
| `scheduler.py` | Proactive triggers (INTERVAL/DAILY), last-run persist | — |

## Chuỗi bắt buộc (không shortcut)

```
Autonomous Agent → Action Proposal → Autonomy Governor → Policy Engine
                → Permission Broker → Capability → Tool
❌ Agent → Tool · ❌ Planner → Shell · ❌ Loop → Runtime side effect
```

## Budget & Risk (Autonomy Budget — PLAN §M9-13)

`max_steps: 100 · max_llm_calls: 50 · max_cost: 10.00 · max_duration_s: 7200 · max_tool_calls: 200 · max_retries: 5 · max_parallel_agents: 4`
Risk table: read/edit = autonomous · commit/deploy = approval · delete = impossible.
Hết budget → STOP hoặc ASK_HUMAN.

## Level hoạt động (Governance — PLAN §M9-29)

`LEVEL 0 Observe only · 1 Recommend · 2 Execute read-only · 3 Execute reversible · 4 Bounded production · 5 Fully autonomous within policy`
Enterprise mặc định: `default_level: 2 · production: 1 · development: 4`.
