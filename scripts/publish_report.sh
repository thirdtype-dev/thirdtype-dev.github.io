#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
REPORT_HTML="$ROOT_DIR/report/index.html"
HERMES_AGENT_ROOT="${HERMES_AGENT_ROOT:-/Users/thirdtype/.hermes/hermes-agent}"
RENDERER="$HERMES_AGENT_ROOT/website/scripts/render_report.py"

if [[ ! -f "$RENDERER" ]]; then
  echo "Missing renderer: $RENDERER" >&2
  exit 1
fi

rm -rf "$ROOT_DIR/report/articles"
python3 "$RENDERER" --output "$REPORT_HTML"
python3 "$ROOT_DIR/scripts/trim_latest_reports.py" "$REPORT_HTML"

git -C "$ROOT_DIR" add report

git -C "$ROOT_DIR" commit -m "Publish latest two reports" || {
  echo "No changes to commit."
  exit 0
}

git -C "$ROOT_DIR" push origin main
