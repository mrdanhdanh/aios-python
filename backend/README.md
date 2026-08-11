# aios-core

Backend core package for AIOS: configuration, logging, metadata, health checks.

## Development

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest            # from backend/
.venv/Scripts/python -m pytest tests      # from repo root: pytest backend/tests
```

Coverage gate: ≥ 80% on `aios_core` (enforced via `addopts`).

See [`docs/PLAN.md`](../docs/PLAN.md) for the full architecture.
