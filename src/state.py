"""Durable run-state without a DB. JSON file committed back by the workflow.
Holds dedup fingerprints (capped) + competitor page hashes."""
from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "output" / "state.json"
MAX_FINGERPRINTS = 5000


def load() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"seen": [], "competitor_hashes": {}}


def save(seen: set[str], competitor_hashes: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    seen_list = list(seen)[-MAX_FINGERPRINTS:]  # cap so file never grows unbounded
    STATE_PATH.write_text(
        json.dumps({"seen": seen_list, "competitor_hashes": competitor_hashes}, indent=2),
        encoding="utf-8",
    )
