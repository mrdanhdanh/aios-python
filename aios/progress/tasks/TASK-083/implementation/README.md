# TASK-083 — Implementation

> Code thật nằm ở backend/ (xem bảng dưới). Task này implement M11-P4a/b:
> R5 SkillDistiller (Ecosystem Extension) + R7 Static Deploy (optional).

| Module | File | Nội dung |
|--------|------|----------|
| R5 | `backend/src/aios_core/ecosystem/distiller.py` | `SkillDistiller` pipeline 7 bước deterministic + `GitHubFetchStub` (hash URL → seed) + fail-closed/no-overwrite + mirror contract validation (semver — không import skills do allow-list M8) |
| R7 | `backend/src/aios_core/ecosystem/deploy.py` | `StaticDeploy` verify (fail-closed) + SHA256 manifest + deploy dry-run/apply (marker `.aios/deploy.json` merge, exclude `.aios` khỏi manifest) |
| CLI | `backend/src/aios_core/workflow/cli.py` | `aiagent skill distill <url> --out` + `aiagent deploy --static <dir> [--apply]` |
| Test | `backend/tests/test_m11_p4.py` | 18 tests (R5/R7) |
