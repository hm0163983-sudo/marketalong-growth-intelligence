"""Transparent 0-100 scoring. Every factor stored separately for audit."""
from __future__ import annotations

from .config_loader import scoring as scoring_cfg
from .models import Finding


def _clamp(v: float, hi: float) -> int:
    return int(max(0, min(hi, round(v))))


def score(f: Finding) -> Finding:
    cfg = scoring_cfg()
    w = cfg["weights"]
    core = set(cfg.get("core_verticals", []))

    is_core = bool(set(f.verticals) & core)
    is_risk = f.ftype in ("risk", "regulation")
    is_update = f.ftype in ("platform_update", "tool_update")
    is_competitor = f.ftype == "competitor_move"

    factors = {
        # revenue: opportunities/updates in core verticals carry more
        "revenue_potential": _clamp(
            w["revenue_potential"] * (0.8 if (is_update or f.ftype == "opportunity") and is_core
                                      else 0.5 if is_core else 0.3), w["revenue_potential"]),
        "strategic_relevance": _clamp(
            w["strategic_relevance"] * (1.0 if is_core else 0.4 if f.verticals else 0.2),
            w["strategic_relevance"]),
        "urgency": _clamp(f.urgency, w["urgency"]),  # urgency already 0..15
        "competitive_advantage": _clamp(
            w["competitive_advantage"] * (1.0 if is_competitor else 0.7 if is_update and is_core else 0.3),
            w["competitive_advantage"]),
        "ease_of_implementation": _clamp(
            w["ease_of_implementation"] * (0.7 if is_update else 0.5), w["ease_of_implementation"]),
        "risk_of_ignoring": _clamp(
            w["risk_of_ignoring"] * (1.0 if is_risk else 0.6 if is_competitor else 0.3),
            w["risk_of_ignoring"]),
        "source_confidence": _clamp(w["source_confidence"] * (f.confidence / 10), w["source_confidence"]),
    }
    f.score_factors = factors
    raw = sum(factors.values())
    # Decisions over volume: a generic post with no event keyword is just noise.
    # Dampen market_signal so only real updates/risks/competitor/opportunity moves clear the bar.
    f.score = int(round(raw * 0.55)) if f.ftype == "market_signal" else raw

    # separate risk score 0..100
    sev = {"risk": 70, "regulation": 65, "competitor_move": 45}.get(f.ftype, 10)
    f.risk_score = _clamp(sev + f.urgency + (f.confidence), 100)

    b = cfg["bands"]
    f.band = ("critical" if f.score >= b["critical"]
              else "high" if f.score >= b["high"]
              else "watchlist" if f.score >= b["watchlist"]
              else "low_signal")
    return f


def is_critical_alert(f: Finding) -> bool:
    cfg = scoring_cfg()["critical_alert"]
    return f.score >= cfg["min_score"] and f.tier <= cfg["min_source_confidence_tier"]
