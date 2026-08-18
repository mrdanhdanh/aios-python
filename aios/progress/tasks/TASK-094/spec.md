# TASK-094 — M14-P0: Detect & Diagnose — Failure Corpus + Signature + Localization

> Milestone: M14 Controlled Self-Healing (Issue #8, nhánh `feature/ISSUE-8-m14-controlled-self-healing`)
> Nâng cấp: P0 — Detect & Diagnose — thu thập evidence, sinh failure signature, localize component
> Dependency: M13 (TASK-089..093 ✅) → M14-P0 → (P1 TASK-095)
> Trạng thái: `in-progress` (hard gate)

## 1. Mục tiêu

**Detect & Diagnose** là bước đầu tiên của closed-loop remediation (PLAN §M14-P0):
- Thu thập **failure evidence** từ các harness run đã thất bại (FAILED/DIAGNOSED)
- Sinh **failure signature** — fingerprint deterministic của lỗi (hash từ error type + component + message)
- **Localize** — xác định component/module nào gây lỗi
- Lưu vào **failure corpus** — kho lưu trữ các lỗi đã biết, dùng cho P1 (candidate generate)

**🔴 Nguyên tắc**: Detect & Diagnose **KHÔNG** sửa lỗi — nó chỉ thu thập, phân loại, và localize. Sửa chữa thuộc P1 (candidate generate) + P2 (simulation) + P3 (apply).

## 2. Phạm vi

**In:**
- Module mới `backend/src/aios_core/harness/diagnose/` (contracts + engine + errors)
- `FailureRecord` — bản ghi một lần thất bại (run_id, harness_id, status, error_type, error_message, component, signature, evidence, timestamp)
- `FailureSignature` — fingerprint deterministic (sha256 của error_type + component + normalized_message)
- `FailureCorpus` — kho lưu trữ (in-memory dict + persist qua StateService)
- `DiagnoseEngine` — phân tích failure record → sinh signature + localize component
- Wiring: đăng ký `DiagnoseHarness` (id="diagnose") vào `HarnessRegistry`
- CLI: `aiagent harness diagnose` (xem corpus, phân tích failure)
- Tests: `backend/tests/test_harness_diagnose.py`

**Out:**
- P1 (candidate generate) — TASK-095
- P2 (simulation + meta-verify) — TASK-096
- P3 (permission + apply + rollback) — TASK-097
- KHÔNG sửa Runtime/Orchestrator (INV-017..021 giữ nguyên)
- KHÔNG sửa verifier production

## 3. Thiết kế

### 3.1 Contracts (`harness/diagnose/contracts.py`)

```python
class FailureSeverity(str, Enum):
    LOW = "low"          # cosmetic, non-blocking
    MEDIUM = "medium"    # affects functionality
    HIGH = "high"        # blocks release
    CRITICAL = "critical" # security/integrity violation

class FailureRecord(BaseModel):  # extra="forbid"
    run_id: str
    harness_id: str
    status: str            # HarnessRunStatus.value (FAILED/DIAGNOSED)
    error_type: str        # exception class name
    error_message: str     # normalized (no timestamps/uuids)
    component: str         # localized module (e.g. "harness/meta/engine")
    signature: str         # sha256 fingerprint
    severity: FailureSeverity
    evidence: dict         # {events: [...], report: {...}} từ HarnessRunner
    timestamp: datetime

class FailureCorpusReport(BaseModel):  # extra="forbid"
    total: int
    by_harness: dict[str, int]
    by_severity: dict[str, int]
    by_component: dict[str, int]
    unique_signatures: int
    recent: list[FailureRecord]  # 10 gần nhất
    reproducible: dict
```

### 3.2 Engine (`harness/diagnose/engine.py`)

```python
class DiagnoseEngine:
    """Thuần — phân tích failure + sinh signature + localize component."""

    def analyze(self, report: HarnessReport) -> FailureRecord:
        """Tạo FailureRecord từ HarnessReport (FAILED/DIAGNOSED)."""
        # extract error from report.result.summary or events
        # normalize message (strip timestamps, uuids, paths)
        # compute signature = sha256(error_type + component + normalized_msg)
        # determine severity (error subclass → severity mapping)
        # localize component (error traceback → module path)

    def compute_signature(self, error_type: str, component: str,
                          normalized_message: str) -> str:
        """Deterministic signature — same input → same hash."""

    def normalize_message(self, message: str) -> str:
        """Loại bỏ timestamps, uuids, absolute paths — giữ pattern."""
```

### 3.3 Harness (`harness/diagnose/harness.py`)

```python
class DiagnoseHarness(Harness):  # id="diagnose"
    def run(self, ctx) -> Any
        # lấy failure records từ corpus → build report
    def verify(self, ctx, payload) -> None
        # strict → corpus rỗng khi có failures → raise (fail-closed)
    def get_corpus(self) -> list[FailureRecord]
    def add_from_report(self, report: HarnessReport) -> FailureRecord
```

### 3.4 Wiring + CLI

- Wiring: `DiagnoseHarness(state_service=...)` → register id="diagnose"
- CLI: `aiagent harness diagnose` → corpus summary (total/by_harness/by_severity/by_component) + recent 10

## 4. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm chứng |
|---|----|-----------------|
| AC1 | FailureRecord shape: 9 fields + extra="forbid" | Unit test |
| AC2 | FailureSignature deterministic: same input → same hash | Unit test |
| AC3 | normalize_message strips timestamps, uuids, absolute paths | Unit test |
| AC4 | analyze() từ FAILED HarnessReport → FailureRecord với correct fields | Unit test |
| AC5 | analyze() từ COMPLETED report → None (không tạo record) | Unit test |
| AC6 | Severity mapping: HarnessHookError → HIGH, HarnessLifecycleError → MEDIUM, default → LOW | Unit test |
| AC7 | Component localization: error traceback → module path (e.g. "harness/meta/engine") | Unit test |
| AC8 | FailureCorpusReport: total + by_harness + by_severity + by_component + unique_signatures + recent 10 | Unit test |
| AC9 | Harness id="diagnose" registry + lifecycle + persist round-trip | Test wiring + harness |
| AC10 | CLI `aiagent harness diagnose`: corpus summary + JSON | Test CLI |
| AC11 | Full suite không regression + arch-health 0 + doctor healthy | Chạy full pytest |
| AC12 | Determinism: analyze 2 lần cùng report → signature giống hệt | Unit test |

## 5. Rủi ro & giả định

- **R1**: DiagnoseEngine là pure function (không I/O) — dễ test.
- **R2**: Failure corpus in-memory + persist qua StateService (pattern behavioral/coverage).
- **R3**: KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant.
- **R4**: normalize_message phải đủ mạnh để strip variable data nhưng giữ pattern.
- **R5**: Component localization dùng string matching trên error message (không AST — nhẹ).
