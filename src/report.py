"""Deterministic HTML reports. No LLM. Light blue/white MarketAlong style."""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone, timedelta

from bs4 import BeautifulSoup

from .config_loader import profile as load_profile
from .models import Finding

IST = timezone(timedelta(hours=5, minutes=30))
BAND_COLOR = {"critical": "#c0392b", "high": "#1565c0", "watchlist": "#5c6bc0", "low_signal": "#90a4ae"}


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


# Plain-English translations so a non-technical reader understands instantly.
FTYPE_PLAIN = {
    "platform_update": "A tool you use changed something",
    "tool_update": "A new tool or update is out",
    "risk": "⚠️ This could affect your business",
    "regulation": "⚠️ A new rule or policy",
    "competitor_move": "A competitor made a move",
    "opportunity": "A possible opportunity",
    "market_signal": "Industry news",
}
VERT_PLAIN = {
    "digital_marketing": "Marketing & Ads", "ai_automation": "AI & Automation",
    "marketverse": "Marketplace", "app_development": "Apps & Websites",
    "shop": "Online Store", "learn": "Courses & Content", "studio": "Design",
    "finance_ops": "Finance & Admin", "media": "Video & Content", "ventures": "New Ideas",
}
BAND_PLAIN = {"critical": "🔥 Big deal", "high": "⭐ Worth your attention", "watchlist": "👀 Keep an eye on it"}


def _plain_verts(f: Finding) -> str:
    names = [VERT_PLAIN.get(v, v) for v in f.verticals]
    return ", ".join(dict.fromkeys(names)) or "your business"


def _clean_summary(text: str, limit: int = 360) -> str:
    """Strip HTML, collapse whitespace, trim at a sentence end so the email is self-contained."""
    if not text:
        return ""
    plain = BeautifulSoup(text, "lxml").get_text(" ", strip=True)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= limit:
        return plain
    cut = plain[:limit]
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return (cut[: end + 1] if end > limit * 0.5 else cut.rstrip() + "…")


def _capability_note(f: Finding) -> str:
    """If the news touches a tool the user already has, say so plainly."""
    tools = (load_profile().get("tools_you_have") or {})
    text = f"{f.title} {f.summary}".lower()
    for key, label in tools.items():
        if key in text:
            return f"✅ **This touches {label} — so it's directly relevant to you.**"
    return ""


def _gap_label(gap_id: str) -> str:
    for g in (load_profile().get("gaps") or []):
        if g["id"] == gap_id:
            return g["label"]
    return ""


def _gap_note(f: Finding) -> str:
    if not f.gap_id:
        return ""
    return f"🎯 **Stay-ahead move:** this helps you close a gap — _{_gap_label(f.gap_id)}_."


def daily_brief_markdown(findings: list[Finding], opportunities: list[dict], risks: list[dict],
                         council_pack: str | None, run_at_utc: str) -> tuple[str, str]:
    """Plain-English brief for GitHub Issue delivery. Anyone can read it. Returns (title, body)."""
    notable = sorted([f for f in findings if f.band != "low_signal"], key=lambda x: x.score, reverse=True)
    title = f"📋 Your MarketAlong Update — {datetime.now(IST):%d %b %Y}"

    L = [f"**Hi! Here's what happened in your industry today, in plain words.**",
         f"_({_now_ist()})_\n",
         "---\n"]

    # The headline takeaways
    L.append("## ⭐ The main things to know today\n")
    if notable:
        for i, f in enumerate(notable[:5], 1):
            tag = BAND_PLAIN.get(f.band, "")
            summary = _clean_summary(f.summary)
            cap = _capability_note(f)
            block = [f"### {i}. {f.title}",
                     f"_{FTYPE_PLAIN.get(f.ftype, 'News')} — about {_plain_verts(f)}. {tag}_\n"]
            if summary:
                block.append(f"**What happened:** {summary}\n")
            gap = _gap_note(f)
            if gap:
                block.append(gap + "\n")
            if cap:
                block.append(cap + "\n")
            block.append(f"_Source: {f.source}. Want the original? [Open it here]({f.url})_\n")
            L.append("\n".join(block))
    else:
        L.append("_Nothing major today. That's normal — quiet days happen._\n")

    # Stay-ahead roundup: which of the user's gaps saw movement today
    gap_hits = {}
    for f in notable:
        if f.gap_id:
            gap_hits.setdefault(f.gap_id, f)  # keep highest-scored per gap (notable is sorted)
    if gap_hits:
        L.append("## 🎯 How to stay ahead this week\n")
        L.append("_These items move you toward gaps we identified for MarketAlong:_\n")
        for gid, f in gap_hits.items():
            L.append(f"- **{_gap_label(gid)}**  \n  → See item above: *{f.title}*")
        L.append("")

    # Money ideas
    if opportunities:
        L.append("## 💡 Ideas you could make money from\n")
        for o in opportunities[:3]:
            spark = o.get("why_now", "")[:70]
            push = "**Looks promising — try it.**" if o["recommendation"] == "pursue" else "Worth thinking about."
            L.append(f"- **You could offer clients:** {o['suggested_offer']}  \n"
                     f"  💰 You could charge around **{o['suggested_price']}**. {push}  \n"
                     f"  _Why now: {spark}_  \n"
                     f"  ▶️ First step: {o['validation_plan']}\n")

    # Watch-outs
    act_risks = [r for r in risks if r["status"] == "act"] + [r for r in risks if r["status"] != "act"]
    if act_risks:
        L.append("## ⚠️ Things to watch out for\n")
        for r in act_risks[:3]:
            L.append(f"- **{r['title']}**  \n  What to do: {r['mitigation']}\n")

    # The smart-advice box, explained for a beginner
    if council_pack:
        L.append("## 🧠 Want expert business advice on today's biggest item?\n")
        L.append("Copy the grey box below. Open **Claude**, type **`/billion-dollar-team`**, and paste it. "
                 "8 famous business experts will tell you exactly what to do, step by step.\n")
        L.append("```\n" + council_pack + "\n```")

    L.append("\n---\n_This is your simple daily summary. It updates by itself every weekday morning — "
             "you don't have to do anything._")
    return title, "\n".join(L)


