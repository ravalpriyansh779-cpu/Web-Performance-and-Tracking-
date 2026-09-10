"""
cli.py

Entry point: python src/cli.py --har sample_data/session.har
Runs tag-firing audit + latency bottleneck report against a HAR file
(real, exported from Chrome DevTools, or synthetic via session_simulator.py).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from har_parser import stream_entries
import tag_audit
import latency_report


def main():
    parser = argparse.ArgumentParser(description="Web Performance & Tracking Diagnostic Tool")
    parser.add_argument("--har", required=True, help="Path to a .har file")
    parser.add_argument("--threshold-ms", type=int, default=800, help="Latency bottleneck threshold in ms")
    args = parser.parse_args()

    entries = list(stream_entries(args.har))

    print(tag_audit.format_report(tag_audit.audit(entries)))
    print()
    print(latency_report.format_report(entries, threshold_ms=args.threshold_ms))


if __name__ == "__main__":
    main()
