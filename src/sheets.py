"""Google Sheets writer. Skips gracefully if creds absent (local dev)."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from .models import ROW_HEADERS

log = logging.getLogger("sheets")


def _client():
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not raw or not sheet_id:
        return None, None
    import gspread
    from google.oauth2.service_account import Credentials
    info = json.loads(raw)
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds), sheet_id


def _tab(spreadsheet, name: str, headers: list[str]):
    try:
        ws = spreadsheet.worksheet(name)
    except Exception:  # noqa: BLE001
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=max(10, len(headers)))
        ws.append_row(headers)
    return ws


def write_findings(findings, health, opportunities, risks, council_pack) -> bool:
    """Append everything to the Command Center. Returns True if written."""
    client, sheet_id = _client()
    if not client:
        log.info("no Google creds -> skipping Sheets write (local mode)")
        return False
    ss = client.open_by_key(sheet_id)
    ts = datetime.now(timezone.utc).isoformat()

    intel = _tab(ss, "Latest Intelligence", ROW_HEADERS)
    rows = [f.to_row() for f in findings if f.band != "low_signal"]
    if rows:
        intel.append_rows(rows, value_input_option="RAW")

    alerts = _tab(ss, "Critical Alerts", ROW_HEADERS)
    crit = [f.to_row() for f in findings if f.band == "critical"]
    if crit:
        alerts.append_rows(crit, value_input_option="RAW")

    if opportunities:
        opp = _tab(ss, "Opportunities", ["ts", "name", "vertical", "price", "recommendation", "trigger_url"])
        opp.append_rows([[ts, o["name"], o["vertical"], o["suggested_price"],
                          o["recommendation"], o["trigger_url"]] for o in opportunities],
                        value_input_option="RAW")

    if risks:
        rk = _tab(ss, "Risks", ["ts", "title", "vertical", "severity", "status", "mitigation"])
        rk.append_rows([[ts, r["title"], r["vertical"], r["severity"], r["status"], r["mitigation"]]
                        for r in risks], value_input_option="RAW")

    sh = _tab(ss, "Source Health", ["ts", "source", "ok", "count", "error"])
    sh.append_rows([[ts, h.get("source") or h.get("competitor", "?"), h["ok"],
                     h.get("count", ""), h.get("error", "")] for h in health],
                   value_input_option="RAW")

    if council_pack:
        cp = _tab(ss, "Strategic Council Packs", ["ts", "pack"])
        cp.append_row([ts, council_pack], value_input_option="RAW")

    log.info("Sheets write OK: %d intel rows", len(rows))
    return True
