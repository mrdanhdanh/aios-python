"""Model errors (hierarchy: specific errors subclass ModelError)."""


class ModelError(Exception):
    """Base error for model layer failures."""


class ModelNotAvailableError(ModelError):
    """Provider is not available (not installed / missing credentials)."""


class ModelTimeoutError(ModelError):
    """Provider call timed out."""


class ModelRateLimitError(ModelError):
    """Provider rate-limited the request (TASK-025 — fallback chain)."""


class RouterError(ModelError):
    """Model routing failure (TASK-025): unknown policy, no model, chain exhausted."""
