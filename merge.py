#!/usr/bin/env python3
"""
Fetch every source DNS filter list in sources.txt, merge them into one
de-duplicated list, and write it to filters/merged.txt for AdGuard Home
to consume as a single "DNS blocklist" subscription.

Usage:
    python merge.py

Reads:  sources.txt          (one "Name | URL" per line)
Writes: filters/merged.txt   (the merged filter, AGH-ready)
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.txt"
OUTPUT_FILE = ROOT / "filters" / "merged.txt"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AdGuardHome-Merger/1.0)"}
TIMEOUT = 30
MAX_RETRIES = 2


def load_sources() -> list[tuple[str, str]]:
    sources = []
    for line in SOURCES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            print(f"  ! skipping malformed sources.txt line: {line!r}", file=sys.stderr)
            continue
        name, url = line.split("|", 1)
        sources.append((name.strip(), url.strip()))
    return sources


def fetch(url: str) -> str | None:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:  # noqa: BLE001 - we want to survive any single bad source
            last_err = exc
            if attempt <= MAX_RETRIES:
                continue
    print(f"  ! failed to fetch {url} -> {last_err}", file=sys.stderr)
    return None


def extract_rules(raw_text: str) -> list[str]:
    """Strip comments/blank lines, keep every actual rule line as-is
    (adblock syntax, hosts syntax, and dnsmasq-style regex lines are all
    passed through unchanged — AdGuard Home decides how to interpret each
    line itself)."""
    rules = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("!") or line.startswith("#"):
            continue
        rules.append(line)
    return rules


def main() -> int:
    sources = load_sources()
    if not sources:
        print("No sources found in sources.txt — nothing to do.", file=sys.stderr)
        return 1

    seen: set[str] = set()
    merged_rules: list[str] = []
    per_source_summary: list[str] = []
    failed: list[str] = []

    for name, url in sources:
        print(f"Fetching: {name} ({urlparse(url).netloc})")
        raw = fetch(url)
        if raw is None:
            failed.append(f"{name} | {url}")
            per_source_summary.append(f"! FAILED    {name} — {url}")
            continue

        rules = extract_rules(raw)
        new_count = 0
        for rule in rules:
            if rule not in seen:
                seen.add(rule)
                merged_rules.append(rule)
                new_count += 1

        per_source_summary.append(
            f"! {len(rules):>7} rules ({new_count:>7} new) — {name} — {url}"
        )

    if not merged_rules:
        print("Every source failed to fetch — refusing to overwrite filters/merged.txt with an empty file.", file=sys.stderr)
        return 1

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    header = [
        "! Title: Sam's Merged AdGuard Home Filter",
        "! Description: Auto-merged, de-duplicated combination of multiple DNS filter lists.",
        "! Homepage: (set this to your GitHub repo URL)",
        f"! Last modified: {now}",
        f"! Sources: {len(sources)} configured, {len(sources) - len(failed)} fetched OK, {len(failed)} failed",
        f"! Total unique rules: {len(merged_rules)}",
        "!",
        "! ---- Per-source breakdown ----",
        *per_source_summary,
        "! -------------------------------",
        "!",
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(header) + "\n" + "\n".join(merged_rules) + "\n", encoding="utf-8")

    print(f"\nWrote {len(merged_rules)} unique rules from {len(sources) - len(failed)}/{len(sources)} sources to {OUTPUT_FILE}")
    if failed:
        print(f"\n{len(failed)} source(s) failed to fetch this run:")
        for f in failed:
            print(f"  - {f}")
        # Don't fail the whole job just because one mirror had a bad day —
        # the merged file is still valid and useful. Change this to `return 1`
        # if you'd rather the Action fail loudly when any source is down.

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
