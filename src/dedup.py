"""Dedup without paid vector DB. URL fingerprint + difflib title similarity."""
from __future__ import annotations

from difflib import SequenceMatcher

from .models import Finding

TITLE_SIM_THRESHOLD = 0.86


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def filter_new(findings: list[Finding], seen_fingerprints: set[str]) -> tuple[list[Finding], set[str]]:
    """Drop anything already seen (by fingerprint) or near-duplicate within this batch.
    Returns (new_findings, updated_seen)."""
    seen = set(seen_fingerprints)
    kept: list[Finding] = []
    for f in findings:
        fp = f.fingerprint
        if fp in seen:
            continue
        # near-duplicate title vs already-kept this run (same event, diff source)
        if any(_similar(f.title, k.title) >= TITLE_SIM_THRESHOLD for k in kept):
            seen.add(fp)
            continue
        kept.append(f)
        seen.add(fp)
    return kept, seen
