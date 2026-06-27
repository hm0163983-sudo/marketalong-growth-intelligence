# MarketAlong Growth Intelligence OS

Zero-cost intelligence engine. Monitors digital-marketing & AI-automation industry, competitors, tools, opportunities and risks → scores them → emails you a decision-focused brief and writes a Google Sheet dashboard. Runs on GitHub Actions while your Mac is off.

**No paid APIs. No LLM API. No paid hosting.** Python + free RSS + GitHub Actions + Google Sheets + Gmail SMTP.

## What runs today (Phase 1 — built & tested)

- RSS collector (12 official sources, edit `config/sources.yaml`)
- Competitor page change-watch via content hash (`config/competitors.yaml`)
- Deterministic keyword classifier (`config/keywords.yaml`) — no LLM
- Transparent 0–100 scorer with per-factor audit (`config/scoring_weights.yaml`)
- Dedup (URL fingerprint + difflib title similarity), state persisted in `output/state.json`
- Opportunity + risk cards (templates, never invents demand numbers)
- Daily HTML brief (top 5 signals, 3 actions, 3 opps, 3 risks)
- **Strategic Council Pack** — ready-to-paste prompt for the Billion Dollar Team skill in Claude Code
- Gmail SMTP sender with safe **preview mode** default
- Google Sheets writer (skips silently with no creds)
- GitHub Actions daily workflow + manual dispatch
- 5 unit tests, all passing

## Run locally in 30 seconds (no accounts needed)

```bash
cd marketalong-growth-intelligence
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q          # 5 passed
python -m scripts.run_daily         # live RSS, writes output/previews/daily-YYYYMMDD.html
open output/previews/daily-*.html   # see your brief
```

No secrets → preview-only, Sheets skipped, nothing emailed. Safe.

## Go live (one-time setup)

1. **Gmail App Password** — Google Account → Security → 2-Step Verification → App Passwords. Put it in GitHub Secret `SMTP_APP_PASSWORD`.
2. **Google Sheet** — create one named `MarketAlong Growth Intelligence Command Center`. Copy its ID from the URL.
3. **Service account** — Google Cloud Console → new project → enable Google Sheets API → create service account → JSON key. **Share the Sheet with the service-account email (Editor).** Paste the JSON (one line) into Secret `GOOGLE_SERVICE_ACCOUNT_JSON`.
4. **GitHub repo (private)** → Settings → Secrets and variables → Actions. Add:
   `EMAIL_SEND_ENABLED=true`, `EMAIL_RECIPIENT=hmehta4851@gmail.com`,
   `SMTP_USERNAME`, `SMTP_APP_PASSWORD`, `SMTP_FROM`,
   `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SHEET_ID`.
5. Push repo → Actions tab → run **Daily Intelligence Brief** manually to test.

Keep `EMAIL_SEND_ENABLED=false` until you've reviewed a few previews.

## Schedule

`.github/workflows/daily.yml` runs `0 3 * * 1-5` UTC = **08:30 IST Mon–Fri**. GitHub cron drifts ±15–30 min; the report records the **actual** run time. State (`output/state.json`) is committed back each run so dedup survives across runs without a database.

## Using the Billion Dollar Team (manual decision layer)

When a finding scores ≥70, the brief includes a **Strategic Council Pack**. Copy it → open Claude Code → `/billion-dollar-team` → paste. The pack contains verified facts + the decision question only. The system never fabricates strategic opinions or endorsements.

## Known limits / honest notes

- 2 starter feeds (Google Ads, Anthropic) don't expose clean RSS — they skip gracefully and are logged in Source Health. Swap URLs in `config/sources.yaml` anytime.
- Classification is keyword rules, not semantic. Occasionally miscategorizes. Tune `config/keywords.yaml`.
- Replace the `Example Agency` placeholder in `config/competitors.yaml` with real competitors.

## Not built yet (Phase 2/3 — say the word)

Weekly/monthly reports, critical-alert workflow, the other 12 Sheet tabs with conditional formatting, source-health email alerts. Skipped deliberately (ponytail): build when you actually feel the gap, not before.
```
