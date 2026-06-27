"""Daily competitor page change-watch via content hash. Zero-cost, polite."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from ..models import Finding

log = logging.getLogger("collectors.competitor")
UA = "MarketAlongGrowthIntel/1.0 (+research bot; research contact via repo owner)"
TIMEOUT = 20


def _meaningful_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    # focus on signal-bearing content, drop chrome
    parts = []
    for sel in ("h1", "h2", "h3", "title", "[class*=price]", "[class*=plan]", "main", "p"):
        for el in soup.select(sel):
            t = el.get_text(" ", strip=True)
            if t:
                parts.append(t)
    text = " ".join(parts)
    return " ".join(text.split())[:20000]


def check_url(name: str, url: str, prev_hash: str | None, verticals: list) -> tuple[Finding | None, dict]:
    health = {"competitor": name, "url": url, "ok": False, "changed": False,
              "hash": prev_hash or "", "error": "", "run_at": datetime.now(timezone.utc).isoformat()}
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        r.raise_for_status()
        text = _meaningful_text(r.text)
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        health.update(ok=True, hash=h)
        if prev_hash and prev_hash != h:
            health["changed"] = True
            return Finding(
                title=f"{name} changed a tracked page",
                url=url,
                summary=f"Meaningful content change detected on {url}. Review for pricing/offer/positioning moves.",
                source=f"Competitor: {name}",
                tier=1,
                published=datetime.now(timezone.utc).isoformat(),
                ftype="competitor_move",
                verticals=list(verticals),
            ), health
        return None, health
    except Exception as exc:  # noqa: BLE001
        log.warning("competitor fetch failed: %s %s -> %s", name, url, exc)
        health["error"] = str(exc)[:300]
        return None, health


def collect_all(competitors: list[dict], hashes: dict) -> tuple[list[Finding], list[dict], dict]:
    """hashes: {url: last_hash}. Returns (findings, health, updated_hashes)."""
    findings, health = [], []
    updated = dict(hashes)
    for c in competitors:
        for url in c.get("urls", []):
            f, h = check_url(c["name"], url, hashes.get(url), c.get("verticals", []))
            health.append(h)
            if h["ok"]:
                updated[url] = h["hash"]
            if f:
                findings.append(f)
    return findings, health, updated
