"""Fetch RSS/Atom feeds. Never crash the run on one bad source."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser

from ..models import Finding

log = logging.getLogger("collectors.rss")

UA = "MarketAlongGrowthIntel/1.0 (+https://marketalong.example; research bot; contact hmehta4851@gmail.com)"


def _published(entry) -> str:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except (TypeError, ValueError):
                pass
    return ""


def fetch_source(src: dict) -> tuple[list[Finding], dict]:
    """Return (findings, health). health is always returned, even on failure."""
    name, url = src.get("name", "?"), src.get("url", "")
    health = {"source": name, "url": url, "ok": False, "count": 0, "error": "",
              "run_at": datetime.now(timezone.utc).isoformat()}
    try:
        feed = feedparser.parse(url, agent=UA)
        if feed.bozo and not feed.entries:
            raise RuntimeError(str(feed.get("bozo_exception", "parse error")))
        out = []
        for e in feed.entries[:40]:
            summary = (e.get("summary") or e.get("description") or "")[:1000]
            out.append(Finding(
                title=(e.get("title") or "").strip(),
                url=(e.get("link") or "").strip(),
                summary=summary,
                source=name,
                tier=int(src.get("tier", 3)),
                published=_published(e),
                verticals=list(src.get("verticals", [])),  # seed hint; classifier may add more
            ))
        health.update(ok=True, count=len(out))
        return out, health
    except Exception as exc:  # noqa: BLE001 - one source must not kill the batch
        log.warning("source failed: %s -> %s", name, exc)
        health["error"] = str(exc)[:300]
        return [], health


def collect_all(sources: list[dict]) -> tuple[list[Finding], list[dict]]:
    findings, health = [], []
    for src in sources:
        f, h = fetch_source(src)
        findings.extend(f)
        health.append(h)
    return findings, health
