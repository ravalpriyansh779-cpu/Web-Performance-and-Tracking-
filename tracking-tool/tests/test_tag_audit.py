import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tag_audit
import latency_report


def _entry(url, status=200, time_ms=100):
    return {
        "request": {"method": "GET", "url": url},
        "response": {"status": status},
        "time": time_ms,
        "timings": {"wait": time_ms * 0.9},
    }


def test_classify_entry_known_tag():
    assert tag_audit.classify_entry("https://www.google-analytics.com/g/collect") == "GA4"
    assert tag_audit.classify_entry("https://api.example.com/v1/cart") is None


def test_audit_flags_missing_tag():
    entries = [_entry("https://www.googletagmanager.com/gtm.js")]
    report = tag_audit.audit(entries, expected_tags=["GTM", "GA4"])
    assert "GA4" in report["missing"]
    assert "GTM" not in report["missing"]
    assert report["healthy"] is False


def test_audit_flags_broken_call():
    entries = [_entry("https://www.google-analytics.com/g/collect", status=500)]
    report = tag_audit.audit(entries, expected_tags=["GA4"])
    assert len(report["broken_calls"]) == 1
    assert report["broken_calls"][0]["tag"] == "GA4"


def test_healthy_when_all_expected_tags_fire_ok():
    entries = [_entry("https://www.google-analytics.com/g/collect", status=200)]
    report = tag_audit.audit(entries, expected_tags=["GA4"])
    assert report["healthy"] is True


def test_find_bottlenecks_sorted_slowest_first():
    entries = [_entry("https://a.com", time_ms=100), _entry("https://b.com", time_ms=900)]
    slow = latency_report.find_bottlenecks(entries, threshold_ms=500)
    assert len(slow) == 1
    assert slow[0]["url"] == "https://b.com"


def test_summarize_stats():
    entries = [_entry("https://a.com", time_ms=100), _entry("https://b.com", time_ms=300)]
    stats = latency_report.summarize(entries)
    assert stats["count"] == 2
    assert stats["avg_ms"] == 200
