# Lifecycle Model

Computed by `scripts/lifecycle_model.py` from the vendored data
(`data/features_current.json`, `data/close_sample.json`,
`data/governance_params.json`). Machine-readable output:
`data/lifecycle_model.json`. Verbose per-step log:
`outputs/lifecycle_simulation.log`.

## Rules (re-derived from source, not assumed)

Operative rule on testnet: `fixAmendmentMajorityCalc` is enabled, so
the post-fix rule applies (`AmendmentTable.cpp:326-341`, `:360-377`):

- `threshold = max(1, floor(trusted * 67 / 100))`
- passes iff `votes > threshold` (strict), except `trusted == 1`,
  where `>=` applies.
- Pre-fix counterfactual (for comparison only): `threshold = max(1,
  floor(trusted * 204 / 256))`, passes iff `votes >= threshold`.

Integer division truncates. The strict `>` means the effective
required fraction exceeds the nominal 67% for almost every
trusted-set size. At the live trusted set of 25: threshold 16,
required 17 votes (68.00%). Under the pre-fix rule the same set
would need 19 votes (76.00%).

## Required-vote table (trusted 1..25)

Full table in `data/lifecycle_model.json` (`required_votes_table`).
Selected rows:

| Trusted | Post-fix required | Post-fix fraction | Pre-fix required | Pre-fix fraction |
|---|---|---|---|---|
| 1 | 1 | 100.00% | 1 | 100.00% |
| 2 | 2 | 100.00% | 1 | 50.00% |
| 5 | 4 | 80.00% | 3 | 60.00% |
| 10 | 7 | 70.00% | 7 | 70.00% |
| 15 | 11 | 73.33% | 11 | 73.33% |
| 20 | 14 | 70.00% | 15 | 75.00% |
| 24 | 17 | 70.83% | 19 | 79.17% |
| 25 | 17 | 68.00% | 19 | 76.00% |

## Activation timing

- Majority hold: 1,209,600 s (2 weeks, `defaultAmendmentMajorityTime`).
- At the measured close cadence 3.0000 s (11 headers, n = 10 diffs,
  2026-11-25 19:27 UTC): 403,200 ledgers = 1,575.0 flag intervals.
- At the 24 h mean cadence 3.0243 s (2026-11-24 → 25 window, 28,800
  ledgers): 399,960.3 ledgers = 1,562.3 flag intervals.
- Majority is recorded at flag-ledger boundaries (every 256 ledgers);
  activation is evaluated at those boundaries, so the earliest
  activation is the first flag ledger at or after
  `majorityTime + 2 weeks`.

## Day-tick simulations

One tick = one day. Majority is recorded on the first day support
reaches the required votes; it is lost the first day support drops
below; re-gain restarts the 14-day clock from scratch. Day
granularity is a model simplification: the real system records
majority at flag ledgers, so a real activation lands on a flag
ledger, not a calendar day.

| Scenario | Support | Result |
|---|---|---|
| S-a steady majority | 17/25 from day 0 | Activates day 14 |
| S-b one vote short | 16/25 steady | Never activates |
| S-c majority lost and regained | 17/25, dip to 15/25 days 7–8, back to 17/25 day 9 | Activates day 23 (lost day 7, re-recorded day 9, +14) |
| S-d eight vetoes | max support 17/25 | Activates day 14 |
| S-e nine vetoes | max support 16/25 | Never activates |
| S-f 24 h expiry dip | 17/25, dip to 16/25 day 5, back day 6 | Activates day 20 (5 days of accumulated hold discarded) |
| S-g pre-fix rule at 17 votes | 17/25, required 19 | Never activates |

## Rollback / negative cases

1. **Lost majority resets the clock.** `tfLostMajority` removes the
   majority entry (`Change.cpp:308-309`); a re-gained majority records
   a fresh `sfCloseTime`. Scenario S-c quantifies it: a 2-day dip
   costs 9 days of delay (activation day 14 → 23).
2. **Veto blocking.** 9 vetoes (or non-supporters) cap max support at
   16/25, below the required 17 — the amendment can never activate
   while they hold. 8 vetoes leave exactly 17 supporters and the
   amendment still activates (S-d). Veto lists are node-local config
   and are not gossiped, so the veto count itself is not observable.
3. **24 h vote expiry.** A validator silent for 24 h flips to "no"
   (`TrustedVotes::expiresAfter`, `AmendmentTable.cpp:172`). Scenario
   S-f: a 1-day dip on day 5 discards 5 days of accumulated hold.
4. **Unsupported activation.** An unsupported amendment that reaches
   majority has `firstUnsupportedExpected = majority time + 2 weeks`
   (`AmendmentTable.cpp:988`); if it then activates, servers without
   code support are blocked (`setAmendmentBlocked`, `Change.cpp:370`).
5. **Single-validator exception.** At `trusted == 1` the pass test is
   `>=`, not `>` (`AmendmentTable.cpp:372-374`).
6. **Truncation edge.** `floor(t * 67 / 100)` plus strict `>` pushes
   the effective fraction above 67% for nearly every trusted-set
   size; at t = 2 and t = 3 the requirement is 100%.
7. **One-way enable.** Once enabled, an amendment can never be
   disabled, only superseded (`AmendmentTable.cpp:298`). There is no
   rollback of an enabled amendment.

## Assumptions (stated, not hidden)

- A-1: every validator uses the published testnet list (25
  validators); the live `validation_quorum` of 17 corroborates a
  25-UNL under the 67% rule, but per-validator UNL contents are not
  observable.
- A-2: day-tick granularity approximates flag-ledger majority
  recording; real activation lands on a flag ledger.
- A-3: the operator has not overridden `AMENDMENT_MAJORITY_TIME`
  from the 2-week default (node-local config, not observable).
- A-4: close cadence stays near 3.0 s over a 2-week hold; the
  conversion is order-of-magnitude, not a prediction.
