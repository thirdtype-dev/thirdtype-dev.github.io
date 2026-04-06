#!/usr/bin/env python3
"""Keep only the latest two <article class="report"> sections in report/index.html.

This is a small safety script for the public market report page. It assumes the
page structure is stable:
- one <main> wrapper
- a sequence of top-level <article class="report"> blocks
- each article already contains the full rendered report content

When publishing, run this script before committing so older report sections
cannot linger on the public page.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPORT_RE = re.compile(
    r'<article class="report">.*?</article>',
    re.DOTALL,
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: trim_latest_reports.py PATH_TO_report/index.html", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
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

    # Rebuild using only the first two report articles.
    rebuilt = prefix + body + suffix
    path.write_text(rebuilt, encoding="utf-8")

    print(f"trimmed {len(articles)} report sections down to 2 in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
