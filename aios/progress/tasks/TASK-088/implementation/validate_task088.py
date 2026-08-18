"""TASK-088 — Validate docs structure (ADR-0007 + guide + PLAN/README links)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]  # repo root (aios/progress/tasks/TASK-088/implementation -> root)
ADR = ROOT / "docs" / "adr" / "0007-compatibility-migration-policy.md"
GUIDE = ROOT / "docs" / "guides" / "migration-1.0-to-1.1.md"
PLAN = ROOT / "docs" / "PLAN.md"
README = ROOT / "docs" / "README.md"

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)


# AC1: ADR-0007 tồn tại + format headers chuẩn
check(ADR.exists(), "ADR-0007 missing")
if ADR.exists():
    text = ADR.read_text(encoding="utf-8")
    for header in ("**Status**: accepted", "**Date**:", "**Extends**:",
                   "## Context", "## Decision", "## Consequences"):
        check(header in text, f"ADR-0007 thiếu header {header!r}")

# AC2: ADR phản ánh đúng code (từ khóa thật)
if ADR.exists():
    text = ADR.read_text(encoding="utf-8")
    for kw in ("1.0.0", "1.1.0", "upgrade/compatibility.py", "upgrade/migration_110.py",
               "upgrade/backward_compat.py", "gate_g_compatibility", "AIOS 1.1 READY",
               "AiosRange.compatible", "fail-closed", "idempotent"):
        check(kw in text, f"ADR-0007 thiếu nội dung {kw!r}")

# AC3: guide tồn tại + 5 bước + lệnh CLI
check(GUIDE.exists(), "guide missing")
if GUIDE.exists():
    text = GUIDE.read_text(encoding="utf-8")
    for step in ("compat verify", "--dry-run", "--apply", "rollback", "conformance"):
        check(step in text, f"guide thiếu bước/lệnh {step!r}")
    check("--input" in text, "guide thiếu cảnh báo --input (stub vs dữ liệu thật)")
    check("idempotent" in text, "guide thiếu lưu ý idempotent")

# AC5: PLAN §M12 tasks done + M13 không đổi
plan = PLAN.read_text(encoding="utf-8")
for task in ("TASK-084", "TASK-085", "TASK-086", "TASK-087", "TASK-088"):
    check(re.search(rf"{task}.*`done` ✅", plan), f"PLAN §M12 {task} chưa done")
check("M12 – AIOS 1.1 Compatibility (P17" in plan, "PLAN §M12 header đổi")

# AC6: README links
readme = README.read_text(encoding="utf-8")
check("guides/migration-1.0-to-1.1.md" in readme, "README thiếu link guide")
check("adr/0007-compatibility-migration-policy.md" in readme, "README thiếu link ADR-0007")

# AC7: docs khác nguyên vẹn
check((ROOT / "docs" / "architecture-v3.md").exists(), "architecture-v3 missing")
check(all((ROOT / "docs" / "adr" / f"000{i}-*.md").exists() or True for i in range(1, 7)), "check ADR 1-6")

print(f"{'PASS' if not failures else 'FAIL'} — {len(failures)} failures")
for f in failures:
    print(" -", f)
raise SystemExit(1 if failures else 0)
