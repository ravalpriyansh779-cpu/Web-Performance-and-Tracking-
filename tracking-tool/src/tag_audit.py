"""
tag_audit.py

Validates tracking/tag-firing logic from captured network entries (from a HAR file)
without needing to touch the live site. Given a list of expected tags (e.g. "GA4
must fire on every pageview", "GTM container must load"), it checks the captured
requests and reports what fired, what's missing, and what looks malformed.
"""

KNOWN_TAGS = {
    "GA4": ["google-analytics.com/g/collect", "analytics.google.com/g/collect"],
    "GTM": ["googletagmanager.com/gtm.js"],
    "Meta Pixel": ["connect.facebook.net", "fbevents.js"],
    "LinkedIn Insight": ["px.ads.linkedin.com/collect", "snap.licdn.com"],
}


def classify_entry(url: str):
    """Return the tag name a URL belongs to, or None if it's not a known tag."""
    for tag_name, patterns in KNOWN_TAGS.items():
        if any(p in url for p in patterns):
            return tag_name
    return None


def audit(entries, expected_tags=None):
    """
    entries: list of dicts with at least {"request": {"url": ..., "method": ...},
             "response": {"status": ...}}
    expected_tags: list of tag names (from KNOWN_TAGS) that should have fired at
             least once in this session. Defaults to all known tags.

    Returns a report dict: fired tags (with count + example statuses),
    missing expected tags, and any tag calls that returned a non-2xx status.
    """
    expected_tags = expected_tags or list(KNOWN_TAGS.keys())

    fired = {}
    broken = []

    for entry in entries:
        url = entry["request"]["url"]
        status = entry.get("response", {}).get("status")
        tag = classify_entry(url)
        if tag is None:
            continue

        fired.setdefault(tag, {"count": 0, "statuses": []})
        fired[tag]["count"] += 1
        fired[tag]["statuses"].append(status)

        if status is not None and not (200 <= status < 300):
            broken.append({"tag": tag, "url": url, "status": status})

    missing = [t for t in expected_tags if t not in fired]

    return {
        "fired": fired,
        "missing": missing,
        "broken_calls": broken,
        "healthy": len(missing) == 0 and len(broken) == 0,
    }


def format_report(report: dict) -> str:
    lines = ["=== Tag Firing Audit ==="]
    if report["fired"]:
        lines.append("Fired tags:")
        for tag, info in report["fired"].items():
            lines.append(f"  - {tag}: {info['count']} call(s), statuses={info['statuses']}")
    else:
        lines.append("Fired tags: none detected")

    if report["missing"]:
        lines.append("Missing expected tags: " + ", ".join(report["missing"]))
    else:
        lines.append("Missing expected tags: none")

    if report["broken_calls"]:
        lines.append("Broken calls (non-2xx):")
        for b in report["broken_calls"]:
            lines.append(f"  - {b['tag']} -> {b['url']} (status {b['status']})")
    else:
        lines.append("Broken calls: none")

    lines.append(f"Overall: {'HEALTHY' if report['healthy'] else 'ISSUES FOUND'}")
    return "\n".join(lines)
