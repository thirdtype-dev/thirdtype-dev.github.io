#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
REPORT_HTML="$ROOT_DIR/report/index.html"

python3 "$ROOT_DIR/scripts/trim_latest_reports.py" "$REPORT_HTML"

git -C "$ROOT_DIR" add report/index.html

git -C "$ROOT_DIR" commit -m "Publish latest two reports" || {
  echo "No changes to commit."
  exit 0
}

git -C "$ROOT_DIR" push origin main
