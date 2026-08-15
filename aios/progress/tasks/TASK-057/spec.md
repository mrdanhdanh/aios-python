# TASK-057 — Autonomous Memory (M9-P2)

## Mục tiêu
Nâng Memory Coordinator (M5) thành nhiều loại memory: `Working · Episodic · Semantic · Procedural · Failure · Goal` (PLAN §M9-19). Learning Loop: `Execution → Evaluation → Failure/Success → Extract Lesson → Validate → Memory → Future Planning` (§M9-20). **INV-034: autonomous memory không tự promote thành Knowledge chưa kiểm chứng** — phải candidate → deduplicate → validate → confidence → promote.

## Phạm vi
- `autonomous/memory.py`: `AutonomousMemory` — 6 kinds, entry persist (SQLite), `LearningLoop` (extract lesson → candidate → deduplicate → validate → promote)
- `contracts.py`: `MemoryEntryKind` (6), `MemoryEntry` (kind, key, content, confidence, validated, source, created_at), `Lesson`

## Input/Output
- In: `store(kind, key, content, confidence)`; `learn(failure/success, context)` → Lesson; Out: MemoryEntry / promotion
- Fail-closed: promote entry chưa validated → raise (INV-034)

## Tiêu chí chấp nhận (AC)
1. 6 kinds: WORKING/EPISODIC/SEMANTIC/PROCEDURAL/FAILURE/GOAL
2. `store` + `retrieve(kind, key)` — persist SQLite cross-instance
3. `learn()` tạo Lesson candidate từ failure (when/failure/cause/fix/confidence — pattern Failure Memory §M9-19)
4. Deduplicate: lesson trùng (cùng failure fingerprint) → không thêm mới, tăng confidence
5. **INV-034**: `promote(key)` chỉ thành công khi `validated=True` — chưa validate → raise `MemoryPromotionError`
6. `validate(key, confidence)` đánh dấu validated + cập nhật confidence (từ evaluation/human)
7. Confidence threshold: entry confidence < 0.5 không được promote kể cả validated? (không — validated bởi nguồn đáng tin; giữ validated là gate duy nhất v1)
8. Emit event `autonomy.memory_promoted` khi promote thành công
9. Goal memory: lưu goal progress notes theo goal_id
10. Contract `extra=forbid` + unit tests coverage ≥ 90%

## Amend (critique ×2 resolve)
- C1-01: `validate(key, confidence, source)` — source bắt buộc (không validate trống)
- C1-02: dedup → confidence = min(1.0, old + 0.1), updated_at mới
- C1-03: learn() thiếu cause/fix → confidence 0.3 (không promote được); đủ 5 keys → confidence input
- C1-04: `retrieve(kind, key=None)` — key None → list theo kind
- C1-05: working memory không TTL v1 (cleanup wiring sau)
- C2-01: promote cần validated=True VÀ confidence ≥ 0.5 (double gate)
- C2-02: promote v1 = đánh dấu promoted=True + emit event (không sửa knowledge/)
- C2-03: learn() key tự sinh `lesson:{fingerprint}`
