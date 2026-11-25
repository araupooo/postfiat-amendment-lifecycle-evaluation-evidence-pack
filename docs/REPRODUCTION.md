# Reproduction

## One command

```sh
bash reproduce.sh
```

Expected output ends with `REPRODUCE OK` and exit code 0. The full
output is saved to `outputs/reproduce_selfcheck.log`, which is
byte-identical to a fresh run of the same command (no timestamps, no
absolute paths, no network access in the reproduce path).

## What reproduce.sh does

1. `bash scripts/run_all.sh` — runs the three checks in order, each
   writing a verbose per-step log to `outputs/`:
   - `scripts/feature_inventory.py` (M-01): replays the vendored
     inventory (`data/features_current.json`), recomputes the diff
     against `data/features_baseline.json`, prints one line per
     amendment (101 lines) plus summary lines.
   - `scripts/governance_audit.py` (M-02): re-greps the pinned
     source constants. NOTE: this check reads the pinned checkout
     at `~/workspace/postfiatd-pin-0085a1f` by default; to reproduce
     on another machine, clone postfiatd at commit
     `0085a1ff885d6a446369cf73a4430f75af22be55` and pass
     `--pin <path>`. The check prints one PASS line per check
     (G-01–G-23) with exact file:line citations.
   - `scripts/lifecycle_model.py` (M-03): recomputes the
     required-vote tables, activation timing, and the seven day-tick
     scenarios, printing one line per table row and per simulation
     tick.
2. `bash verify_digests.sh` — `sha256sum -c SHA256SUMS` over every
   pack file except the manifest itself and
   `outputs/reproduce_selfcheck.log`. The self-check log cannot be in
   its own digest set because it embeds the digest verification
   output; it is verified instead by re-running `bash reproduce.sh`
   and confirming the regenerated log is byte-identical (same
   SHA-256) to the vendored one.

## Live fetch (build time only, not part of reproduce)

```sh
python3 scripts/feature_inventory.py --fetch-live
```

POSTs `feature` and `server_info` to
`https://rpc.testnet.postfiat.org`, fetches 11 ledger headers, and
rewrites `data/features_current.json`, `data/server_info.json`,
`data/close_sample.json`, and `data/features_diff.json`. The
vendored files in this pack are the output of that fetch
(2026-11-25 19:27 UTC, validated ledger 8363822).

## Environment

- Python 3.12, standard library only (no third-party packages).
- `bash`, `sha256sum` (coreutils).
- CI (`.github/workflows/ci.yml`) runs the same `bash reproduce.sh`
  on `ubuntu-latest` with Python 3.12 and no secrets.
- The pinned postfiatd checkout is needed only for M-02; M-01 and
  M-03 replay vendored data and run anywhere.
