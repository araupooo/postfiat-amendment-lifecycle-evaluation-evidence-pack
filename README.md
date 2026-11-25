# PFTL Amendment Lifecycle Evaluation Evidence Pack

An evaluation of the full lifecycle of a PostFiat protocol amendment
— proposal, validator voting, activation threshold, majority time,
stalled support, veto, and rollback/negative cases — built from the
live testnet amendment inventory and the pinned postfiatd source
(commit `0085a1ff885d6a446369cf73a4430f75af22be55`, release 1.0.9).

Every substantive claim is labelled [MEASURED] (observed on the live
testnet or read from the pinned source, with the script and raw
output that produced it), [SIMULATED] (produced by a local model —
not observed live), or [UNSUPPORTED] (cannot be established from the
public sources used here). See `docs/CLAIMS.md`.

## Headline results

- **Inventory:** 101 known amendments — 64 enabled, 37 disabled —
  unchanged against the previous window (0 changes).
- **Operative rule:** `fixAmendmentMajorityCalc` is enabled, so the
  post-fix rule applies: threshold `max(1, floor(trusted * 67 /
  100))`, passes iff votes are strictly greater. At the live trusted
  set of 25: **17 votes (68.00%)** required, held for **2 weeks**
  (1,209,600 s = 403,200 ledgers at the measured 3.0 s cadence).
- **Fastest activation:** 14 days from first majority (scenario S-a).
- **One vote short (16/25):** never activates. **Nine vetoes:**
  never activates. **A 2-day dip below majority mid-hold:** delays
  activation by 9 days (day 14 → 23).
- **Main gap:** live per-amendment vote counts are admin-only, so
  current support for any disabled amendment is unobservable from
  public data — and the vote-tracking amendment that would close
  that gap (`PF_ValidatorVoteTracking`) is itself disabled.

## Layout

- `scripts/` — the three checks (`feature_inventory.py`,
  `governance_audit.py`, `lifecycle_model.py`), the shared
  `rpc_client.py`, and `run_all.sh`. Every check logs each step as
  it happens (verbose per-step lines, not just a final summary).
- `data/` — live inventory, baseline inventory, diff, server info,
  close-cadence sample, governance parameters, lifecycle model, and
  the source pin.
- `docs/` — claim index, decision memo, remediation guidance,
  failure modes, governance-parameter audit, lifecycle model,
  reproduction guide, sources.
- `outputs/` — unedited verbose logs from the three checks plus the
  reproduce self-check log.
- `reproduce.sh`, `verify_digests.sh`, `SHA256SUMS`,
  `.github/workflows/ci.yml` — one-command fresh-clone reproduction
  with digest verification.

## Reproduce

```sh
bash reproduce.sh   # expect exit 0 and REPRODUCE OK
```

See `docs/REPRODUCTION.md` for details, including the build-time
live-fetch step. No checkout is needed to reproduce.
