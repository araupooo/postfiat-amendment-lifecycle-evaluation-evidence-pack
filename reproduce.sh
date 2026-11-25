#!/usr/bin/env bash
# Reproduce every check from a fresh clone and verify all digests.
# Deterministic: no timestamps, no absolute paths, no network.
# Usage: bash reproduce.sh   (run from the pack root)
# Exit code 0 and "REPRODUCE OK" mean every check passed and every
# vendored file matches its recorded SHA-256.
set -e
cd "$(dirname "$0")"
bash scripts/run_all.sh
bash verify_digests.sh
{
  echo "== feature_inventory =="
  cat outputs/feature_inventory.log
  echo "== governance_audit =="
  cat outputs/governance_audit.log
  echo "== lifecycle_simulation =="
  cat outputs/lifecycle_simulation.log
  echo "== digest verification =="
  bash verify_digests.sh
  echo "REPRODUCE OK"
} > outputs/reproduce_selfcheck.log
tail -5 outputs/reproduce_selfcheck.log
echo "REPRODUCE OK"
