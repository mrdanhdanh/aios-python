# TASK-052 — World Model (M9-P1)

## Mục tiêu
Tạo abstraction **Autonomous World State** kế thừa System Catalog + Knowledge Graph + Observability + Memory: `WORLD = System · Runtime · Goals · Tasks · Environment · Constraints · Historical State`. **World State ≠ Memory**: Memory = những gì AIOS nhớ; World State = AIOS tin thế giới hiện tại như thế nào. Mỗi fact có `source · timestamp · confidence · freshness`.

## Phạm vi
- `autonomous/world.py`: `WorldModel` — store facts (in-memory v1 + deterministic), snapshot, confidence decay
- `contracts.py`: `WorldFact` (name, value, source, observed_at, confidence 0..1), `WorldState` (system, runtime, goals, tasks, environment, constraints, history[]), `WorldScope` (7 loại)

## Input/Output
- In: `observe(scope, name, value, source, confidence)`; Out: `get_fact`, `snapshot()`, `history`
- Fail-closed: confidence ngoài [0,1] → clamp (không raise)

## Tiêu chí chấp nhận (AC)
1. `WorldFact` đủ 5 trường (name, value, source, observed_at, confidence) — `extra=forbid`
2. `observe()` ghi fact + append vào history của scope
3. `get_fact(name)` trả fact mới nhất (theo observed_at)
4. `freshness` tính deterministic từ observed_at + clock (già → fresh thấp)
5. Confidence decay theo freshness (fact càng cũ → confidence càng giảm, không âm)
6. `snapshot()` trả `WorldState` đủ 7 nhóm, deterministic (sorted)
7. World ≠ Memory: `world.py` KHÔNG import `aios_core.memory` / `aios_core.knowledge` (arch test)
8. `WorldScope` đủ 7 giá trị (SYSTEM, RUNTIME, GOALS, TASKS, ENVIRONMENT, CONSTRAINTS, HISTORY)
9. Clock injectable (test deterministic)
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique-1 resolve)
- **C1-01**: `freshness = max(0.0, 1.0 - age_s / TTL_S)` (TTL_S injectable, mặc định 86400); `effective_confidence = confidence * freshness`
- **C1-02**: history giới hạn `max_history` per scope (mặc định 100, injectable) — FIFO trim
- **C1-03**: `value: Any` (primitive + dict/list; JSON-serializable)
- **C1-04**: key = `f"{scope.value}.{name}"` — `get_fact(scope, name)` unambiguous
- **C1-05**: WorldModel là store thuần (observable state); constraints/goals được observe từ ngoài (loop/engine ghi vào)

## Amend (critique-2 resolve)
- **C2-01**: `observed_at: float` (epoch seconds từ clock injectable); snapshot() xuất ISO string
- **C2-02**: lưu raw (confidence, observed_at); `get_fact` tính `effective_confidence` tại thời điểm get; history lưu raw
- **C2-03**: `WorldState.constraints: dict[str, Any]` flat
