#!/usr/bin/env python3
"""Keep only the latest two <article class="report"> sections in report/index.html.

Default behavior:
- trim older report sections so only the newest two remain

Validation mode:
- pass --check to fail if more than two report sections are present

This is a small safety script for the public market report page. It assumes the
page structure is stable:
- one <main> wrapper
- a sequence of top-level <article class="report"> blocks
- each article already contains the full rendered report content
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPORT_RE = re.compile(r'<article class="report">.*?</article>', re.DOTALL)


def trim_latest_two(path: Path) -> int:
    html = path.read_text(encoding="utf-8")
    articles = list(REPORT_RE.finditer(html))

    if len(articles) <= 2:
        print(f"ok: found {len(articles)} report sections; nothing to trim")
        return 0

    keep = articles[:2]
    start = keep[0].start()
    end = keep[-1].end()

    prefix = html[:start]
    body = html[start:end]
    suffix = html[articles[-1].end():]

    rebuilt = prefix + body + suffix
    path.write_text(rebuilt, encoding="utf-8")

    print(f"trimmed {len(articles)} report sections down to 2 in {path}")
    return 0


def check_latest_two(path: Path) -> int:
    html = path.read_text(encoding="utf-8")
    articles = list(REPORT_RE.finditer(html))
    if len(articles) <= 2:
        print(f"ok: found {len(articles)} report sections")
        return 0

    print(f"error: found {len(articles)} report sections; keep only the latest two", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to report/index.html")
    parser.add_argument("--check", action="store_true", help="Validate only; do not modify the file")
    args = parser.parse_args()

    path = Path(args.path)
    if args.check:
        return check_latest_two(path)
    return trim_latest_two(path)


if __name__ == "__main__":
    raise SystemExit(main())
