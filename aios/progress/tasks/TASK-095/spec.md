# TASK-095 — M14-P1: Candidate Generate + Risk Scoring

> Milestone: M14 Controlled Self-Healing
> P1: Generate candidate fixes from failure corpus + risk scoring (low/med/high)

## Design

### Contracts (`harness/heal/contracts.py`)

```python
class RiskLevel(str, Enum):
    LOW = "low"        # auto-apply allowed (M15)
    MEDIUM = "medium"  # requires human approval
    HIGH = "high"      # always requires human approval
    CRITICAL = "critical"  # never auto-apply

class CandidateFix(BaseModel):  # extra="forbid"
    failure_signature: str
    description: str
    risk_level: RiskLevel
    confidence: float  # 0.0-1.0
    suggested_action: str  # "retry" | "fix_config" | "fix_code" | "skip"
    evidence: dict

class CandidateReport(BaseModel):
    candidates: list[CandidateFix]
    total: int
    by_risk: dict[str, int]
```

### Engine (`harness/heal/engine.py`)

```python
class HealEngine:
    def generate(self, corpus: list[FailureRecord]) -> CandidateReport:
        """Analyze failure patterns → generate candidate fixes with risk scores."""
        # Pattern matching: repeated failures → higher confidence
        # Severity mapping: HIGH severity → higher risk
        # Component analysis: known flaky components → lower confidence
```

### AC
1. CandidateFix shape (extra="forbid") + 4 RiskLevel enum
2. generate() from empty corpus → empty candidates
3. generate() from single failure → 1 candidate with correct risk
4. Risk scoring: HIGH severity → HIGH risk, LOW → LOW
5. Repeated failures (same signature) → higher confidence
6. CandidateReport shape
7. Determinism: same corpus → same candidates
8. Harness id="heal" + persist
9. CLI `aiagent harness heal` → candidate list
10. Full suite no regression
