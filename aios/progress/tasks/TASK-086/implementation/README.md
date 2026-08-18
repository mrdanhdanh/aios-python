# TASK-086 — Implementation artifacts

## Deliverables

| File | Nội dung |
|------|----------|
| `backend/src/aios_core/upgrade/backward_compat.py` | **MỚI** — BackwardCompatibilitySuite: 9 check (5 kind: workflow×2, plugin×2, contract×2, extension×1, migrated×2), fail-closed bắt BaseException, `_NullSink` redirect stdout, fixtures v0 chuẩn |
| `backend/src/aios_core/plugins/contracts.py` | **FIX parse-only** — `AiosRange.compatible: list[str] = Field(default_factory=list)` (lỗ hổng do TASK-085: payload migrate không parse lại được) |
| `backend/src/aios_core/workflow/cli.py` | CLI `compat verify` (JSON 1 dòng, exit 0/1) |
| `backend/tests/test_architecture.py` | Allow-list + 7 module (kèm comment từng cái) |
| `backend/tests/test_backward_compat.py` | **MỚI** — 11 test (suite 9 check, fail-closed BaseException, AiosRange fix round-trip, CLI) |

## Kết quả

- Full suite: **2109 PASS / 0 FAIL** (2098 + 11 mới), coverage 92.98%
- CLI thật: `compat verify` → ok=true, 9/9 passed, exit 0; `compat list/check` không phá
- arch-health 0 violations · doctor healthy
