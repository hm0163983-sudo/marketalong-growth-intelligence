"""Smallest checks that fail if the logic breaks. No frameworks beyond pytest."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Finding, canonical_url
from src.classify import classify
from src.scoring import score
from src.dedup import filter_new


def test_canonical_url_strips_tracking():
    a = canonical_url("https://x.com/post?utm_source=rss&id=5#top")
    assert a == "https://x.com/post?id=5"
    assert canonical_url("https://x.com/post/") == "https://x.com/post"


def test_classify_detects_vertical_and_risk():
    f = Finding(title="OpenAI deprecates the old Assistants API",
                summary="The legacy endpoint will be removed.", tier=1)
    classify(f)
    assert "ai_automation" in f.verticals
    assert f.ftype == "risk"          # 'deprecat' + 'removed'
    assert f.urgency > 0


def test_score_bands_and_factors_sum():
    f = Finding(title="Google Ads introduces new AI campaign feature",
                summary="now available for advertisers", tier=1,
                verticals=["digital_marketing"])
    classify(f)
    score(f)
    assert f.score == sum(f.score_factors.values())   # factors are transparent
    assert 0 <= f.score <= 100
    assert f.band in ("critical", "high", "watchlist", "low_signal")


def test_dedup_drops_seen_and_near_duplicates():
    a = Finding(title="Meta launches new ad format", url="https://meta.com/a", tier=1)
    b = Finding(title="Meta launches new ad format!", url="https://other.com/b", tier=2)  # near-dup title
    c = Finding(title="Totally different SEO update", url="https://g.com/c", tier=1)
    kept, seen = filter_new([a, b, c], set())
    assert len(kept) == 2              # b dropped as near-duplicate of a
    # re-running with same fingerprints drops everything
    kept2, _ = filter_new([a, c], seen)
    assert kept2 == []


def test_critical_alert_requires_tier1():
    from src.scoring import is_critical_alert
    f = Finding(title="x", tier=3)
    f.score = 90
    assert is_critical_alert(f) is False   # tier 3 blocked even at score 90
