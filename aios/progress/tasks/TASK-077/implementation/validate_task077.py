"""TASK-077 test script — validate issue templates, PR template, workflow, docs.

Usage: python validate_task077.py
Chạy từ repo root (hoặc đổi ROOT bên dưới).
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(r"c:\Users\nguye\OneDrive\Desktop\AIAGENT")
PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS | {name} {detail}")
    else:
        FAIL += 1
        print(f"  FAIL | {name} {detail}")


def load_yaml(rel):
    with open(ROOT / rel, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------- T1: YAML parse
print("== T1: YAML parse ==")
TEMPLATES = ["bug-report.yml", "feature-upgrade.yml", "idea-proposal.yml"]
for t in TEMPLATES:
    try:
        load_yaml(f".github/ISSUE_TEMPLATE/{t}")
        check(f"parse {t}", True)
    except Exception as e:  # noqa: BLE001
        check(f"parse {t}", False, str(e))
try:
    cfg = load_yaml(".github/ISSUE_TEMPLATE/config.yml")
    check("parse config.yml", True)
except Exception as e:  # noqa: BLE001
    check("parse config.yml", False, str(e))
    cfg = {}
try:
    wf = load_yaml(".github/workflows/pr-validation.yml")
    check("parse pr-validation.yml", True)
except Exception as e:  # noqa: BLE001
    check("parse pr-validation.yml", False, str(e))
    wf = {}

# ---------------------------------------------------------------- T2: schema assertions
print("== T2: schema assertions (AC1 + workflow) ==")
ALLOWED_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes"}
for t in TEMPLATES:
    d = load_yaml(f".github/ISSUE_TEMPLATE/{t}")
    check(f"{t}: name str <=80", isinstance(d.get("name"), str) and len(d["name"]) <= 80, repr(d.get("name")))
    check(f"{t}: about str <=190", isinstance(d.get("about"), str) and len(d["about"]) <= 190, repr(d.get("about")))
    check(f"{t}: labels str|list", "labels" in d and (isinstance(d["labels"], str) or isinstance(d["labels"], list)), repr(d.get("labels")))
    body = d.get("body")
    check(f"{t}: body list non-empty", isinstance(body, list) and len(body) > 0)
    types_ok = all(isinstance(el, dict) and el.get("type") in ALLOWED_TYPES for el in body or [])
    check(f"{t}: body types allowed", types_ok)
    req_ok = all(
        "validations" not in el or isinstance(el["validations"].get("required"), bool)
        for el in body or []
    )
    check(f"{t}: validations.required bool", req_ok)

# config.yml
check("config.yml: blank_issues_enabled is False", cfg.get("blank_issues_enabled") is False)
check("config.yml: contact_links list", isinstance(cfg.get("contact_links"), list) and len(cfg["contact_links"]) > 0)

# workflow
check("workflow: name present", isinstance(wf.get("name"), str) and "PR" in wf["name"])
# PyYAML quirk: key `on` parse thành boolean True (YAML 1.1)
on_key = wf.get("on") if "on" in wf else wf.get(True)
check("workflow: on present (quirk True)", on_key is not None)
pr_types = (on_key or {}).get("pull_request", {}).get("types")
expected_types = {"opened", "edited", "synchronize", "reopened", "ready_for_review"}
check("workflow: pull_request types", pr_types is not None and set(pr_types) == expected_types, str(pr_types))
check("workflow: jobs.validate exists", isinstance(wf.get("jobs", {}).get("validate"), dict))
check("workflow: permissions read-only", wf.get("permissions") == {"contents": "read", "issues": "read"}, str(wf.get("permissions")))
check("workflow: concurrency group", "concurrency" in wf and "group" in wf["concurrency"])
check("workflow: uses github-script@v7", "actions/github-script@v7" in str(wf))

# PR template
prt = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
check("PR template: has issue section", "Issue liên quan" in prt and "Fixes #N" in prt)
check("PR template: has [bypass] section", "[bypass]" in prt)
check("PR template: has checklist", "Checklist" in prt)

# ---------------------------------------------------------------- T3: decision-flow simulation
print("== T3: decision-flow simulation (>=14 cases) ==")


def simulate(title, body, base, draft=False):
    """Mô phỏng chính xác luồng 7 bước trong pr-validation.yml."""
    re_release = re.compile(r"^release: verify \u2192 master")
    re_issue = re.compile(r"^(feature|fix|docs|operation|refactor|test)/ISSUE-\d+")
    re_bypass = re.compile(r"^(feature|fix|docs|operation|refactor|test)/(bypass|hotfix)-[a-z0-9-]+")
    re_link = re.compile(r"(?:#\d+|ISSUE-\d+)")
    re_bypass_tag = re.compile(r"\[bypass\]", re.IGNORECASE)

    if draft:
        return "pass", "draft"
    if re_release.match(title):
        if base != "master":
            return "fail", "release-base"
        return "pass", "release"
    if base != "verify":
        return "fail", "base"
    if re_bypass_tag.search(body):
        return "pass", "bypass-body"
    if re_issue.match(title):
        if not re_link.search(body):
            return "fail", "issue-no-link"
        return "pass", "issue"
    if re_bypass.match(title):
        return "fail", "bypass-title-no-tag"
    return "fail", "title-format"


CASES = [
    # (title, body, base, draft, expected_result, expected_reason, label)
    ("feature/ISSUE-5: add tab", "Fixes #5", "verify", False, "pass", "issue", "1a ISSUE title + link"),
    ("feature/ISSUE-5: add tab", "Fixes #5", "master", False, "fail", "base", "1b base master -> fail"),
    ("fix/ISSUE-2: login timeout", "Refs #2", "verify", False, "pass", "issue", "2a fix ISSUE + Refs"),
    ("fix/ISSUE-2: login timeout", "mô tả", "verify", False, "fail", "issue-no-link", "2b ISSUE title thiếu link"),
    ("release: verify \u2192 master (2026-08-16)", "Issues included: #5", "master", False, "pass", "release", "3a promotion base master"),
    ("release: verify \u2192 master (2026-08-16)", "", "verify", False, "fail", "release-base", "3b promotion base verify -> fail"),
    ("docs/ISSUE-3: workflow docs", "Refs #3", "verify", False, "pass", "issue", "4a docs ISSUE"),
    ("docs/ISSUE-3: workflow docs", "", "verify", False, "fail", "issue-no-link", "4b docs thiếu link"),
    ("fix/bypass-typo: sửa typo", "thêm [bypass] vì fix nhỏ", "verify", False, "pass", "bypass-body", "5a bypass title + tag"),
    ("fix/bypass-typo: sửa typo", "không có tag", "verify", False, "fail", "bypass-title-no-tag", "5b bypass title thiếu tag"),
    ("fix/bypass-typo: sửa typo", "[bypass] lý do", "master", False, "fail", "base", "5c bypass + base master -> base fail trước"),
    ("whatever: title lạ", "[bypass] dogfood", "verify", False, "pass", "bypass-body", "6a body [bypass] override title"),
    ("xyz/ISSUE-9: sai prefix", "Fixes #9", "verify", False, "fail", "title-format", "6b prefix không hợp lệ"),
    ("", "", "verify", False, "fail", "title-format", "6c title trống"),
    ("feature/ISSUE-5: wip", "Fixes #5", "verify", True, "pass", "draft", "7a draft skip"),
    ("hotfix/bypass-urgent: fix nhanh", "[bypass] khẩn cấp", "verify", False, "pass", "bypass-body", "7b hotfix bypass"),
    ("operation/ISSUE-12: chạy thử", "Refs #12", "verify", False, "pass", "issue", "7c operation prefix"),
    ("refactor/ISSUE-7: di", "link #7", "verify", False, "pass", "issue", "7d #N trần vẫn pass (giới hạn đã biết)"),
    ("test/ISSUE-8: thêm test", "Fixes #8", "verify", False, "pass", "issue", "7e test prefix"),
    ("feature/ISSUE-5: x", "Fixes #5", "master", True, "pass", "draft", "8 draft ưu tiên hơn base"),
]
ok_cases = 0
for title, body, base, draft, exp, exp_reason, label in CASES:
    got, reason = simulate(title, body, base, draft)
    ok = got == exp and reason == exp_reason
    ok_cases += ok
    check(f"case {label}", ok, f"got=({got},{reason}) exp=({exp},{exp_reason})")
check(">=14 cases", len(CASES) >= 14, f"{len(CASES)} cases")
check("100% cases pass", ok_cases == len(CASES), f"{ok_cases}/{len(CASES)}")

# ---------------------------------------------------------------- T4: docs structure
print("== T4: docs structure (AC5/AC6/AC7/AC8) ==")
wfdoc = (ROOT / "docs/workflows/issue-pr-workflow.md").read_text(encoding="utf-8")
for h in ["Giai đoạn 1", "Giai đoạn 2", "Giai đoạn 3", "Giai đoạn 4", "Giai đoạn 5",
          "Quy ước tên nhánh", "Sơ đồ tổng thể", "gh auth", "setup-git", "Tham chiếu"]:
    check(f"workflow doc: {h}", h in wfdoc)

adr = (ROOT / "docs/adr/0006-issue-pr-workflow.md").read_text(encoding="utf-8")
for h in ["**Status**: accepted", "## Context", "## Decision", "## Consequences", "ADR-0005", "master"]:
    check(f"ADR-0006: {h}", h in adr)

agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
check("AGENTS.md: §4.2", "4.2. Issue-Driven Development" in agents)
check("AGENTS.md: ADR-0006 link", "ADR-0006" in agents)

plan = (ROOT / "docs/PLAN.md").read_text(encoding="utf-8")
check("PLAN.md: ADR-0006 link", "0006-issue-pr-workflow" in plan)
check("PLAN.md: workflow docs link", "issue-pr-workflow.md" in plan)

prt = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
check("PR template tồn tại", len(prt) > 100)

print(f"\n== KẾT QUẢ: {PASS} PASS, {FAIL} FAIL ==")
sys.exit(1 if FAIL else 0)
