"""Model errors (hierarchy: specific errors subclass ModelError)."""


class ModelError(Exception):
    """Base error for model layer failures."""


class ModelNotAvailableError(ModelError):
    """Provider is not available (not installed / missing credentials)."""


class ModelTimeoutError(ModelError):
    """Provider call timed out."""
