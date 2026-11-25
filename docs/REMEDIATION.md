# Remediation Guidance

Severity scale: HIGH = exploitable or data-exposing now; MEDIUM =
weakens a security boundary or mainnet readiness; LOW = hygiene or
observability; INFO = context, no action required.

## R-01 — MEDIUM: per-amendment vote counts are not publicly observable

[MEASURED] The public `feature` RPC returns only enabled / supported /
name per amendment. The vote counts that would show whether a disabled
amendment is close to activation (`count` / `validations` /
`threshold`) are gated on `isAdmin` in `injectJson`
(`AmendmentTable.cpp:1019`). Consequence: for all 37 disabled
amendments, current support is unknowable from public data (U-01,
U-02). A stalled amendment and a vetoed amendment look identical.

Guidance: expose the vote counts on the public `feature` response, or
enable `PF_ValidatorVoteTracking` (see R-02). Until then, any claim
about a specific amendment's support is unsupported, not measured.

## R-02 — MEDIUM: the vote-tracking amendment is itself disabled

[MEASURED] `PF_ValidatorVoteTracking` is disabled on testnet
(`data/features_current.json:76`), and the vote tracker is gated on
it (`ValidatorVoteTracker.cpp:162`). The facility that would close
R-01 exists in the code but is off.

Guidance: evaluate enabling `PF_ValidatorVoteTracking` on testnet
first. It needs 17/25 validator votes held for 2 weeks like any
other amendment; while it is off, no vote telemetry is produced.

## R-03 — LOW: a lost majority restarts the full 2-week clock

[SIMULATED] `tfLostMajority` removes the majority entry
(`Change.cpp:308-309`); a re-gained majority records a fresh
`sfCloseTime`. Scenario S-c quantifies it: a 2-day dip below
threshold delays activation by 9 days (day 14 → 23). This is the
designed behavior, but operators should know a flapping validator
can keep an amendment perpetually stalled.

Guidance: no code change. When scheduling an amendment, monitor
support continuously through the hold window; treat any dip below
17 votes as a restart, not a pause.

## R-04 — LOW: 24 h vote expiry can cost a majority

[MEASURED] Vote records expire 24 h after a validator's last
validation (`AmendmentTable.cpp:172`). Scenario S-f: a 1-day silence
discards 5 days of accumulated hold (activation day 14 → 20).

Guidance: no code change. Validator uptime through the hold window
is part of activation; a single validator going quiet for a day at
exactly 17 votes of support loses the majority.

## R-05 — INFO: the effective required fraction exceeds 67%

[SIMULATED] Integer division (`floor(t * 67 / 100)`) plus the strict
`>` test push the effective requirement above the nominal ratio for
nearly every trusted-set size: 68.00% at 25, 70.83% at 24, 100% at
2 and 3. The full table is in `data/lifecycle_model.json`.

Guidance: document the required-vote table rather than the nominal
67% figure; operators planning an amendment should read the table
row for the current trusted-set size.

## R-06 — LOW: 9 vetoes permanently block activation

[SIMULATED] Vetoes are node-local config and are not gossiped, so the
veto count is unobservable (U-03). At trusted 25, 9 vetoes cap max
support at 16 < 17 (scenario S-e). The amendment can never activate
while they hold.

Guidance: before proposing an amendment, count committed
non-supporters. 9 is the blocking number on the current set; it
falls as the trusted set shrinks (see the required-vote table).

## R-07 — INFO: `PF_AccountExclusion` is disabled

[MEASURED] `PF_AccountExclusion` is disabled
(`data/features_current.json:201`); the exclusion managers are
gated on it (`ExclusionManager.cpp:160`,
`ValidatorExclusionManager.cpp:145`). The validator-exclusion
machinery is dormant.

Guidance: none required. Noted because the exclusion feature and
its vote-tracking companion are the only two PostFiat-specific
amendments, and both are off.
