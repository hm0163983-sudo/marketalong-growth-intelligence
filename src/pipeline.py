"""End-to-end daily pipeline. Runs with zero secrets (preview mode)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import config_loader, state
from .collectors import rss, competitor
from .classify import classify
from .scoring import score
from .dedup import filter_new
from .opportunities import build_all as build_opportunities
from .risks import build_all as build_risks
from .council import build_pack, pick_for_council
from .report import daily_brief
from .emailer import send
from .sheets import write_findings

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
    if notable:
        email_result = send(subject, body, report_id=f"daily-{datetime.now(timezone.utc):%Y%m%d}")
    else:
        log.info("no notable findings -> no email")

    # 6. persist
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


if __name__ == "__main__":
    run_daily()
