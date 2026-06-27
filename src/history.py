"""Durable finding history for weekly/monthly rollups. JSONL committed by the workflow.
No DB. Capped so it never grows unbounded."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .models import Finding

HIST = Path(__file__).resolve().parent.parent / "output" / "history.jsonl"
MAX_ROWS = 2000

_FIELDS = ("title", "url", "summary", "source", "tier", "ftype", "verticals",
           "score", "risk_score", "band", "gap_id", "confidence", "collected_at")


def append(findings: list[Finding]) -> None:
    HIST.parent.mkdir(parents=True, exist_ok=True)
    new = [json.dumps({k: getattr(f, k) for k in _FIELDS}, ensure_ascii=False) for f in findings]
    existing = HIST.read_text(encoding="utf-8").splitlines() if HIST.exists() else []
    rows = existing + new
    HIST.write_text("\n".join(rows[-MAX_ROWS:]) + "\n", encoding="utf-8")


def load_findings(days: int) -> list[Finding]:
    """Rebuild Findings from the last `days` of history."""
    if not HIST.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: list[Finding] = []
    for line in HIST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = d.get("collected_at", "")
        try:
            if ts and datetime.fromisoformat(ts) < cutoff:
                continue
        except ValueError:
            pass
        out.append(Finding(
            title=d.get("title", ""), url=d.get("url", ""), summary=d.get("summary", ""),
            source=d.get("source", ""), tier=d.get("tier", 2), ftype=d.get("ftype", "market_signal"),
            verticals=d.get("verticals", []), score=d.get("score", 0), risk_score=d.get("risk_score", 0),
            band=d.get("band", "watchlist"), gap_id=d.get("gap_id", ""), confidence=d.get("confidence", 5),
            collected_at=ts,
        ))
    return out