def critical_alert_markdown(criticals: list[Finding], council_pack: str | None,
                            run_at_utc: str) -> tuple[str, str]:
    """URGENT alert — only fires for score>=85 tier-1 items. Plain, action-first."""
    top = criticals[0]
    title = f"🚨 URGENT: MarketAlong — {top.title[:70]}"
    L = [f"**🚨 Something important just happened. Read this now.** _({_now_ist()})_\n", "---\n"]
    for f in criticals:
        summary = _clean_summary(f.summary)
        L.append(f"### {f.title}")
        L.append(f"_About {_plain_verts(f)}. Importance score: {f.score}/100._\n")
        if summary:
            L.append(f"**What happened:** {summary}\n")
        gap = _gap_note(f)
        if gap:
            L.append(gap + "\n")
        cap = _capability_note(f)
        if cap:
            L.append(cap + "\n")
        L.append(f"**Why it's urgent:** this is a major change in something you rely on. "
                 f"Acting early keeps you ahead; ignoring it lets competitors react first.\n")
        L.append(f"_Source: {f.source}. [Open it]({f.url})_\n")

    if council_pack:
        L.append("## 🧠 Get an expert action plan now\n")
        L.append("Open **Claude**, type **`/billion-dollar-team`**, paste the box:\n")
        L.append("```\n" + council_pack + "\n```")
    L.append("\n---\n_You only get this email when something is genuinely big (rare by design)._")
    return title, "\n".join(L)


def period_report_markdown(findings: list[Finding], opportunities: list[dict], risks: list[dict],
                           council_pack: str | None, run_at_utc: str, period: str) -> tuple[str, str]:
    """Weekly/monthly rollup in plain English. period = 'week' or 'month'."""
    is_month = period == "month"
    notable = sorted(findings, key=lambda x: x.score, reverse=True)
    icon = "🗓️" if is_month else "📊"
    word = "Monthly Strategy" if is_month else "Weekly Report"
    title = f"{icon} Your MarketAlong {word} — {datetime.now(IST):%d %b %Y}"

    L = [f"**Your MarketAlong {word.lower()}, in plain words.** _({_now_ist()})_\n", "---\n"]

    # At-a-glance
    gap_counts: dict[str, int] = {}
    for f in notable:
        if f.gap_id:
            gap_counts[f.gap_id] = gap_counts.get(f.gap_id, 0) + 1
    L.append(f"## 📈 The {period} at a glance\n")
    L.append(f"- **{len(notable)}** important things happened in your industry")
    L.append(f"- **{sum(gap_counts.values())}** of them help you get ahead on your goals")
    L.append(f"- **{sum(1 for f in notable if f.ftype in ('risk', 'regulation'))}** are risks to watch\n")

    # Gap scorecard — where you're moving vs still blind
    all_gaps = load_profile().get("gaps") or []
    if all_gaps:
        L.append("## 🎯 Your stay-ahead scorecard\n")
        for g in all_gaps:
            n = gap_counts.get(g["id"], 0)
            mark = "✅ moving" if n >= 2 else "🟡 some movement" if n == 1 else "🔴 blind spot — no movement"
            L.append(f"- **{g['label']}** — {mark} ({n} item{'s' if n != 1 else ''})")
        L.append("\n_🔴 blind spots are where competitors can pass you. Pick one to act on._\n")

    # Biggest changes
    L.append(f"## ⭐ Biggest changes this {period}\n")
    for f in notable[:6]:
        L.append(f"- **{f.title}** — _{FTYPE_PLAIN.get(f.ftype, 'News')}, {_plain_verts(f)}_. [Open]({f.url})")
    L.append("")

    # What to launch (month) / try (week)
    if opportunities:
        head = "## 🚀 What to launch this month" if is_month else "## 💡 What to try this week"
        L.append(head + "\n")
        for o in opportunities[:4]:
            L.append(f"- **{o['suggested_offer']}** — charge ~{o['suggested_price']}. First step: {o['validation_plan']}")
        L.append("")

    if risks:
        L.append("## ⚠️ Risks to handle\n")
        for r in risks[:4]:
            L.append(f"- **{r['title']}** — {r['mitigation']}")
        L.append("")

    if council_pack:
        L.append(f"## 🧠 Your biggest decision this {period}\n")
        L.append("Open **Claude**, type **`/billion-dollar-team`**, paste the box below. "
                 "8 business experts will give you a full action plan.\n")
        L.append("```\n" + council_pack + "\n```")

    L.append(f"\n---\n_Automatic {period}ly report. Nothing for you to do — it builds itself._")
    return title, "\n".join(L)


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
