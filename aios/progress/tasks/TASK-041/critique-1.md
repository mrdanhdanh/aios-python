# TASK-041 — Critique v1

## Vấn đề
- **P1-01**: hash phải bao gồm previous_hash để chain không thể reorder.
- **P2-01**: SENSITIVE action set cần define để mark.

## Resolution
- ✅ `_hash_event` sha256(previous_hash + serialized).
- ✅ SENSITIVE set trong operations.py.
