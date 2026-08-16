"""Static Deploy — R7 (M11-P4b, TASK-083).

`aiagent deploy --static <dir>`: verify → SHA256 manifest → dry-run →
optional apply (marker `.aios/deploy.json`, không push thật — R7 optional).
Fail-closed (INV-035): dir thiếu/rỗng → BLOCKED; deploy luôn verify trước.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

_MARKER_DIR = ".aios"
_MARKER_FILE = "deploy.json"

_GITHUB_PAGES_HINT = (
    "Deploy hint: GitHub Pages CI (Node 20 + build + dọn node_modules) — "
    "xem proposal M11 §R7 (pages.yml pattern)."
)


class DeployReport(BaseModel):
    """Kết quả deploy (C2-03)."""

    model_config = ConfigDict(extra="forbid")

    dir: str
    status: str = "ok"  # ok | blocked
    files: int = 0
    total_bytes: int = 0
    total_sha256: str = ""
    marker: str = ""
    hint: str = ""


class StaticDeploy:
    """Verify + manifest + deploy (dry-run/apply) deterministic."""

    # -- verify ---------------------------------------------------------------

    def _iter_files(self, root: Path) -> list[Path]:
        """Toàn bộ file, LOẠI `.aios/` (deploy marker không tự đếm vào manifest)."""
        return [p for p in root.rglob("*") if p.is_file()
                and _MARKER_DIR not in p.parts]

    def verify(self, dir_path: str | Path) -> DeployReport:
        """Dir hợp lệ: tồn tại + ≥1 file + (index.html OR bytes>0).

        Fail-closed (INV-035): dir thiếu/rỗng → BLOCKED (không bao giờ OK).
        """
        root = Path(dir_path)
        if not root.exists() or not root.is_dir():
            return DeployReport(dir=str(root), status="blocked",
                                hint="directory missing")
        files = self._iter_files(root)
        if not files:
            return DeployReport(dir=str(root), status="blocked",
                                hint="directory empty")
        total_bytes = sum(p.stat().st_size for p in files)
        has_index = (root / "index.html").exists()
        if not has_index and total_bytes <= 0:
            return DeployReport(dir=str(root), status="blocked",
                                hint="no index.html and empty artifacts")
        report = self.manifest(root)
        report.hint = _GITHUB_PAGES_HINT
        return report

    # -- manifest -------------------------------------------------------------

    def manifest(self, dir_path: str | Path) -> DeployReport:
        """SHA256 từng file + tổng (byte-identical, deterministic)."""
        root = Path(dir_path)
        files = sorted(self._iter_files(root))
        total_bytes = 0
        hasher = hashlib.sha256()
        for p in files:
            data = p.read_bytes()
            total_bytes += len(data)
            hasher.update(data)
        return DeployReport(
            dir=str(root),
            status="ok",
            files=len(files),
            total_bytes=total_bytes,
            total_sha256=hasher.hexdigest(),
        )

    # -- deploy ---------------------------------------------------------------

    def deploy(self, dir_path: str | Path, dry_run: bool = True) -> DeployReport:
        """Deploy — luôn verify trước (fail-closed, C2-05).

        dry_run=True → không tạo gì; dry_run=False → marker `.aios/deploy.json`
        (merge không ghi đè nếu đã có — C1-03).
        """
        report = self.verify(dir_path)
        if report.status != "ok":
            return report  # BLOCKED — không apply
        if dry_run:
            report.hint = "dry-run — no files written. " + report.hint
            return report
        root = Path(dir_path)
        marker_dir = root / _MARKER_DIR
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker_path = marker_dir / _MARKER_FILE
        payload: dict = {
            "deployed_at_utc": "deterministic",
            "files": report.files,
            "total_bytes": report.total_bytes,
            "total_sha256": report.total_sha256,
        }
        # Merge không ghi đè: giữ các key cũ chưa có
        if marker_path.exists():
            try:
                existing = json.loads(marker_path.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    payload = {**existing, **payload}
            except Exception:  # noqa: BLE001 — marker hỏng → ghi mới
                pass
        marker_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report.marker = str(marker_path)
        report.hint = "applied (marker written — static push thật ngoài scope R7)"
        return report
