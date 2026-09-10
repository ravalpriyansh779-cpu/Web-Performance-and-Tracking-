"""
session_simulator.py

Generates synthetic HAR (HTTP Archive) sessions that mimic what Chrome DevTools'
Network tab would export from a real browsing session. This lets the rest of the
toolkit (tag audit, latency report, memory benchmark) be developed and tested
without needing live site access -- you can point it at a real exported .har file
from Chrome DevTools just as easily.

Each simulated entry includes: url, method, status, timing breakdown (dns, connect,
send, wait, receive), and response size -- the same fields a real HAR file has.
"""
import json
import random
import argparse
from pathlib import Path

# A representative mix of real-world tracking/analytics endpoints + normal app traffic.
TRACKING_ENDPOINTS = [
    "https://www.google-analytics.com/g/collect",
    "https://analytics.google.com/g/collect",
    "https://www.googletagmanager.com/gtm.js",
    "https://connect.facebook.net/en_US/fbevents.js",
    "https://px.ads.linkedin.com/collect",
    "https://snap.licdn.com/li.lms-analytics/insight.min.js",
]

APP_ENDPOINTS = [
    "https://api.example.com/v1/products",
    "https://api.example.com/v1/cart",
    "https://cdn.example.com/static/app.js",
    "https://cdn.example.com/static/styles.css",
    "https://api.example.com/v1/user/session",
]


def _timing():
    """Random but plausible per-request timing breakdown, in ms."""
    dns = random.uniform(0, 15)
    connect = random.uniform(0, 40)
    send = random.uniform(0, 5)
    wait = random.uniform(20, 900)  # server think time -- where bottlenecks usually hide
    receive = random.uniform(1, 60)
    return {
        "dns": round(dns, 2),
        "connect": round(connect, 2),
        "send": round(send, 2),
        "wait": round(wait, 2),
        "receive": round(receive, 2),
    }


def generate_session(num_entries=40, inject_slow_tracking=True, seed=None):
    """Build one synthetic HAR document with `num_entries` network calls."""
    if seed is not None:
        random.seed(seed)

    entries = []
    pool = APP_ENDPOINTS + TRACKING_ENDPOINTS
    for i in range(num_entries):
        url = random.choice(pool)
        timing = _timing()

        # Deliberately inject a couple of slow tracking calls so the latency
        # report / tag audit have something real to catch.
        if inject_slow_tracking and url in TRACKING_ENDPOINTS and random.random() < 0.25:
            timing["wait"] = round(random.uniform(1200, 3000), 2)

        total_time = round(sum(timing.values()), 2)
        entries.append({
            "startedDateTime": f"2026-09-01T10:00:{i:02d}.000Z",
            "request": {
                "method": "GET" if "collect" not in url else "POST",
                "url": url,
            },
            "response": {
                "status": random.choice([200, 200, 200, 204, 200, 404]),
                "content": {"size": random.randint(200, 50000)},
            },
            "time": total_time,
            "timings": timing,
        })

    return {"log": {"version": "1.2", "entries": entries}}


def main():
    parser = argparse.ArgumentParser(description="Generate a synthetic HAR session for testing.")
    parser.add_argument("--entries", type=int, default=40, help="Number of network entries to generate")
    parser.add_argument("--out", type=str, default="sample_data/session.har", help="Output .har path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    session = generate_session(num_entries=args.entries, seed=args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(session, indent=2))
    print(f"Wrote {args.entries} entries to {out_path}")


if __name__ == "__main__":
    main()
