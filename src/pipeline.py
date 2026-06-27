"""End-to-end daily pipeline. Runs with zero secrets (preview mode)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import config_loader, state, history
from .collectors import rss, competitor
from .classify import classify
from .scoring import score, is_critical_alert
from .dedup import filter_new
from .opportunities import build_all as build_opportunities
from .risks import build_all as build_risks
from .council import build_pack, pick_for_council
from .report import daily_brief, daily_brief_markdown
from .emailer import send
from .sheets import write_findings

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("pipeline")


def run_daily() -> dict:
    run_at = datetime.now(timezone.utc).isoformat()
    st = state.load()
    seen = set(st.get("seen", []))

    # 1. collect
    rss_findings, rss_health = rss.collect_all(config_loader.sources())
    comp_findings, comp_health, new_hashes = competitor.collect_all(
        config_loader.competitors(), st.get("competitor_hashes", {}))
    findings = rss_findings + comp_findings
    health = rss_health + comp_health
    log.info("collected %d raw findings", len(findings))

    # 2. dedup (drops already-seen across runs + near-dupes this run)
    findings, seen = filter_new(findings, seen)
    log.info("%d new after dedup", len(findings))

    # 3. classify + score
    for f in findings:
        classify(f)
        score(f)

    # 4. derive
    opportunities = sorted(build_opportunities(findings), key=lambda o: o["score"], reverse=True)
    risks = sorted(build_risks(findings), key=lambda r: r["severity"], reverse=True)
    council_finding = pick_for_council(findings)
    council_pack = build_pack(council_finding) if council_finding else None

    # 5. report + email (preview unless EMAIL_SEND_ENABLED=true)
    subject, body = daily_brief(findings, opportunities, risks, council_pack, run_at)
    notable = [f for f in findings if f.band != "low_signal"]
    email_result = {"sent": False, "preview": ""}
    OUT.mkdir(parents=True, exist_ok=True)
    # Always clear stale brief so the workflow only posts when there's real news.
    (OUT / "brief_title.txt").write_text("", encoding="utf-8")
    (OUT / "brief_body.md").write_text("", encoding="utf-8")
    if notable:
        email_result = send(subject, body, report_id=f"daily-{datetime.now(timezone.utc):%Y%m%d}")
        # Free delivery path: write markdown brief for the workflow to post as a GitHub Issue.
        md_title, md_body = daily_brief_markdown(findings, opportunities, risks, council_pack, run_at)
        (OUT / "brief_title.txt").write_text(md_title, encoding="utf-8")
        (OUT / "brief_body.md").write_text(md_body, encoding="utf-8")
    else:
        log.info("no notable findings -> no brief")

    # 6. persist
    if notable:
        history.append(notable)  # feeds weekly/monthly rollups
    write_findings(findings, health, opportunities, risks, council_pack)
    state.save(seen, new_hashes)

    summary = {
        "run_at": run_at, "raw": len(rss_findings) + len(comp_findings),
        "new": len(findings), "notable": len(notable),
        "critical": sum(1 for f in findings if f.band == "critical"),
        "opportunities": len(opportunities), "risks": len(risks),
        "sources_failed": sum(1 for h in health if not h["ok"]),
        "email_sent": email_result["sent"], "preview": email_result.get("preview", ""),
    }
    log.info("DONE: %s", summary)
    return summary


def run_critical() -> dict:
    """Fast RSS-only check for genuine criticals (score>=85, tier-1). Posts an URGENT
    issue immediately. Marks ONLY the criticals as seen so the daily brief still reports
    everything else. Leaves competitor hashes untouched (daily owns those)."""
    run_at = datetime.now(timezone.utc).isoformat()
    st = state.load()
    seen = set(st.get("seen", []))
    rss_findings, _ = rss.collect_all(config_loader.sources())
    new, _ = filter_new(rss_findings, seen)
    for f in new:
        classify(f)
        score(f)
    criticals = sorted([f for f in new if is_critical_alert(f)], key=lambda x: x.score, reverse=True)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "brief_title.txt").write_text("", encoding="utf-8")
    (OUT / "brief_body.md").write_text("", encoding="utf-8")
    if not criticals:
        log.info("no criticals this check")
        return {"criticals": 0, "posted": False}

    from .report import critical_alert_markdown
    council_pack = build_pack(criticals[0])
    title, body = critical_alert_markdown(criticals, council_pack, run_at)
    (OUT / "brief_title.txt").write_text(title, encoding="utf-8")
    (OUT / "brief_body.md").write_text(body, encoding="utf-8")

    seen |= {c.fingerprint for c in criticals}   # don't re-alert the same item
    history.append(criticals)
    state.save(seen, st.get("competitor_hashes", {}))  # preserve competitor hashes
    log.info("CRITICAL: %d alert(s) -> %s", len(criticals), title)
    return {"criticals": len(criticals), "posted": True}


def run_period(period: str) -> dict:
    """Weekly ('week', 7d) or monthly ('month', 30d) rollup from stored history.
    No fresh collection — summarizes what the daily runs already gathered."""
    run_at = datetime.now(timezone.utc).isoformat()
    days = 30 if period == "month" else 7
    findings = history.load_findings(days)
    log.info("%s rollup: %d findings in last %dd", period, len(findings), days)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "brief_title.txt").write_text("", encoding="utf-8")
    (OUT / "brief_body.md").write_text("", encoding="utf-8")
    if not findings:
        log.info("no history yet -> no %s report", period)
        return {"period": period, "findings": 0, "posted": False}

    opportunities = sorted(build_opportunities(findings), key=lambda o: o["score"], reverse=True)
    risks = sorted(build_risks(findings), key=lambda r: r["severity"], reverse=True)
    council_finding = pick_for_council(findings)
    council_pack = build_pack(council_finding) if council_finding else None

    from .report import period_report_markdown
    title, body = period_report_markdown(findings, opportunities, risks, council_pack, run_at, period)
    (OUT / "brief_title.txt").write_text(title, encoding="utf-8")
    (OUT / "brief_body.md").write_text(body, encoding="utf-8")
    # also email if SMTP enabled, reusing HTML daily layout's send path with markdown->simple wrap
    log.info("%s report ready: %s", period, title)
    return {"period": period, "findings": len(findings), "opportunities": len(opportunities),
            "risks": len(risks), "posted": True}


if __name__ == "__main__":
    run_daily()
