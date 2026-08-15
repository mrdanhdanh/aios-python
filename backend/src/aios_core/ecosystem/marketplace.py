"""Marketplace / Distribution (TASK-048, M8-E6).

Trust Model pipeline (PLAN §M8-E6):
    Download → Manifest validation → Signature verification → Dependency
    check → Permission analysis → Compatibility check → Security scan →
    Harness certification → Install.

Signatures are deterministic HMAC-SHA256 over the canonical manifest JSON —
trust chain v1 without heavy crypto. The raw signing key is NEVER serialized;
records keep only the key fingerprint.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from ..semver import compare, parse_version
from .certification import CertLevel, CertificationEngine
from .errors import MarketplaceError

_SIGNING_KEY_LEN = 64


class Publisher(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = ""
    signing_key_id: str = ""


class PackageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publisher_id: str
    name: str
    version: str
    manifest: dict
    signature: str


class InstallResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    step: str
    reason: str = ""
    cert_level: CertLevel = CertLevel.COMMUNITY


def canonical_json(manifest: dict) -> str:
    return json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sign_manifest(manifest: dict, key: str) -> str:
    """Deterministic HMAC-SHA256 hex signature over canonical JSON."""
    digest = hmac.new(key.encode("utf-8"), canonical_json(manifest).encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def verify_signature(manifest: dict, key: str, signature: str) -> bool:
    return hmac.compare_digest(sign_manifest(manifest, key), signature)


class TrustChain:
    """Nine-step install pipeline. Each failure carries the failing step."""

    STEPS = (
        "download", "manifest_validation", "signature_verification",
        "dependency_check", "permission_analysis", "compatibility_check",
        "security_scan", "harness_certification", "install",
    )

    def __init__(
        self,
        entry_resolver: Callable[[str], Any] | None = None,
        aios_version: str = "1.0.0",
    ) -> None:
        # Offline-first: dependencies resolve locally by default; a registry
        # lookup can be injected to enforce hard dependency checks.
        self._entry_resolver = entry_resolver or (lambda entry_id: entry_id)
        self._aios_version = aios_version

    def run(self, manifest: dict, signature: str, signing_key: str) -> InstallResult:
        # 1. download — caller has the package; nothing to verify here.
        # 2. manifest validation
        if not isinstance(manifest, dict) or not manifest.get("id") or not manifest.get("version"):
            return InstallResult(approved=False, step="manifest_validation",
                                 reason="manifest missing id/version")
        try:
            parse_version(str(manifest["version"]))
        except ValueError:
            return InstallResult(approved=False, step="manifest_validation",
                                 reason="invalid semver version")
        # 3. signature verification
        if not verify_signature(manifest, signing_key, signature):
            return InstallResult(approved=False, step="signature_verification",
                                 reason="signature mismatch")
        # 4. dependency check
        for dep in manifest.get("dependencies", []):
            dep_id = dep.split("@")[0]
            if self._entry_resolver(dep_id) is None:
                return InstallResult(approved=False, step="dependency_check",
                                     reason=f"missing dependency: {dep_id}")
        # 5. permission analysis
        permissions = manifest.get("permissions") or []
        if not permissions:
            return InstallResult(approved=False, step="permission_analysis",
                                 reason="no permissions declared")
        # 6. compatibility check (aios range)
        aios = manifest.get("aios") or {}
        lo, hi = aios.get("min", "0.0.0"), aios.get("max", "*")
        if not self._in_range(lo, hi):
            return InstallResult(approved=False, step="compatibility_check",
                                 reason=f"aios {self._aios_version} outside {lo}..{hi}")
        # 7. security scan (wildcard permission → hard fail)
        if any(perm == "*" for perm in permissions):
            return InstallResult(approved=False, step="security_scan",
                                 reason="wildcard permission '*'")
        # 8. harness certification
        report = CertificationEngine().certify(manifest)
        if report.level.value in ("community",):
            return InstallResult(approved=False, step="harness_certification",
                                 reason=f"certification failed ({report.failed} failed checks)")
        # 9. install
        return InstallResult(approved=True, step="install", cert_level=report.level)

    def _in_range(self, lo: str, hi: str) -> bool:
        try:
            have = parse_version(self._aios_version)
            if lo != "*":
                want = parse_version(str(lo))
                if compare(str(have), str(want)) < 0:
                    return False
            if hi != "*":
                raw = str(hi)
                if raw.endswith(".x"):
                    major = int(raw[:-2].split(".")[0])
                    if have.major > major:
                        return False
                else:
                    want = parse_version(raw)
                    if compare(str(have), str(want)) > 0:
                        return False
            return True
        except ValueError:
            return False


class MarketplaceRegistry:
    """Publisher + package records (SQLite). Raw keys never persisted."""

    def __init__(self, db_path: Path | str, event_sink: Callable[[str, dict], None] | None = None) -> None:
        self._db_path = Path(db_path)
        self._event_sink = event_sink
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS publishers (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '',
                    signing_key_id TEXT NOT NULL DEFAULT '', key_hash TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS packages (
                    publisher_id TEXT NOT NULL, name TEXT NOT NULL,
                    version TEXT NOT NULL, manifest_json TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    PRIMARY KEY (publisher_id, name)
                );
                """
            )

    def _emit(self, kind: str, payload: dict) -> None:
        if self._event_sink is None:
            return
        try:
            self._event_sink(kind, payload)
        except Exception:  # noqa: BLE001 — best-effort
            pass

    def register_publisher(self, publisher: Publisher, key: str) -> Publisher:
        if len(key) < _SIGNING_KEY_LEN:
            raise MarketplaceError("signing key must be at least 64 characters")
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO publishers (id, name, signing_key_id, key_hash)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT (id) DO UPDATE SET name=excluded.name,"
                " signing_key_id=excluded.signing_key_id, key_hash=excluded.key_hash",
                (publisher.id, publisher.name, publisher.signing_key_id or "",
                 key_hash),
            )
        return publisher

    def publish(self, publisher_id: str, key: str, manifest: dict) -> PackageRecord:
        """Sign + upsert a package under the publisher's key."""
        record = PackageRecord(
            publisher_id=publisher_id,
            name=str(manifest.get("name", manifest.get("id", "unknown"))),
            version=str(manifest.get("version", "0.0.0")),
            manifest=dict(manifest),
            signature=sign_manifest(manifest, key),
        )
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO packages (publisher_id, name, version, manifest_json, signature)"
                " VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (publisher_id, name) DO UPDATE SET version=excluded.version,"
                " manifest_json=excluded.manifest_json, signature=excluded.signature",
                (record.publisher_id, record.name, record.version,
                 json.dumps(record.manifest, ensure_ascii=False), record.signature),
            )
        return record

    def get_package(self, publisher_id: str, name: str) -> PackageRecord | None:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM packages WHERE publisher_id=? AND name=?",
                (publisher_id, name),
            ).fetchone()
        if row is None:
            return None
        return PackageRecord(
            publisher_id=row[0], name=row[1], version=row[2],
            manifest=json.loads(row[3]), signature=row[4],
        )

    def install_flow(self, publisher_id: str, name: str, key: str) -> InstallResult:
        """Trust chain over a published package; emits marketplace.installed."""
        record = self.get_package(publisher_id, name)
        if record is None:
            return InstallResult(approved=False, step="download",
                                 reason="package not found in marketplace")
        chain = TrustChain(
            entry_resolver=self._entry_lookup, aios_version=self._aios_version
        )
        result = chain.run(record.manifest, record.signature, key)
        if result.approved:
            self._emit("marketplace.installed",
                       {"publisher": publisher_id, "name": name,
                        "version": record.version})
        return result

    # -- injectable entry resolver --------------------------------------------

    def _entry_lookup(self, entry_id: str) -> Any:
        # v1: local entries treated as satisfied (offline-first marketplace).
        return entry_id

    @property
    def _aios_version(self) -> str:
        return "1.0.0"


__all__ = [
    "InstallResult",
    "MarketplaceRegistry",
    "PackageRecord",
    "Publisher",
    "TrustChain",
    "canonical_json",
    "sign_manifest",
    "verify_signature",
]
