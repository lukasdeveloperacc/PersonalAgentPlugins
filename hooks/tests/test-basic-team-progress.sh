#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
uv run --script "$ROOT/hooks/tests/test_basic_team_progress.py"
