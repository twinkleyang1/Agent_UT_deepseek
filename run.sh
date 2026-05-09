#!/bin/bash
# UT Generation Orchestrator - convenience launcher
# Usage: ./run.sh [command]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python src/main.py "$@"
