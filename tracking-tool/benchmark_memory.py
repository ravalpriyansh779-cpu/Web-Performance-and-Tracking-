"""
benchmark_memory.py

Generates a large synthetic HAR session, then measures peak memory usage of
har_parser.load_full() vs har_parser.stream_entries(), and prints the % reduction.
Run standalone: python benchmark_memory.py --entries 5000
"""
import argparse
import gc
import sys
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from session_simulator import generate_session
import json
import har_parser


def measure_full_load(path):
    gc.collect()
    tracemalloc.start()
    entries = har_parser.load_full(path)
    _ = len(entries)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def measure_streaming(path):
    gc.collect()
    tracemalloc.start()
    count = 0
    for _ in har_parser.stream_entries(path):
        count += 1
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entries", type=int, default=5000, help="Size of the synthetic HAR session")
    parser.add_argument("--out", type=str, default="sample_data/large_session.har")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    session = generate_session(num_entries=args.entries, seed=7)
    out_path.write_text(json.dumps(session))
    print(f"Generated {args.entries} entries -> {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")

    full_peak = measure_full_load(out_path)
    stream_peak = measure_streaming(out_path)

    reduction = (1 - stream_peak / full_peak) * 100

    print(f"\nPeak memory (full json.load):        {full_peak / 1024:.1f} KB")
    print(f"Peak memory (streaming w/ ijson):     {stream_peak / 1024:.1f} KB")
    print(f"Memory footprint reduction:           {reduction:.1f}%")


if __name__ == "__main__":
    main()
