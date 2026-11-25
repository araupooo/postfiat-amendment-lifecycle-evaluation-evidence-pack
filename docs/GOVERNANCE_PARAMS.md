# Governance Parameter Audit

Every parameter below was re-derived by `scripts/governance_audit.py`
(checks G-01–G-23, log `outputs/governance_audit.log`) from the pinned
postfiatd source (commit `0085a1ff885d6a446369cf73a4430f75af22be55`).
Machine-readable form: `data/governance_params.json`.

## Thresholds

| Parameter | Value | Source |
|---|---|---|
| Pre-fix majority threshold | 204/256 (79.6875%) | `include/xrpl/protocol/SystemParameters.h:83` |
| Post-fix majority threshold (operative) | 67/100 | `include/xrpl/protocol/SystemParameters.h:85` |
| Operative rule selector | `fixAmendmentMajorityCalc` enabled on testnet (live `feature` RPC) | `src/xrpld/app/misc/detail/AmendmentTable.cpp:328`, `data/features_current.json` |
| Threshold formula (post-fix) | `threshold = max(1, floor(trusted * 67 / 100))`; passes iff `votes > threshold` | `AmendmentTable.cpp:326-341`, `:360-377` |
| Threshold formula (pre-fix) | `threshold = max(1, floor(trusted * 204 / 256))`; passes iff `votes >= threshold` | Same lines |
| Single-validator exception | `trustedValidations == 1` → `>=` instead of `>` | `AmendmentTable.cpp:372-374` |
| Required votes, trusted = 25 (live) | 17 post-fix (68.00%); 19 pre-fix counterfactual (76.00%) | `data/lifecycle_model.json` table, computed by `scripts/lifecycle_model.py` |
| Effective required fraction | Exceeds the nominal ratio for most trusted-set sizes (integer division + strict `>`): 100% at t = 2, 3; 70.83% at t = 24; 68.00% at t = 25 | Same table |

## Majority hold time

| Parameter | Value | Source |
|---|---|---|
| Default majority hold | 2 weeks = 1,209,600 s | `include/xrpl/protocol/SystemParameters.h:88` |
| Config default | `AMENDMENT_MAJORITY_TIME = defaultAmendmentMajorityTime` | `src/xrpld/core/Config.h:248` |
| Config override | `[amendment_majority_time]` section, value in minutes/hours/days/weeks | `src/xrpld/core/detail/Config.cpp:872-897` |
| Wiring | Config value passed to `make_AmendmentTable` | `src/xrpld/app/main/Application.cpp:1286-1291` |
| Activation condition | Majority recorded at `majorityTime`; enabled only when `majorityTime + majorityTime_ <= closeTime` and the local vote is up | `AmendmentTable.cpp:918`, `Change.cpp:357-364` |
| Hold in ledgers (measured cadence 3.0000 s) | 403,200 ledgers = 1,575.0 flag intervals | `data/lifecycle_model.json` |
| Hold in ledgers (24 h mean cadence 3.0243 s) | 399,960.3 ledgers = 1,562.3 flag intervals | Same file |

## Voting mechanics

| Parameter | Value | Source |
|---|---|---|
| Voting evaluated at | 256-ledger flag boundaries (`needValidatedLedger`) | `AmendmentTable.cpp:943-952` |
| Vote record expiry | 24 h after the last validation from that validator (`expiresAfter = 24h`); expired records flip to "no" | `AmendmentTable.cpp:153-175` |
| Votes counted | Only validators with a live (unexpired) vote record count toward `trustedValidations` | `AmendmentTable.cpp:270-284` |
| Majority recording | `tfGotMajority` (0x00010000) pseudo-transaction records `sfCloseTime` in the ledger | `include/xrpl/protocol/TxFlags.h:128`, `Change.cpp:340-348` |
| Majority loss | `tfLostMajority` (0x00020000) removes the majority entry; the 2-week clock restarts from scratch on re-gain | `TxFlags.h:129`, `Change.cpp:308-309`, `AmendmentTable.cpp:910-915` |
| Who votes | Only supported, non-vetoed, not-yet-enabled amendments (`doValidation` / `getDesired`) | `AmendmentTable.cpp:813-842` |
| Veto | Local `[veto_amendments]` config sets the vote down; vetoed amendments are never announced as supported | `AmendmentTable.cpp:600-648`, `:736-760` |
| Unknown amendments | Effectively vetoed already | `AmendmentTable.cpp:648` |
| Unsupported majority | `firstUnsupportedExpected = majority time + majorityTime_`; if it then activates, servers without code support are blocked (`setAmendmentBlocked`) | `AmendmentTable.cpp:955-992`, `Change.cpp:364-371` |
| Enabled amendments | One-way switch: never disabled, only superseded by a subsequent amendment | `AmendmentTable.cpp:295-300` |
| Per-amendment vote counts | Admin-only in `getJson` (`count` / `validations` / `threshold`); the public `feature` RPC returns only enabled / supported / name | `AmendmentTable.cpp:1000-1024` |

## PostFiat-specific amendments

| Amendment | Live state | What gates on it |
|---|---|---|
| `PF_ValidatorVoteTracking` | Disabled | `ValidatorVoteTracker` (`ValidatorVoteTracker.cpp:162`, `ValidatorVoteTracker.h:86`) |
| `PF_AccountExclusion` | Disabled | `ExclusionManager` (`ExclusionManager.cpp:160`), `ValidatorExclusionManager` (`ValidatorExclusionManager.cpp:145`); exclusion-list changes ride in validations (`RCLConsensus.cpp:873-874`) |
