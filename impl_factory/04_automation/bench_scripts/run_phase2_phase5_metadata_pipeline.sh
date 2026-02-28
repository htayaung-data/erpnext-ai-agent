#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

bash impl_factory/04_automation/bench_scripts/run_phase2_phase4_metadata_pipeline.sh
