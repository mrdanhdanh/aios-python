# TASK-047 — Test + Evaluation

## Test
`tests/test_ecosystem_devkit.py` (7 tests): structure 6 file, manifest YAML round-trip, stub compile, deterministic bytes, no-overwrite, invalid kind/name, all 5 kinds. CLI `aiagent plugin create` verified thật (tạo 6 file trong TEMP).

## Evaluation
Đạt 7/7 AC. DevKit stateless; stub dùng public SDK (`from aios import ...`); f-string trong template phải escape (`{{...}}`) để không bị `.format` parse nhầm.
**TASK-047 DONE**
