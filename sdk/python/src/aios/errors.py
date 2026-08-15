class SDKError(Exception):
    """Base error raised by the public SDK boundary."""


class ContractError(SDKError, ValueError):
    """A public component or DTO violates its contract."""
