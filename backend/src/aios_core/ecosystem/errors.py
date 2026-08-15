"""Ecosystem errors (TASK-046..TASK-049, M8-E4..E7)."""


class EcosystemError(Exception):
    """Base error for the AIOS ecosystem subsystem."""


class RegistryError(EcosystemError):
    """Raised on registry misuse (malformed entry, bad query)."""


class DevKitError(EcosystemError):
    """Raised on scaffold generation errors."""


class CertificationError(EcosystemError):
    """Raised on certification misuse."""


class MarketplaceError(EcosystemError):
    """Raised on marketplace trust-chain failures (carries ``step``)."""

    def __init__(self, message: str, step: str | None = None) -> None:
        super().__init__(message)
        self.step = step
