# TASK-073 — Implementation + Evaluation

## Implementation
| Artifact | Nội dung |
|----------|----------|
| `harness/certification/contracts.py` | CertificationArea (9) + AreaResult + GoldenScenario + ConformanceReport (ready = areas + golden + gates) |
| `harness/certification/checks.py` | AreaChecks — 9 area checks structural (scanner/checker/doctor/registry) |
| `harness/certification/golden.py` | 20 GoldenScenario GS-001..020 — behavioral, component thật |
| `harness/certification/conformance.py` | ConformanceRunner (cached golden) + 5 release gates A–E + format |
| `observability/arch_health.py` | +rule harness/certification + exempt khỏi rule harness |
| `workflow/cli.py` | +`aiagent conformance` |
| `tests/test_certification.py` | 9 tests |

## Evaluation — 8/8 AC ĐẠT — `aiagent conformance` → **AIOS 1.0 READY** (9/9 areas, 20/20 GS, 5/5 gates)

## Bài học
- Area = structural ("có cơ chế"), GS = behavioral ("chạy đúng") — phân vai rõ.
- Gate B: FAIL critical ∨ high → fail (warn OK); Gate D: GS + SLO.
