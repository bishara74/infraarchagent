"""Author restart helper: load private JSON into the child environment, never print it."""

import json
import os
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Usage: private-run.py PRIVATE_RUNTIME_JSON COMMAND [ARG ...]")
    state = Path(sys.argv[1]).resolve()
    if state.stat().st_mode & 0o077:
        raise SystemExit("Private configuration must have mode 0600")
    values = json.loads(state.read_text())
    if not isinstance(values, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in values.items()
    ):
        raise SystemExit("Invalid private runtime configuration")
    root = Path(__file__).resolve().parents[2]
    os.chdir(root / "backend")
    command = sys.argv[2:]
    executable = Path(command[0])
    if not executable.is_absolute():
        command[0] = str(root / executable)
    os.execvpe(command[0], command, values)


if __name__ == "__main__":
    main()
