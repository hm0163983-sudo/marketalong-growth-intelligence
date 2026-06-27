"""Deterministic keyword classification. No LLM."""
from __future__ import annotations

from .config_loader import keywords
from .models import Finding


def _haystack(f: Finding) -> str:
    return f"{f.title}\n{f.summary}".lower()


def classify(f: Finding) -> Finding:
    kw = keywords()
    text = _haystack(f)
    hits: list[str] = []

    # verticals (keep any seeded by the source, add keyword matches)
    verts = set(f.verticals)
    for vert, words in kw.get("verticals", {}).items():
        for w in words:
            if w in text:
                verts.add(vert)
                hits.append(w)
    f.verticals = sorted(verts)

    # type: first matching category wins
    f.ftype = f.ftype if f.ftype in ("competitor_move",) else "market_signal"
    if f.ftype != "competitor_move":
        for ftype, words in kw.get("types", {}).items():
            if any(w in text for w in words):
                f.ftype = ftype
                break

    # urgency 0..15
    urg_words = kw.get("urgency_high", [])
    urg_hits = sum(1 for w in urg_words if w in text)
    f.urgency = min(15, urg_hits * 8) if urg_hits else (4 if f.ftype in ("platform_update", "risk", "regulation") else 0)

    # confidence 0..10 from tier (official = high)
    f.confidence = {1: 9, 2: 6, 3: 4}.get(f.tier, 4)

    f.keywords = sorted(set(hits))[:12]
    return f
