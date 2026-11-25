# Failure Modes

Severity follows `docs/REMEDIATION.md` (R-01–R-07).

## F-01 — Support invisible (R-01, MEDIUM)

Per-amendment vote counts are admin-only. Failure: an amendment sits
one vote short of majority for weeks and nobody outside the
validators can tell. Recovery: none available from public data;
enable the vote tracker (R-02) or publish counts.

## F-02 — Vote tracker off (R-02, MEDIUM)

`PF_ValidatorVoteTracking` is disabled, so the telemetry that would
diagnose F-01 does not exist. Recovery: propose and activate the
amendment itself (17/25 votes, 2-week hold).

## F-03 — Majority lost mid-hold (R-03, LOW)

Support dips below 17 votes at any flag ledger during the hold.
Failure: `tfLostMajority` removes the majority entry and the 2-week
clock restarts from zero (scenario S-c: 9 days of delay from a
2-day dip). Recovery: re-gain majority and hold it for a fresh
2 weeks; nothing of the earlier hold is preserved.

## F-04 — Validator goes quiet (R-04, LOW)

A validator silent for 24 h flips to "no" (`expiresAfter = 24h`).
At exactly 17 votes of support, one quiet validator loses the
majority (scenario S-f). Recovery: the validator resumes validating;
its vote is re-recorded at the next flag ledger, but the hold clock
has already reset.

## F-05 — Veto block (R-06, LOW)

9 vetoes (or non-supporters) cap max support at 16/25. Failure: the
amendment can never activate while they hold, and the veto count is
not observable, so the block is indistinguishable from low support.
Recovery: convince a vetoing validator to un-veto, or wait for the
trusted set to change.

## F-06 — Unsupported amendment reaches majority (R-01/R-03 context)

An amendment most validators have no code for reaches majority.
Failure: `firstUnsupportedExpected = majority time + 2 weeks`; if it
then activates, servers without code support are blocked
(`setAmendmentBlocked`, `Change.cpp:370`) until they upgrade.
Recovery: upgrade before the expected time, or veto it locally.

## F-07 — Majority-time override (U-04)

The testnet operator may have overridden `AMENDMENT_MAJORITY_TIME`
from the 2-week default via `[amendment_majority_time]`. The override
is node-local config and is not observable, so every activation
timeline in this pack assumes the default. If the override is set,
all timelines shift proportionally. Recovery: none from public data;
confirm the config with the operator.

## F-08 — Trusted-set shrinkage (R-05, INFO)

If validators leave the trusted set, the required votes fall in
absolute terms but the effective fraction rises (17/24 = 70.83%).
Failure mode: planning against the nominal 67% figure understates
the votes needed. Recovery: read the required-vote table for the
current trusted-set size (`data/lifecycle_model.json`).
