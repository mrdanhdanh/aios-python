# TASK-075 — Test + Evaluation (Performance & Cost)

## Test — `tests/test_performance.py` **11/11 pass**
- Cost formula: tokens/1M × cost (AC2) + unknown capability → 0
- Tool cost + aggregate 5 chiều + cost_per_success SKIPPED khi 0 success (AC3/AC4)
- PerformanceMetrics: empty → 0; storage size (AC1); với metrics thật
- Model independence: 3 provider đều ModelContract + registry swap (AC7)
- CLI cost + performance (AC5/AC6)

## Full suite: **1917 passed** (AC8).

## Evaluation — 9/9 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 performance metrics | ✅ |
| AC2 cost formula | ✅ |
| AC3 aggregate | ✅ |
| AC4 cost/success | ✅ |
| AC5 CLI cost | ✅ |
| AC6 CLI performance | ✅ |
| AC7 model independence | ✅ |
| AC8 regression | ✅ |
| AC9 DoD | ✅ |

## Bài học
1. Offline-first: token estimate injectable — không cần LLM thật để tính cost.
2. Model Provider Contract độc lập đã chứng minh (Mock/OpenAI/Ollama cùng interface) — AIOS không thành OpenAI wrapper.
3. Layer rule: CLI không được import models.capability trực tiếp (scanner bắt) — dùng registry qua container.
