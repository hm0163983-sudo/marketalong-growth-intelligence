"""Deterministic HTML reports. No LLM. Light blue/white MarketAlong style."""
from __future__ import annotations

import html
from datetime import datetime, timezone, timedelta

from .models import Finding

IST = timezone(timedelta(hours=5, minutes=30))
BAND_COLOR = {"critical": "#c0392b", "high": "#1565c0", "watchlist": "#5c6bc0", "low_signal": "#90a4ae"}


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


def _esc(s: str) -> str:
    return html.escape(s or "")


def _finding_row(f: Finding) -> str:
    color = BAND_COLOR.get(f.band, "#607d8b")
    verts = _esc(", ".join(f.verticals) or "—")
    return f"""
    <tr>
      <td style="padding:8px;border-bottom:1px solid #e3eaf2;">
        <span style="background:{color};color:#fff;border-radius:4px;padding:2px 8px;font-size:11px;">
          {f.band.upper()} {f.score}</span>
      </td>
      <td style="padding:8px;border-bottom:1px solid #e3eaf2;">
        <a href="{_esc(f.url)}" style="color:#1565c0;text-decoration:none;font-weight:600;">{_esc(f.title)}</a>
        <div style="font-size:12px;color:#607d8b;">{_esc(f.source)} · {f.ftype} · {verts}</div>
      </td>
    </tr>"""


def _section(title: str, items_html: str) -> str:
    if not items_html:
        return ""
    return f"""<h2 style="color:#0d47a1;font-size:16px;margin:24px 0 8px;">{title}</h2>
    <table style="width:100%;border-collapse:collapse;">{items_html}</table>"""


def daily_brief(findings: list[Finding], opportunities: list[dict], risks: list[dict],
                council_pack: str | None, run_at_utc: str) -> tuple[str, str]:
    """Return (subject, html). Only watchlist+ findings are emailed."""
    notable = [f for f in findings if f.band != "low_signal"]
    notable.sort(key=lambda x: x.score, reverse=True)
    top5 = notable[:5]
    crit = [f for f in notable if f.band == "critical"]

    subject = f"MarketAlong Daily Brief · {len(notable)} signals · {len(crit)} critical · {_now_ist()}"

    top_actions = []
    for o in opportunities[:3]:
        top_actions.append(f"Validate: {_esc(o['name'])} — {o['recommendation'].upper()}")
    for r in risks[:2]:
        if r["status"] == "act":
            top_actions.append(f"Act on risk: {_esc(r['title'])}")
    actions_html = "".join(f"<li>{a}</li>" for a in top_actions[:3]) or "<li>No high-priority action today.</li>"

    council_html = ""
    if council_pack:
        council_html = f"""<h2 style="color:#0d47a1;font-size:16px;margin:24px 0 8px;">🧠 Strategic Council Pack (paste into Claude Code → Billion Dollar Team)</h2>
        <pre style="background:#f4f8fc;border:1px solid #d6e4f0;border-radius:6px;padding:12px;
        white-space:pre-wrap;font-size:12px;color:#263238;">{_esc(council_pack)}</pre>"""

    body = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:680px;margin:auto;color:#263238;">
    <div style="background:#1565c0;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;">
      <div style="font-size:20px;font-weight:700;">MarketAlong Growth Intelligence</div>
      <div style="font-size:13px;opacity:.9;">Daily Brief · generated {_now_ist()} (run UTC {_esc(run_at_utc)})</div>
    </div>
    <div style="background:#fff;border:1px solid #e3eaf2;border-top:none;padding:20px;border-radius:0 0 8px 8px;">
      <h2 style="color:#0d47a1;font-size:16px;margin:0 0 8px;">Do This Today</h2>
      <ol style="margin:0 0 8px 18px;padding:0;">{actions_html}</ol>
      {_section("Top Signals", "".join(_finding_row(f) for f in top5))}
      {_section("Opportunities", "".join(f'<tr><td style="padding:8px;border-bottom:1px solid #e3eaf2;">▸ {_esc(o["name"])} <span style="color:#607d8b;font-size:12px;">({o["recommendation"]}, {o["suggested_price"]})</span></td></tr>' for o in opportunities[:3]))}
      {_section("Risks", "".join(f'<tr><td style="padding:8px;border-bottom:1px solid #e3eaf2;">⚠ {_esc(r["title"])} <span style="color:#607d8b;font-size:12px;">(sev {r["severity"]}, {r["status"]})</span></td></tr>' for r in risks[:3]))}
      {council_html}
      <p style="font-size:11px;color:#90a4ae;margin-top:20px;">
        Low-signal items suppressed. Verified facts only; interpretations are heuristic. Tune config/ to adjust.</p>
    </div></div>"""
    return subject, body
