"""Generate a ready-to-paste Billion Dollar Team Strategic Council Input Pack.
Packages verified facts only. No fake strategic opinions, no invented numbers."""
from __future__ import annotations

from .models import Finding

ADVISORS = {
    "ai_automation": ["Alex Hormozi (offer/packaging)", "Russell Brunson (funnel)", "Gary Vee (attention)"],
    "digital_marketing": ["Dan Kennedy (direct response)", "Gary Vee (content)", "Russell Brunson (conversion)"],
    "app_development": ["Seth Godin (differentiation)", "Alex Hormozi (offer)", "Tony Robbins (execution)"],
    "marketverse": ["Seth Godin (category)", "Russell Brunson (value ladder)", "Grant Cardone (sales volume)"],
    "ventures": ["Tony Robbins (RPM)", "Seth Godin (purple cow)", "Alex Hormozi (economics)"],
}
DEFAULT_ADVISORS = ["Alex Hormozi (offer)", "Grant Cardone (sales)", "Tony Robbins (execution)"]


def select_advisors(f: Finding) -> list[str]:
    for v in f.verticals:
        if v in ADVISORS:
            return ADVISORS[v]
    return DEFAULT_ADVISORS


def build_pack(f: Finding) -> str:
    advisors = select_advisors(f)
    verts = ", ".join(f.verticals) or "general"
    return f"""## MarketAlong Strategic Council Input Pack

### Business Situation
A {f.ftype.replace('_', ' ')} was detected by the automated intelligence engine and scored {f.score}/100 ({f.band}).

### Relevant Numbers
- Score: {f.score}/100 | Risk score: {f.risk_score}/100 | Source confidence: {f.confidence}/10
- (No verified market/demand numbers available — do not assume any.)

### What Changed
{f.title}
{f.summary[:400]}

### Why It Matters
This affects MarketAlong verticals: {verts}. It may shift client needs, competitor positioning, or delivery tooling.

### MarketAlong Vertical Affected
{verts}

### Options Being Considered
1. Build a productized offer responding to this change.
2. Watch and validate with 3 client conversations before investing.
3. Ignore as low-impact noise.

### Weak Assumptions to Challenge
- That demand exists without validation.
- That MarketAlong must respond immediately.
- That competitors will move the same way.

### Selected Strategic Perspectives
{chr(10).join('- ' + a for a in advisors)}

### Required Output
1. Root cause analysis
2. Best option and why
3. Risks of each option
4. Three actions to complete today
5. Seven-day execution plan
6. Metrics to track
7. Stop/continue decision rule

### Evidence Links
- {f.source}: {f.url}
"""


def pick_for_council(findings: list[Finding], min_score: int = 70) -> Finding | None:
    candidates = [f for f in findings if f.score >= min_score]
    return max(candidates, key=lambda x: x.score) if candidates else None
