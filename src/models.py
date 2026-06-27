"""Core data shapes. Plain dataclasses — no heavy deps."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def canonical_url(url: str) -> str:
    """Strip tracking params + fragments so the same link dedupes."""
    if not url:
        return ""
    base = url.split("#", 1)[0]
    if "?" in base:
        head, query = base.split("?", 1)
        keep = [
            p for p in query.split("&")
            if p and not p.lower().startswith(("utm_", "ref=", "ref_", "fbclid", "gclid"))
        ]
        base = head + ("?" + "&".join(keep) if keep else "")
    return base.rstrip("/")


@dataclass
class Finding:
    title: str
    url: str = ""
    summary: str = ""
    source: str = ""
    tier: int = 3
    published: str = ""               # ISO string if known
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # filled by classifier / scorer
    verticals: list = field(default_factory=list)
    ftype: str = "market_signal"
    urgency: int = 0                  # 0..15 (pre-weighted urgency points)
    confidence: int = 0               # 0..10
    keywords: list = field(default_factory=list)
    score: int = 0
    risk_score: int = 0
    band: str = "low_signal"
    gap_id: str = ""
    score_factors: dict = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        cu = canonical_url(self.url)
        basis = cu if cu else (self.source + "|" + self.title.lower().strip())
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

    def to_row(self) -> list:
        return [
            self.collected_at, self.band, self.score, self.risk_score,
            self.ftype, ", ".join(self.verticals), self.source, self.tier,
            self.confidence, self.title, canonical_url(self.url),
            self.published, ", ".join(self.keywords[:8]),
        ]

    def as_dict(self) -> dict:
        return asdict(self)


ROW_HEADERS = [
    "collected_at", "band", "score", "risk_score", "type", "verticals",
    "source", "tier", "confidence", "title", "url", "published", "keywords",
]
