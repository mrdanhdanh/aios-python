"""DSH Bridge errors (M16)."""

from ..errors import HarnessError


class DSHBridgeError(HarnessError):
    """DSH bridge error — dsh not configured or unreachable."""
