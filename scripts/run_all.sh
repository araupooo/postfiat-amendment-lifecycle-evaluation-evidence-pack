#!/usr/bin/env bash
# Run every check in order. Each script logs verbosely, one line per
# step/event, to its own outputs/*.log file. No network access: all
# checks replay the vendored data/*.json files.
# Usage: bash scripts/run_all.sh   (run from the pack root)
set -e
cd "$(dirname "$0")/.."
mkdir -p outputs
python3 scripts/feature_inventory.py > outputs/feature_inventory.log
python3 scripts/governance_audit.py > outputs/governance_audit.log
python3 scripts/lifecycle_model.py > outputs/lifecycle_simulation.log
echo "ALL CHECKS DONE"
