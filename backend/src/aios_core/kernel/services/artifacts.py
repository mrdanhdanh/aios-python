"""Artifact service: store/load/delete/list artifacts on the filesystem."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from ...contracts import ArtifactContract, ArtifactType
from ...logging import get_logger
from ..events import Event, EventBus, EventType

logger = get_logger("aios.kernel.services.artifacts")


class ArtifactCorruptedError(Exception):
    """Raised when an artifact's checksum does not match its content."""


class ArtifactService:
    """Persist artifacts as files + JSON sidecar metadata.

    Path guard: every stored/loaded/deleted path must resolve inside base_dir.
    """

    def __init__(self, base_dir: Path | str, bus: EventBus) -> None:
        self._base_dir = Path(base_dir)
        self._bus = bus

    def _resolve(self, storage_path: str) -> Path:
        path = Path(storage_path)
        if not path.is_absolute():
            path = self._base_dir / path
        resolved = path.resolve()
        if not resolved.is_relative_to(self._base_dir.resolve()):
            raise ValueError(f"storage_path escapes artifact base dir: {storage_path!r}")
        return resolved

    def store(self, contract: ArtifactContract, content: bytes) -> ArtifactContract:
        """Write content + sidecar; always recompute checksum (overwrites)."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        target = self._resolve(contract.storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        checksum = hashlib.sha256(content).hexdigest()
        contract.checksum = checksum
        # model_copy would be cleaner; mutate in place per spec (R3-3 note).
        contract.updated = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)

        target.write_bytes(content)
        self._write_sidecar(target, contract)

        self._bus.publish(
            Event(
                type=EventType.ARTIFACT_CREATED,
                payload={"artifact": contract.model_dump(mode="json")},
                source="artifact_service",
            )
        )
        return contract

    def _sidecar_path(self, target: Path) -> Path:
        return Path(str(target) + ".aios.json")

    def _write_sidecar(self, target: Path, contract: ArtifactContract) -> None:
        sidecar = self._sidecar_path(target)
        sidecar.write_text(json.dumps(contract.model_dump(mode="json"), default=str), encoding="utf-8")

    def load(self, contract: ArtifactContract) -> bytes:
        target = self._resolve(contract.storage_path)
        if not target.is_file():
            raise FileNotFoundError(f"artifact not found: {target}")
        content = target.read_bytes()
        if contract.checksum is not None:
            actual = hashlib.sha256(content).hexdigest()
            if actual != contract.checksum:
                raise ArtifactCorruptedError(
                    f"checksum mismatch for {target}: expected {contract.checksum}, got {actual}"
                )
        return content

    def delete(self, contract: ArtifactContract) -> None:
        target = self._resolve(contract.storage_path)
        target.unlink(missing_ok=True)
        sidecar = self._sidecar_path(target)
        sidecar.unlink(missing_ok=True)

    def list(self, artifact_type: ArtifactType | None = None) -> list[ArtifactContract]:
        if not self._base_dir.is_dir():
            return []
        contracts: list[ArtifactContract] = []
        for sidecar in self._base_dir.rglob("*.aios.json"):
            try:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
                contract = ArtifactContract.model_validate(data)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Skipping corrupt artifact sidecar %s: %s", sidecar, exc)
                continue
            if artifact_type is None or contract.type == artifact_type:
                contracts.append(contract)
        return contracts
