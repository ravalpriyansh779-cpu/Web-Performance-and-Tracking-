"""
latency_report.py

Flags latency bottlenecks in captured network payloads (HAR entries). "Bottleneck"
here means a request's total time (or its server 'wait' phase specifically) exceeds
a configurable threshold -- this is where tracking calls most often silently delay
page interactivity.
"""


def find_bottlenecks(entries, threshold_ms=800):
    """Return entries whose total time exceeds threshold_ms, sorted slowest-first."""
    slow = []
    for entry in entries:
        total_time = entry.get("time", 0)
        if total_time >= threshold_ms:
            slow.append({
                "url": entry["request"]["url"],
                "time_ms": total_time,
                "wait_ms": entry.get("timings", {}).get("wait", None),
            })
    return sorted(slow, key=lambda x: x["time_ms"], reverse=True)


def summarize(entries):
    """Basic latency stats across the whole session."""
    times = [e.get("time", 0) for e in entries]
    if not times:
        return {"count": 0}
    return {
        "count": len(times),
        "avg_ms": round(sum(times) / len(times), 2),
        "max_ms": round(max(times), 2),
        "min_ms": round(min(times), 2),
    }


def format_report(entries, threshold_ms=800) -> str:
    stats = summarize(entries)
    bottlenecks = find_bottlenecks(entries, threshold_ms)

    lines = ["=== Latency Report ==="]
    lines.append(f"Total requests analyzed: {stats.get('count', 0)}")
    if stats.get("count", 0):
        lines.append(f"Avg: {stats['avg_ms']}ms | Max: {stats['max_ms']}ms | Min: {stats['min_ms']}ms")

    if bottlenecks:
        lines.append(f"\nBottlenecks (>= {threshold_ms}ms), slowest first:")
        for b in bottlenecks[:10]:
            lines.append(f"  - {b['time_ms']}ms  wait={b['wait_ms']}ms  {b['url']}")
    else:
        lines.append(f"\nNo requests exceeded {threshold_ms}ms.")

    return "\n".join(lines)
