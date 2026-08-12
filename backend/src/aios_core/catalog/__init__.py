"""System catalog: metadata index for the whole system."""

from .catalog import CatalogEntry, SystemCatalog
from .errors import CatalogError

__all__ = ["CatalogEntry", "CatalogError", "SystemCatalog"]
