Web Performance & Tracking Diagnostic Tool
Audits tag-firing/tracking logic and flags latency bottlenecks from captured network sessions (HAR files) — without requiring live access to the site under test. Point it at a .har file exported from Chrome DevTools' Network tab, or generate a synthetic session for testing.

Why HAR files
Chrome DevTools can export any Network panel capture as a .har (HTTP Archive) file — a JSON record of every request, response, status code, and timing breakdown from a browsing session. That means tracking/tag-firing logic and network performance can be audited entirely offline, from a file a QA engineer or client hands over, instead of needing credentials or direct access to a live (often staging/client-owned) environment.

What it does
Tag-firing audit (src/tag_audit.py) — checks whether expected analytics/marketing tags (GA4, GTM, Meta Pixel, LinkedIn Insight) actually fired in the session, flags any that are missing, and flags any tag call that returned a non-2xx status.
Latency report (src/latency_report.py) — surfaces the slowest requests in the session (bottleneck detection), which in practice is very often a poorly-configured or slow-loading tracking tag.
Memory-efficient parsing (src/har_parser.py) — HAR files from real sessions can run 20–100MB+ because every request/response header and body is embedded inline. stream_entries() uses ijson to pull only the fields this tool needs, one entry at a time, instead of loading the whole file into memory.
Usage
pip install -r requirements.txt

# Generate a synthetic session (or use a real .har exported from Chrome DevTools)
python src/session_simulator.py --entries 40 --out sample_data/session.har

# Run the full diagnostic
python src/cli.py --har sample_data/session.har --threshold-ms 800
Memory benchmark
benchmark_memory.py generates a large synthetic HAR file and compares peak memory usage of a naive full json.load() against the streaming parser:

python benchmark_memory.py --entries 5000
Sample run on this machine (5,000-entry session, ~1.4MB HAR):

Peak memory (full json.load):        7789.1 KB
Peak memory (streaming w/ ijson):     613.6 KB
Memory footprint reduction:           92.1%
Numbers will vary by machine and session size — re-run it and paste your own output here before treating a specific percentage as a fixed claim.
