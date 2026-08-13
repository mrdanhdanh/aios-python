# TASK-016 — Architecture Hardening: Invariants + Reference Update

**Metadata**
- Task ID: `TASK-016`
- Milestone / Phase: M2 (Developer Edition) / Kiến trúc (chèn giữa M2-P3b → P3c)
- Ngày: 2026-08-13
- Trạng thái: `draft` (chờ critique ×2 + review)
- Owner: AIOS Orchestrator
- Lý do: user gửi phân tích kiến trúc 12 điểm (Orchestrator ≠ God Object, Agent→Capability→Tool enforced, 10 Architecture Invariants, Execution Plane, Evaluation post-execution observer, Knowledge/Context/Memory boundary, Scheduler/Resource/Execution phân vai, Architecture Health M4) — cần chốt vào repo + test tự động TRƯỚC khi sinh agents (TASK-013) và tools (TASK-014)

---

## 1. Mục tiêu

1. **Chốt 10 Architecture Invariants (INV-001..INV-010)** thành phần chuẩn của repo — mọi PR/task vi phạm FAIL architecture review.
2. **Cập nhật `docs/architecture.md`** (đang là source-of-truth reference): phân biệt Control Plane / Execution Plane, sửa flow (Evaluation là post-execution observer, Knowledge KB vs KG, Context vs Memory, Scheduler/Resource/Execution phân vai), dependency một chiều Agent→Capability→Tool→Infra.
3. **Architecture tests tự động** (`tests/test_architecture.py`, AST-based) — enforce các invariant có thể kiểm tra được bằng static analysis; reviewer/subagent có thể chạy để kiểm tra tự động.
4. **ADR mới** ghi quyết định (kèm 4 invariant chốt).

## 2. Phạm vi

