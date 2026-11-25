# Sources

Primary sources only. Every claim in `docs/CLAIMS.md` traces to one of
these. Line numbers are from the vendored files as committed (verify
with `grep -n`); the pinned postfiatd checkout is
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, release 1.0.9).

## 1. Pinned postfiatd source (commit 0085a1ff885d6a446369cf73a4430f75af22be55)

| File | What it establishes |
|---|---|
| `include/xrpl/protocol/SystemParameters.h:83,85,88` | Pre-fix threshold 204/256, post-fix threshold 67/100, majority hold 2 weeks (`defaultAmendmentMajorityTime`). |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:93-300` | `TrustedVotes`: vote records expire after 24 h (`expiresAfter = 24h`, :172); `getVotes` counts only validators with a live record (:270-284). |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:295-298` | Amendment state: vote defaults down (:295); enabled is a one-way switch (:298). |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:326-341` | `computeThreshold`: integer-division threshold, rule selected on `fixAmendmentMajorityCalc`. |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:360-377` | `passes()`: strictly greater than when the fix is enabled; `>=` pre-fix; single-validator exception. |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:600-648` | Veto config parsing (`[veto_amendments]`); unknown amendments are effectively vetoed (:648). |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:736-760` | `veto()` / `unVeto()` set the local vote down / up. |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:813-842` | `doValidation()` / `getDesired()`: vote only for supported, non-vetoed, not-yet-enabled amendments. |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:846-941` | `doVoting()`: `tfGotMajority` (:908) / `tfLostMajority` (:914); activation requires the majority held for `majorityTime_` (:918). |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:943-952` | `needValidatedLedger()`: voting evaluated at 256-ledger flag boundaries. |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:955-992` | `doValidatedLedger()`: `firstUnsupportedExpected_ = majority time + majorityTime_` (:988). |
| `src/xrpld/app/misc/detail/AmendmentTable.cpp:1000-1024` | `injectJson()`: per-amendment vote counts (`count` / `validations` / `threshold`) are admin-only (:1019). |
| `include/xrpl/protocol/TxFlags.h:128-129` | `tfGotMajority = 0x00010000`, `tfLostMajority = 0x00020000`. |
| `src/xrpld/app/tx/detail/Change.cpp:287-379` | `applyAmendment()`: got-majority records `sfCloseTime` (:346); no flags enables the amendment (:357-358, :364); unsupported activation blocks the server (:370). |
| `src/xrpld/core/Config.h:248` | `AMENDMENT_MAJORITY_TIME` defaults to `defaultAmendmentMajorityTime`. |
| `src/xrpld/core/detail/Config.cpp:872-897` | `[amendment_majority_time]` config override (minutes/hours/days/weeks). |
| `src/xrpld/app/main/Application.cpp:1286-1291` | Majority time wired from config into the amendment table. |
| `src/xrpld/app/misc/ValidatorVoteTracker.cpp:162`, `ValidatorVoteTracker.h:86` | Vote tracker gated on `featurePF_ValidatorVoteTracking`. |
| `src/xrpld/app/misc/ExclusionManager.cpp:160`, `ValidatorExclusionManager.cpp:145` | Exclusion managers gated on `featurePF_AccountExclusion`. |
| `src/xrpld/app/consensus/RCLConsensus.cpp:873-874` | `PF_AccountExclusion`: exclusion-list changes ride in validations. |

## 2. Live testnet data (public RPC `https://rpc.testnet.postfiat.org`)

| Data | File | Fetched |
|---|---|---|
| Full amendment inventory (`feature` RPC): 101 features, 64 enabled / 37 disabled | `data/features_current.json` | 2026-11-25 19:27 UTC (validated ledger 8363822) |
| Baseline inventory for the diff (101 features) | `data/features_baseline.json` | 2026-11-25 18:25 UTC (previous window) |
| `server_info` snapshot: validated ledger 8363822, quorum 17, 21 peers, `full`, build 1.0.9, network 2025 | `data/server_info.json` | 2026-11-25 19:27 UTC |
| Close cadence: 11 headers, mean 3.0000 s, diffs [1, 1, 8, 1, 1, 8, 1, 1, 1, 7] | `data/close_sample.json` | 2026-11-25 19:27 UTC |

## 3. Prior measurement windows (cited, not copied)

| Source | Use |
|---|---|
| 24 h window 2026-11-24 → 25, close segment mean 3.0243 s, 28,800 ledgers | Cross-check for the activation-timing conversion in `data/lifecycle_model.json`. |
| Previous-window feature inventory (101 features, 64/37) | Baseline for the diff in `data/features_diff.json` (0 changes). |

## What is NOT a source here

- Per-amendment live vote counts: not exposed by the public RPC
  (admin-only, see `AmendmentTable.cpp:1019`). Any claim about current
  support for a specific disabled amendment is [UNSUPPORTED].
- Validators' individual veto lists: node-local config, not gossiped.
- Whether the testnet operator overrode `AMENDMENT_MAJORITY_TIME`
  from the 2-week default: node-local config, not observable.
