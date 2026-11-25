# Decision Memo — Amendment Lifecycle on the PFTL Testnet

## Bottom line

- The testnet runs 101 known amendments: **64 enabled, 37 disabled**
  (`data/features_current.json`, fetched 2026-11-25 19:27 UTC). The
  inventory is **unchanged** against the previous window (0 changes,
  `data/features_diff.json`).
- The operative majority rule is the **post-fix 67/100 rule, strictly
  greater**: with 25 trusted validators, an amendment needs **17
  votes** and must hold them for **2 weeks** (1,209,600 s = 403,200
  ledgers at the measured 3.0 s cadence) before it activates.
- The single most important gap is **observability, not mechanics**:
  live per-amendment vote counts are admin-only, so no one can see
  from public data whether any disabled amendment is close to
  activation, stalled, or vetoed (R-01). The vote-tracking amendment
  that would close that gap (`PF_ValidatorVoteTracking`) is itself
  disabled (R-02).

## Live amendments (64 enabled)

All 38 enabled `fix*` amendments plus 26 named ones, including
`fixAmendmentMajorityCalc` (the operative rule), `NegativeUNL`,
`NonFungibleTokensV1_1`, `AMM`, `Credentials`, `DID`, `PriceOracle`,
`TicketBatch`, `DeepFreeze`, `HardenedValidations`,
`RequireFullyCanonicalSig`. Full list in `data/features_current.json`.

## Stalled amendments (37 disabled)

"Disabled" here means only "not enabled on this ledger". The public
RPC cannot distinguish "never proposed", "proposed but below
threshold", and "vetoed" — that distinction is exactly what R-01
makes unobservable. Do not read intent into the list.

PostFiat-specific (2): `PF_AccountExclusion`,
`PF_ValidatorVoteTracking`.

Upstream features (19 named): `CryptoConditions`,
`CryptoConditionsSuite`, `EnforceInvariants`, `Escrow`,
`FeeEscalation`, `FlowCross`, `LendingProtocol`, `MPTokensV1`,
`MultiSign`, `NonFungibleTokensV1`, `PayChan`, `PermissionedDEX`,
`PermissionedDomains`, `SingleAssetVault`, `SortedDirectories`,
`TickSize`, `TokenEscrow`, `TrustSetAuth`, `XChainBridge`.
Note `NonFungibleTokensV1` is disabled while `NonFungibleTokensV1_1`
is enabled — the superseding pattern the code anticipates for
one-way amendments.

Fixes (16): `fix1201`, `fix1368`, `fix1373`, `fix1512`, `fix1523`,
`fix1528`, `fixAMMClawbackRounding`, `fixDirectoryLimit`,
`fixIncludeKeyletFields`, `fixMPTDeliveredAmount`, `fixNFTokenDirV1`,
`fixNFTokenNegOffer`, `fixPayChanCancelAfter`, `fixPriceOracleOrder`,
`fixTokenEscrowV1`, `fixXChainRewardRounding`.

## What a stalled amendment needs to activate

1. **17 of 25 trusted validators voting for it** (68.00% effective
   fraction), sustained — not just reached once.
2. **Hold that majority for 2 full weeks** from the first majority
   flag ledger. Any dip below 17 votes, even for one flag ledger,
   removes the majority entry and restarts the clock (scenario S-c:
   a 2-day dip delays activation by 9 days).
3. **No more than 8 vetoes / non-supporters.** 9 vetoes cap max
   support at 16 and block activation permanently while they hold
   (scenario S-e).
4. **Validators must keep validating.** A validator silent for 24 h
   flips to "no" (scenario S-f: a 1-day dip moves activation from
   day 14 to day 20).

## What would change the picture

- Enabling `PF_ValidatorVoteTracking` would make per-amendment vote
  telemetry available and turn U-01/U-02 from unmeasurable into
  measurable (R-02).
- Any operator override of `AMENDMENT_MAJORITY_TIME` from the 2-week
  default would change every activation timeline in this pack; the
  override is node-local config and is not observable (U-04).
- If the trusted set shrinks, the required votes fall in absolute
  terms but the effective fraction rises (e.g. 17/24 = 70.83% at
  trusted 24); the table in `data/lifecycle_model.json` covers
  trusted sets 1..25.

## Recommendations

1. Treat R-01 as the priority: publish vote counts or enable the
   vote-tracking amendment so stalled amendments become diagnosable.
2. Do not assume a disabled amendment is "rejected": without vote
   data, "disabled" carries no information about support.
3. Before proposing a new amendment, count vetoes: 9 committed
   non-supporters are enough to block it forever on the current
   25-validator set.
4. Keep the 2-week hold in mind when scheduling changes: the fastest
   possible activation from first majority is 14 days, and any
   majority loss restarts it.
