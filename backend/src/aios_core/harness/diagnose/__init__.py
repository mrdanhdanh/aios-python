"""Diagnose module (M14-P0, TASK-094): failure corpus + signature + localization."""

from .contracts import FailureCorpusReport, FailureRecord, FailureSeverity
from .engine import DiagnoseEngine
from .errors import DiagnoseError
from .harness import DiagnoseHarness

__all__ = [
    "FailureCorpusReport",
    "FailureRecord",
    "FailureSeverity",
    "DiagnoseEngine",
    "DiagnoseError",
    "DiagnoseHarness",
]