### In
1. `docs/architecture.md`: thêm section "Architecture Invariants" (INV-001..010) + "Control vs Execution Plane" + sửa các flow theo 12 điểm user (Evaluation observer, Knowledge boundary, Context/Memory, Scheduler/Resource/Execution, dependency 1 chiều, System Knowledge là "System Brain")
2. `docs/adr/0004-architecture-invariants.md` — quyết định + rationale + 4 invariant chốt (Orchestrator không God Object; Agent không chạm Tool; Workflow không biết Engine; Execution không bypass Policy)
4. `docs/PLAN.md`: link ADR-0004 + ghi chú invariants ở mục "Quyền hạn" + **ghi chú Architecture Health → M4 (đề xuất #10)** (C1-06)
4. `backend/tests/test_architecture.py` — AST import-graph tests:
   - INV-001: worker agents (`agents/`, `tools/`) nếu tồn tại → không import `kernel.services` — **skip nếu thư mục chưa tồn tại**; hằng số `AGENTS_DIR = SRC_ROOT/"aios_core"/"agents"`, `TOOLS_DIR = SRC_ROOT/"aios_core"/"tools"` (C1-08 — TASK-013/014 phải tạo đúng tên package con); **`SRC_ROOT = Path(__file__).resolve().parents[1] / "src"` (từ `backend/tests/` → `backend/src` — R1) + guard `assert (SRC_ROOT / "aios_core").is_dir()` fail-fast (KHÔNG bao giờ skip âm thầm)**
   - INV-002: `agents/` (khi tồn tại) không import `aios_core.tools` trực tiếp (C2-03) — skip nếu chưa có; **INV-004 tiền đề: `capabilities/` không chứa `aios_core.tools` (chạy NGAY, không skip)**
   - INV-003: **directory scan** `workflow/` (kể cả `__init__.py`, C1-05) không import langgraph / `aios_core.models` (compiler.py LangGraphCompiler stub cho phép — chỉ class, không import thật)
   - INV-004: `capabilities/` không import `aios_core.models`, `aios_core.workflow`
   - INV-005 rule A: `orchestrator/` (kể cả `goals/`) trừ `planner.py` không import `aios_core.models`; **rule B (C2-01 — allow-list): `planner.py` CHỈ được import `aios_core.models.base` + `aios_core.models.errors`** — mọi module khác dưới `models` (kể cả `aios_core.models` trần vì `__init__.py` re-export OpenAIModel/OllamaModel) đều cấm; semantics **dot-boundary** (`mod == target OR mod.startswith(target + ".")`, không startswith trần); test vi phạm `from aios_core.models import OpenAIModel` → FAIL; AST chỉ check direct imports
   - INV-007 (**hard test — C2-04**): `kernel/services/execution.py` phải có **call-site** `self._policy.evaluate(` (AST Attribute access — gỡ call = fail, import chỉ là điều kiện phụ)
   - INV-009 (C2-02): hard test cho **4 business services** ĐÃ emit (execution, artifacts, permissions, policy — mỗi service tham chiếu EventType); `events.py` = infrastructure (loại khỏi phép đếm — chính nó định nghĩa API event); context/state/resource/scheduler chưa emit → ghi nhận future (kèm ghi chú: state có lifecycle thật — snapshot do execution emit SNAPSHOT_SAVED)
   - INV-010 (C1-07): mở rộng — `rule_engine`, `normalizer`, `workflow_matcher`, `system_knowledge` + `catalog/`, `knowledge_graph/`, `prompts/` không import `aios_core.models`
   - INV-012/INV-006 (C1-12): `contracts/` purity — không import `kernel.services`/`kernel.events`
```python
# tests/_arch_scan.py
def collect_imports(package_dir: Path, module_rel: str) -> tuple[set[str], set[str]]:
    """Parse module (ast, không import), trả (external_top_level, aios_core_modules)."""
    # aios_core_modules: FULL dotted name (absolute + relative) — R2
    # MỌI Import node đều tính (top-level, function, try/except, TYPE_CHECKING)

def assert_no_imports(module_rel: str, forbidden: list[str], reason: str):
    """Fail nếu module import module thuộc forbidden.
    Match 2 CHIỀU (R2): mod == target or mod.startswith(target + ".")
    or target.startswith(mod + ".")"""
```

### Out
- KHÔNG sửa code business hiện có (trừ khi test phát hiện vi phạm — fix theo bypass hợp lệ ghi LOG)
- KHÔNG tạo `agents/`/`tools/` (TASK-013/014)
- KHÔNG enforce INV-008 Artifact First (chưa có boundary artifact trong code — ghi nhận tương lai)
- KHÔNG làm Architecture Health runtime (M4 — chỉ ghi vào PLAN như đề xuất #10)
- KHÔNG refactor Orchestrator (chỉ test + docs)

## 3. Input / Output

**Input:** `docs/architecture.md` (hiện có), `docs/PLAN.md` (mục Quyền hạn), phân tích 12 điểm user, source tree `backend/src/aios_core/`
**Output:** architecture.md cập nhật, ADR-0004, PLAN.md link + ADR index (C2-07), `tests/test_architecture.py` + `tests/_arch_scan.py`, commit, PROGRESS/LOG cập nhật

### Bảng map 12 điểm user → xử lý (C2-06)

| # | Điểm user | Xử lý | File/đoạn | AC |
|---|-----------|-------|-----------|-----|
| 1 | Orchestrator không phải God Object — không sở hữu Runtime trực tiếp, chỉ request | Sơ đồ Control/Execution Plane tách bạch + text | architecture.md §1, §2 | AC2 |
| 2 | Agent→Capability→Tool enforced ở contract | INV-001/002 + test (agents/ chưa có — skip, premise capabilities) | architecture.md §Invariants + test | AC6 |
| 3 | 10 Architecture Invariants | Section mới + bảng enforce | architecture.md §7 | AC1 |
| 4 | Dependency 1 chiều Agent→Capability→Tool→Infra | Sửa sơ đồ T5→T6→T7 thành 1 chiều + text | architecture.md §1 | AC2 |
| 5 | Evaluation = post-execution observer | Flow: Execution→Result→User; Execution→Event→Evaluation→Knowledge | architecture.md §3 | AC3 |
| 6 | Knowledge Base vs Knowledge Graph phân biệt | Sơ đồ knowledge tree | architecture.md §3 (hoặc mới) | AC3 |
| 7 | Context vs Memory boundary | Định nghĩa Context (đang dùng) vs Memory (lưu lại), luồng Memory→Coordinator→Context→Execution | architecture.md §3 | AC3 |
| 8 | Scheduler/Resource/Execution 3 vai (WHEN/CAN/ HOW) | Bảng phân vai + flow | architecture.md §3 | AC3 |
| 9 | System Knowledge = System Brain (qua Catalog/KG, không đọc registry trực tiếp) | Text + sơ đồ Registries→Catalog→KG→SystemKnowledge→Orchestrator | architecture.md §3 | AC2/AC3 |
| 10 | Architecture Health → M4 | Ghi chú PLAN.md | PLAN.md | AC5 |
| 11 | Execution Plane (phân biệt Control/Execution, không thêm tầng vật lý) | Sơ đồ 2 plane + text | architecture.md §1, §2 | AC2 |
| 12 | Kiến trúc cuối tham chiếu | Đối chiếu sơ đồ cuối user vs architecture.md — điều chỉnh nếu lệch | architecture.md toàn bộ | AC2 |

## 4. Kiến trúc test (AST scan) — cú pháp dir-scan thống nhất (C2-05)

```python
# tests/_arch_scan.py
def collect_imports(package_dir: Path, module_rel: str) -> tuple[set[str], set[str]]:
    """Parse module (ast, không import), trả (external_top_level, aios_core_modules)."""
    # xử lý: import a, from . import b, from ..x import y, from aios_core.z import w
    # MỌI Import node đều tính (top-level, function, try/except, TYPE_CHECKING)

def assert_no_imports(module_rel: str, forbidden: list[str], reason: str):
    """Fail nếu module import module thuộc forbidden (dot-boundary match)."""
```

Rules (**dir scan — kể cả `__init__.py`, trừ exclude tường minh**):
- `workflow/**` → không import `langgraph`, `aios_core.models` (INV-003)
- `capabilities/**` → không import `aios_core.models`, `aios_core.workflow`, `aios_core.tools` (INV-004)
- `orchestrator/**` (kể cả `goals/`, trừ `planner.py`) → không import `aios_core.models` (INV-005 rule A)
- `orchestrator/planner.py` → **allow-list**: chỉ `aios_core.models.base` + `aios_core.models.errors` (INV-005 rule B — C2-01)
- `orchestrator/rule_engine.py`, `normalizer.py`, `workflow_matcher.py`, `system_knowledge.py` + `catalog/**`, `knowledge_graph/**`, `prompts/**` → không import `aios_core.models` (INV-010)
- `contracts/**` → không import `kernel.services`, `kernel.events` (INV-006 purity — C1-12)
- `agents/**` (khi tồn tại) → không import `kernel.services` (INV-001), không import `aios_core.tools` (INV-002); `capabilities/**` không chứa `aios_core.tools` (INV-004 premise — chạy ngay)
- Policy-first (INV-007): `kernel/services/execution.py` có call-site `self._policy.evaluate(` (C2-04)

## 5. 10 Invariants (ghi vào architecture.md + ADR)

| ID | Tên | Nội dung | Enforce |
|----|-----|----------|---------|
| INV-001 | Runtime Isolation | Worker Agent không truy cập trực tiếp Runtime Service | test (khi có agents/) |
| INV-002 | Capability Isolation | Agent không gọi Tool trực tiếp — chỉ qua Capability | test tiền đề (khi có agents/+tools/) |
| INV-003 | Workflow Independence | Workflow Definition không phụ thuộc engine (LangGraph) | test ✅ |
| INV-004 | Tool Independence | Capability không phụ thuộc implementation Tool cụ thể | test ✅ |
| INV-005 | Control Plane Isolation | Orchestrator điều phối, không chứa business implementation | test ✅ (rule A + rule B allow-list) |
| INV-006 | Contract First | Cross-layer giao tiếp qua Contract | manual review + purity check contracts/ |
| INV-007 | Policy First | Execution phải qua policy pre-check trước side effect | test ✅ (hard — call-site `_policy.evaluate`) |
| INV-008 | Artifact First | Output giữa boundary tham chiếu Artifact | future (M4) |
| INV-009 | Event Driven | Lifecycle quan trọng phát Event | test một phần ⚠️ (4/8 business + infra events; 4 future) |
| INV-010 | Deterministic First | Rule/Registry/Workflow ưu tiên trước LLM | test ✅ (mở rộng catalog/KG/prompts) |

## Ràng buộc (bổ sung sau critique v1)

- `_arch_scan.py` + `test_architecture.py` KHÔNG import aios_core runtime (chỉ `ast.parse` source) — coverage không đổi (C1-11)
- KHÔNG thêm `tests/__init__.py` (sẽ phá `import _arch_scan` — pytest prepend mode)
- AST chỉ check direct imports — transitive qua planner (orchestrator→planner→models) là hợp lệ theo ngoại lệ (C1-03)

## 7. Tiêu chí chấp nhận

- [ ] AC1 — `docs/architecture.md` có section "Architecture Invariants" đủ 10 INV + bảng enforce status
- [ ] AC2 — architecture.md phân biệt rõ **Control Plane vs Execution Plane** (sơ đồ 2 plane + text — điểm #1/#11); **dependency 1 chiều** Agent→Capability→Tool→Infra (#4); **System Knowledge = System Brain** (Registries→Catalog→KG→SystemKnowledge→Orchestrator, #9)
- [ ] AC3 — Flow sửa (#5/#6/#7/#8): Evaluation là post-execution observer (không nằm trong execution chain); Knowledge Base vs Knowledge Graph phân biệt; Context vs Memory boundary (Memory→Coordinator→Context→Execution); Scheduler/Resource/Execution 3 vai (WHEN/CAN/HOW)
- [ ] AC4 — `docs/adr/0004-architecture-invariants.md` tồn tại: 4 invariant chốt + rationale + 10 INV tham chiếu (KHÔNG copy nội dung architecture.md — C2-09) + **ghi gap: `sandbox_required` chưa enforce trong v1** (execution.py chỉ logger.warning)
- [ ] AC5 — `docs/PLAN.md`: link ADR-0004 ở mục Quyền hạn + ghi chú invariants + **ghi chú Architecture Health → M4** + **cập nhật ADR index (0001..0004)** (C2-07)
- [ ] AC6 — `tests/test_architecture.py` chạy được: INV-003 (dir scan cả `__init__.py`), INV-004 (+premise không skip), INV-005 (rule A + rule B allow-list — **test vi phạm `from aios_core.models import OpenAIModel` → fail**), INV-007 (hard call-site), INV-010 (mở rộng catalog/KG/prompts), INV-006 purity pass; INV-009 4 business hard + 4 future; INV-001/002 skip khi agents//tools/ chưa tồn tại
- [ ] AC7 — Helper `_arch_scan.py`: trả 2 tập (external_top_level + aios_core_modules); resolve relative thuần (không sys.path); **mọi Import node đều tính** (function/try-except/TYPE_CHECKING); test assert PHÁT HIỆN import lậu trong try/except
- [ ] AC8 — Test phát hiện vi phạm giả lập: tạo `tmp_path/evil.py` (absolute import `import aios_core.models` — C2-10) → scan phát hiện → test fail
- [ ] AC9 — pytest toàn bộ pass (490 + test mới), **bảng tiến độ architecture.md cập nhật (490 tests, 95.96%, TASK-012 done — C2-08)**, git sạch
- [ ] AC10 — PROGRESS/LOG/STATS cập nhật + commit

## 8. Kế hoạch test

- `tests/test_architecture.py`:
  - `test_inv003_workflow_no_engine` — dir scan `workflow/` (kể cả __init__.py) không import langgraph/models
  - `test_inv004_capability_no_tool_impl` — capabilities/ không import models/workflow/tools
  - `test_inv005_control_plane_no_business` — rule A (orchestrator trừ planner không import models) + rule B (orchestrator kể cả planner không import providers)
  - `test_inv007_policy_first_hard` — execution.py tham chiếu PolicyService (HARD — C1-02)
  - `test_inv009_event_driven_partial` — **4 business services** emit (execution/artifacts/permissions/policy) + events.py = infrastructure + 4 future (C2-02, R5)
  - `test_inv010_deterministic_first` — rule_engine/normalizer/matcher/system_knowledge + catalog/knowledge_graph/prompts không import models (C1-07)
  - `test_inv006_contracts_purity` — contracts/ không import kernel.services/events (C1-12)
  - `test_inv001_worker_no_runtime` / `test_inv002_worker_no_direct_tool` — skip nếu agents//tools/ chưa tồn tại (C1-08/10)
  - `test_arch_scan_detects_violation` — AC8: `tmp_path/evil.py` vi phạm → phát hiện (C1-13)
  - `test_arch_scan_detects_nested_import` — AC7: import lậu trong try/except/function → PHÁT HIỆN (C1-04)
  - `test_arch_scan_resolves_relative` — resolve `.`/`..`/absolute đúng (C1-09)

## Phụ thuộc
- Không có (chỉ stdlib ast + pytest)
