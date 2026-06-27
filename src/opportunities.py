"""Turn strong, non-risk findings into structured opportunity cards.
Template-driven. Never invents demand numbers."""
from __future__ import annotations

from .models import Finding

NO_DEMAND = "Demand evidence incomplete — validate before investment."

VERTICAL_OFFER = {
    "ai_automation": ("Productized AI automation setup (CRM/lead-nurture workflow)", "₹25k–₹1.5L"),
    "digital_marketing": ("Done-for-you campaign refresh aligned to the platform change", "₹20k–₹1L"),
    "app_development": ("Rapid build/integration using the new tool/SDK", "₹50k–₹4L"),
    "marketverse": ("New service listing / template productized around the trend", "₹2k–₹40k"),
    "shop": ("Store feature/upsell flow upgrade", "₹10k–₹60k"),
    "media": ("Content/video package built on the trend", "₹10k–₹50k"),
    "studio": ("Branded creative kit around the new format", "₹8k–₹40k"),
    "ventures": ("Validation experiment / micro-launch", "experiment budget"),
}


def build(f: Finding) -> dict | None:
    if f.ftype in ("risk", "regulation") or f.band == "low_signal":
        return None
    vert = next((v for v in f.verticals if v in VERTICAL_OFFER), None)
    if not vert:
        return None
    offer, price = VERTICAL_OFFER[vert]
    rec = "pursue" if f.band in ("critical", "high") else "watch"
    return {
        "name": f"{offer} (triggered by: {f.title[:80]})",
        "vertical": vert,
        "trigger": f.source,
        "trigger_url": f.url,
        "customer_problem": f"Clients in {vert} now need to adapt to: {f.title[:120]}",
        "suggested_offer": offer,
        "why_now": f.title[:160],
        "suggested_price": price,
        "demand": NO_DEMAND,
        "launch_speed": "fast" if f.ftype in ("tool_update", "platform_update") else "medium",
        "main_risk": "Adoption uncertain; validate with 3 client conversations first.",
        "validation_plan": "Pitch to 3 existing clients this week; build only on a paid pilot.",
        "recommendation": rec,
        "score": f.score,
    }


def build_all(findings: list[Finding]) -> list[dict]:
    out = [build(f) for f in findings]
    return [o for o in out if o]
