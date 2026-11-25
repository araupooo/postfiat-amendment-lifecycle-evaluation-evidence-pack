# Claim-to-Evidence Index

Labels: [MEASURED] observed on the live testnet or read from the pinned
source, with the script and vendored output that produced it;
[SIMULATED] produced by a local model or drill, not observed live;
[UNSUPPORTED] cannot be established from the public sources used here.
Line numbers are from the vendored files as committed (verify with
`grep -n`); JSON keys are given alongside for stability.

## Measured claims

| # | Claim | Evidence (script → output file:line) | Primary source |
|---|---|---|---|
| C-01 | Amendment inventory: 101 known amendments, 64 enabled / 37 disabled | `scripts/feature_inventory.py` → `outputs/feature_inventory.log:3` (`enabled=64 disabled=37`); raw `data/features_current.json` | `https://rpc.testnet.postfiat.org` (`feature`), 2026-11-25 19:27 UTC, validated ledger 8363822 |
| C-02 | Inventory unchanged vs the previous window: 0 changed entries (101 → 101, same enabled states) | `scripts/feature_inventory.py` → `outputs/feature_inventory.log:106`; `data/features_diff.json` (`changed_count: 0`) | Same RPC as C-01; baseline `data/features_baseline.json` (fetched 2026-11-25 18:25 UTC) |
| C-03 | `fixAmendmentMajorityCalc` is enabled on testnet, so the operative majority rule is the post-fix 67/100 rule with strict `>` | `scripts/feature_inventory.py` → `data/features_current.json:186` (`fixAmendmentMajorityCalc`, `enabled: true`); `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:2` | Same RPC as C-01; postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55`, `src/xrpld/app/misc/detail/AmendmentTable.cpp:328` |
| C-04 | Pre-fix threshold 204/256; post-fix threshold 67/100; majority hold 2 weeks (1,209,600 s) | `scripts/governance_audit.py` → `outputs/governance_audit.log:4,5` (G-02/G-03/G-04); `data/governance_params.json` (`pre_fix_threshold_*`, `post_fix_threshold_*`, `amendment_majority_time_seconds`) | postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55`, `include/xrpl/protocol/SystemParameters.h:83,85,88` |
| C-05 | Required votes at the live trusted set of 25: 17 post-fix (68.00%), 19 pre-fix counterfactual (76.00%) | `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:29`; `data/lifecycle_model.json` (`required_votes_table`, trusted 25) | Same source as C-04 plus `AmendmentTable.cpp:326-341,360-377` |
| C-06 | 2-week hold = 403,200 ledgers = 1,575.0 flag intervals at the measured cadence; 399,960.3 ledgers at the 24 h mean cadence | `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:30`; `data/lifecycle_model.json` (`activation_timing`) | Same source as C-04; cadence from C-07 / prior 24 h window |
| C-07 | Close cadence 3.0000 s mean (11 headers, n = 10 diffs [1, 1, 8, 1, 1, 8, 1, 1, 1, 7]) | `scripts/feature_inventory.py` → `data/close_sample.json` (`close_step_mean_s`, `close_step_diffs_s`) | `https://rpc.testnet.postfiat.org` (`ledger` + `server_info`), 2026-11-25 19:27 UTC |
| C-08 | Validated ledger 8363822, validation quorum 17, 21 peers, `server_state: full`, build 1.0.9, network 2025 | `scripts/feature_inventory.py` → `data/server_info.json` (`info.*`) | Same RPC as C-01 |
| C-09 | Validator vote records expire 24 h after the last validation from that validator; expired records flip to "no" | `scripts/governance_audit.py` → `outputs/governance_audit.log:9` (G-08) | postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55`, `AmendmentTable.cpp:153-175` (`expiresAfter = 24h`) |
| C-10 | Voting is evaluated at 256-ledger flag boundaries | `scripts/governance_audit.py` → `outputs/governance_audit.log:13` (G-12) | Same pin, `AmendmentTable.cpp:943-952` (`needValidatedLedger`) |
| C-11 | `tfGotMajority = 0x00010000`, `tfLostMajority = 0x00020000`; got-majority records `sfCloseTime` in the ledger | `scripts/governance_audit.py` → `outputs/governance_audit.log:17,18,19` (G-16/G-17/G-18) | Same pin, `include/xrpl/protocol/TxFlags.h:128-129`, `src/xrpld/app/tx/detail/Change.cpp:340-348` |
| C-12 | Config default majority time is the 2-week constant; overridable via `[amendment_majority_time]` (minutes/hours/days/weeks) | `scripts/governance_audit.py` → `outputs/governance_audit.log:21,22` (G-20/G-21) | Same pin, `src/xrpld/core/Config.h:248`, `src/xrpld/core/detail/Config.cpp:872-897` |
| C-13 | `PF_ValidatorVoteTracking` is disabled; the vote tracker is gated on it. `PF_AccountExclusion` is disabled; the exclusion managers are gated on it | `data/features_current.json:76` (`PF_ValidatorVoteTracking`, `enabled: false`), `:201` (`PF_AccountExclusion`, `enabled: false`); `scripts/governance_audit.py` → `outputs/governance_audit.log:23,24` (G-22/G-23) | Same RPC as C-01; same pin, `ValidatorVoteTracker.cpp:162`, `ExclusionManager.cpp:160` |
| C-14 | Per-amendment vote counts (`count` / `validations` / `threshold`) are admin-only; the public `feature` RPC returns only enabled / supported / name | `scripts/governance_audit.py` → `outputs/governance_audit.log:15` (G-14) | Same pin, `AmendmentTable.cpp:1000-1024` (`injectJson`, `:1019` admin gate) |
| C-15 | Unknown amendments are effectively vetoed already | `scripts/governance_audit.py` → `outputs/governance_audit.log:16` (G-15) | Same pin, `AmendmentTable.cpp:648` |
| C-16 | An unsupported amendment that activates blocks servers without code support (`setAmendmentBlocked`) | `scripts/governance_audit.py` → `outputs/governance_audit.log:20` (G-19) | Same pin, `Change.cpp:364-371` |
| C-17 | Once enabled, an amendment can never be disabled, only superseded | `scripts/governance_audit.py` (source read) | Same pin, `AmendmentTable.cpp:295-300` (one-way switch comment) |

## Simulated claims

| # | Claim | Evidence (script → output file:line) | Primary source |
|---|---|---|---|
| S-01 | Required-vote table for trusted sets 1..25 under both rules (post-fix strict `>`, pre-fix `>=`) | `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:4-28` (one line per trusted size); `data/lifecycle_model.json` (`required_votes_table`) | Threshold formulas C-04/C-05 applied analytically |
| S-02 | S-a steady 17/25 majority activates on day 14 | `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:49` | Model, `docs/LIFECYCLE_MODEL.md` |
| S-03 | S-b 16/25 steady never activates (28-day horizon) | Same script → `outputs/lifecycle_simulation.log:80` | Model |
| S-04 | S-c majority lost day 7, re-gained day 9, activates day 23 (2-day dip costs 9 days) | Same script → `outputs/lifecycle_simulation.log:106` | Model + `tfLostMajority` reset (C-11) |
| S-05 | S-d eight vetoes (max support 17/25) still activates day 14 | Same script → `outputs/lifecycle_simulation.log:123` | Model |
| S-06 | S-e nine vetoes (max support 16/25) never activates | Same script → `outputs/lifecycle_simulation.log:154` | Model |
| S-07 | S-f 24 h expiry dip (16/25 on day 5, back day 6) activates day 20 (5 days of hold discarded) | Same script → `outputs/lifecycle_simulation.log:177` | Model + 24 h expiry (C-09) |
| S-08 | S-g pre-fix rule at 17/25 support never activates (19 required) | Same script → `outputs/lifecycle_simulation.log:208` | Model + pre-fix rule (C-04) |
| S-09 | Effective required fraction exceeds the nominal 67% for most trusted sizes: 68.00% at 25, 70.83% at 24, 100% at 2 and 3 | `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:4-28`; `data/lifecycle_model.json` (`required_votes_table`) | Integer division + strict `>` (C-04/C-05) |
| S-10 | 9 vetoes permanently block activation at trusted 25 (max support 16 < 17) | `scripts/lifecycle_model.py` → `outputs/lifecycle_simulation.log:211` | Model + veto mechanics (C-15) |

## Unsupported claims

| # | Claim | Why it cannot be established |
|---|---|---|
| U-01 | Live support fraction for any specific disabled amendment | Per-amendment vote counts are admin-only (C-14); the public RPC exposes no vote data. |
| U-02 | Whether any disabled amendment currently holds a majority | Same as U-01; a majority in progress is invisible from public data. |
| U-03 | Validators' individual veto lists | Veto config is node-local and not gossiped; a non-vote is indistinguishable from a veto. |
| U-04 | Whether the testnet operator overrode `AMENDMENT_MAJORITY_TIME` from the 2-week default | Node-local config (C-12); not observable from the public RPC. |
| U-05 | Real activation timing for any specific amendment | No amendment changed state across the two windows (C-02); no activation is in progress as far as public data shows, and U-01 blocks measuring one. |
| U-06 | Contents of the vote-tracker telemetry | `PF_ValidatorVoteTracking` is disabled (C-13); the tracker produces no data while off. |
