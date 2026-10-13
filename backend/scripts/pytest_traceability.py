"""Opt-in pytest collection plugin; fixtures and test bodies never execute."""

import json
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption("--traceability-output", required=False)


def pytest_collection_finish(session):
    destination = session.config.getoption("--traceability-output")
    if not destination:
        return
    rows = []
    for item in session.items:
        ids = [
            identifier
            for marker in item.iter_markers("req")
            for identifier in marker.args
        ]
        rows.append(
            {
                "framework": "pytest",
                "node_id": item.nodeid,
                "file": str(item.path),
                "ids": ids,
                "skip": bool(
                    item.get_closest_marker("skip") or item.get_closest_marker("skipif")
                ),
                "perf": bool(item.get_closest_marker("perf")),
            }
        )
    Path(destination).write_text(json.dumps(rows, indent=2) + "\n")
