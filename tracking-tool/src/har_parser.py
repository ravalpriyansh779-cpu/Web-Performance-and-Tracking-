"""
har_parser.py

Two ways to read a .har file's entries:

- load_full(): straightforward json.load -- simplest, but loads the entire file
  (all response bodies, headers, cookies, etc.) into memory at once.
- stream_entries(): uses ijson to pull just the "log.entries.item" fields we
  actually need (request url/method, response status, timing) one at a time,
  without ever materializing the full parsed document. This is what gives the
  memory-footprint win on large HAR files, which routinely run 20-100MB+ because
  every request/response header and body is embedded inline.
"""
import json
import ijson


def load_full(path):
    """Load the entire HAR file into memory and return the list of entries."""
    with open(path, "r") as f:
        data = json.load(f)
    return data["log"]["entries"]


def stream_entries(path):
    """
    Yield lightweight entry dicts one at a time using streaming JSON parsing.
    Only pulls the fields the audit/latency modules actually need, instead of
    the full HAR record (which also carries headers, cookies, and bodies).
    """
    with open(path, "rb") as f:
        for entry in ijson.items(f, "log.entries.item"):
            yield {
                "request": {
                    "method": entry.get("request", {}).get("method"),
                    "url": entry.get("request", {}).get("url"),
                },
                "response": {
                    "status": entry.get("response", {}).get("status"),
                },
                "time": entry.get("time", 0),
                "timings": entry.get("timings", {}),
            }
