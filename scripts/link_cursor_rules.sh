#!/usr/bin/env bash
# Back-compat wrapper — prefer scripts/link_ai_markdown.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec bash "$ROOT/link_ai_markdown.sh" "$@"
