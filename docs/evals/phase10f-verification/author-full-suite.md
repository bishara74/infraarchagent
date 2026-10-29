# Author-run full verification before v1.0

Run by the author on 2026-10-29 in a fresh terminal (no benchmark environment
variables), with the project PostgreSQL test database, after Phase 10f.

| Command | Result |
|---|---|
| `make test` | 2,865 passed, 0 failed, 6 deselected (performance), 473.8 s |
| `make frontend-test` | 469 passed in 46 files |
| `pytest tests/unit/test_phase9l_wire.py` | 48 passed |

An earlier attempt in a terminal that still exported the benchmark
environment (LLM_MODEL, PROVIDER_PREFERENCE, etc.) failed 37 golden-wire
tests; the tests correctly honour explicit environment variables. Rerun in a
clean terminal: all passed. Codex's `make-test.txt` in this folder stopped at
migrations because no test database was configured in its sandbox.
