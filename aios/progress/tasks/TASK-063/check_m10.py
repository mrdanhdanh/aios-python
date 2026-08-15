"""TASK-063 M10-F1 — test script: verify docs/architecture/* structure."""
import pathlib

root = pathlib.Path(r"c:\Users\nguye\OneDrive\Desktop\AIAGENT")
docs = root / "docs" / "architecture"
arch_test = (root / "backend" / "tests" / "test_architecture.py").read_text(encoding="utf-8")
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))


files = ["AIOS-1.0.md", "layer-model.md", "control-plane.md", "execution-plane.md",
         "autonomy.md", "constitution-1.0.md"]
for f in files:
    check(f"file {f}", (docs / f).exists())

lm = (docs / "layer-model.md").read_text(encoding="utf-8")
layers = ["UI / SDK / API", "AUTONOMY CONTROL", "ORCHESTRATOR",
          "WORKFLOW / AGENT / CAPABILITY", "RUNTIME KERNEL",
          "TOOLS / STATE / EVENTS", "INFRA"]
for i, l in enumerate(layers, 1):
    check(f"layer L{i} {l}", l in lm, "layer-model.md")

const = (docs / "constitution-1.0.md").read_text(encoding="utf-8")
missing = [f"INV-{n:03d}" for n in range(1, 35) if f"INV-{n:03d}" not in const]
check("constitution INV-001..034", not missing, f"missing: {missing}")

# AC4: every INV has enforcement test (test_inv0xx_* or test_m9_* for 030-034)
uncovered = []
for n in range(1, 35):
    lbl = f"inv{n:03d}"
    if lbl not in arch_test:
        if lbl in ("inv030", "inv031", "inv032", "inv033", "inv034") and "test_m9_" in arch_test:
            continue
        uncovered.append(lbl)
check("every INV enforced in test_architecture.py", not uncovered, f"uncovered: {uncovered}")

check("freeze declaration", "release blocker" in const)
check("renumber deferred", "AIOS 2.0" in const)

bad = []
for f in files + ["architecture-v2.md"]:
    p = docs / f if (docs / f).exists() else root / "docs" / f
    if p.exists() and "```mermaid" in p.read_text(encoding="utf-8"):
        bad.append(f)
check("no mermaid blocks", not bad, str(bad))

v2 = (root / "docs" / "architecture-v2.md").read_text(encoding="utf-8")
check("v2 has M10 section", "## 15. M10 — AIOS 1.0" in v2 and "constitution-1.0.md" in v2)

for name, ok, detail in results:
    print(("PASS" if ok else "FAIL"), "|", name, ("| " + detail if detail else ""))
print(f"\n{sum(1 for _, ok, _ in results if ok)}/{len(results)} PASS")
