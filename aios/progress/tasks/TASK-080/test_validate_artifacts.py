#!/usr/bin/env python3
"""TASK-080 validate: parse + schema-check skill manifests & catalog entries.

Chạy: backend/.venv/Scripts/python aios/progress/tasks/TASK-080/test_validate_artifacts.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # -> AIAGENT repo root
SKILLS = ROOT / "skills"
CATALOG = ROOT / "catalog"

VALID_SOURCES = {"zip", "git", "pip"}
REQUIRED_MANIFEST_KEYS = {
    "id", "name", "version", "source", "description",
    "dependencies", "capabilities", "permissions", "metadata",
}

errors: list[str] = []


def semver_ok(v: str) -> bool:
    parts = v.split(".")
    return len(parts) == 3 and all(p.isdigit() for p in parts)


def check_manifest(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_MANIFEST_KEYS - data.keys()
    if missing:
        errors.append(f"{path}: thiếu key {missing}")
    if data.get("source") not in VALID_SOURCES:
        errors.append(f"{path}: source phải ∈ {VALID_SOURCES}, got {data.get('source')!r}")
    if not semver_ok(str(data.get("version", ""))):
        errors.append(f"{path}: version không phải semver: {data.get('version')!r}")
    for list_key in ("capabilities", "permissions"):
        val = data.get(list_key)
        if not isinstance(val, list) or len(val) == 0:
            errors.append(f"{path}: {list_key} phải là list không rỗng")
    # extra=forbid: không được có key lạ (ngoại trừ cho phép)
    extra = set(data.keys()) - REQUIRED_MANIFEST_KEYS
    if extra:
        errors.append(f"{path}: key lạ (vi phạm extra=forbid): {extra}")
    if data.get("description", "").strip() == "":
        errors.append(f"{path}: description rỗng")
    print(f"  manifest OK: {path.name} (id={data['id']}, v={data['version']})")


def check_catalog(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "skill":
        errors.append(f"{path}: kind phải = 'skill', got {data.get('kind')!r}")
    if not data.get("id"):
        errors.append(f"{path}: id rỗng")
    if not isinstance(data.get("metadata"), dict):
        errors.append(f"{path}: metadata phải là dict")
    print(f"  catalog OK: {path.name} (id={data['id']})")


def main() -> int:
    print("== TASK-080 validation ==")
    for m in sorted(SKILLS.glob("*/manifest.json")):
        check_manifest(m)
    for c in sorted(CATALOG.glob("skill-*.json")):
        check_catalog(c)
    if errors:
        print("\nFAIL:")
        for e in errors:
            print("  -", e)
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
