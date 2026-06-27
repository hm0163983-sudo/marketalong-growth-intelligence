"""Structured risk cards from risk/regulation/competitor findings."""
from __future__ import annotations

from .models import Finding


def build(f: Finding) -> dict | None:
    if f.ftype not in ("risk", "regulation", "competitor_move"):
        return None
    status = "act" if f.risk_score >= 75 else "monitor" if f.risk_score >= 45 else "ignore"
    return {
        "title": f.title[:140],
        "vertical": ", ".join(f.verticals) or "general",
        "severity": f.risk_score,
        "probability": "high" if f.tier == 1 else "medium",
        "why": f"{f.ftype} from {f.source} may affect delivery/visibility/margins.",
        "evidence": f.url,
        "mitigation": (
            "Audit affected client setups; prep migration/comms plan."
            if f.ftype != "competitor_move"
            else "Review competitor change; counter-position offer if needed."
        ),
        "status": status,
    }


def build_all(findings: list[Finding]) -> list[dict]:
    out = [build(f) for f in findings]
    return [r for r in out if r and r["status"] != "ignore"]
