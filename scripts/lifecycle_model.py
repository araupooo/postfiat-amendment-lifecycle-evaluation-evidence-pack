"""M-03: amendment lifecycle model.

Re-derives, from the vendored data (features_current.json,
close_sample.json, governance_params.json):
  1. the required-vote table for trusted-set sizes 1..25 under both
     the operative post-fix rule (67/100, strictly greater) and the
     pre-fix counterfactual (204/256, greater-or-equal);
  2. activation timing: the 2-week majority hold converted to ledgers
     and flag-ledger intervals at the measured close cadence;
  3. day-tick stalled-amendment simulations (1 tick = 1 day; majority
     is recorded at flag ledgers in the real system, so day
     granularity is a stated model simplification);
  4. rollback / negative cases: lost-majority reset, veto blocking,
     24 h vote expiry, unsupported-activation hazard, the
     single-validator exception, and integer-truncation edges.

Every step prints a verbose line as it happens. Output is fully
deterministic (no clocks, no randomness). Writes
data/lifecycle_model.json. Exit code 0 only if all internal
consistency checks pass.
"""

import json
import os
import sys

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(PACK, "data")

MAJORITY_HOLD_S = 1209600  # 2 weeks, defaultAmendmentMajorityTime
FLAG_INTERVAL = 256


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def required_votes_postfix(trusted):
    """Operative rule: threshold = max(1, floor(t*67/100)); pass iff votes > threshold."""
    threshold = max(1, (trusted * 67) // 100)
    if trusted == 1:
        return threshold, threshold  # single-validator exception: >=
    return threshold, threshold + 1


def required_votes_prefix(trusted):
    """Pre-fix counterfactual: threshold = max(1, floor(t*204/256)); pass iff votes >= threshold."""
    threshold = max(1, (trusted * 204) // 256)
    return threshold, threshold


def simulate(name, support_by_day, required, horizon_days, log):
    """Day-tick simulation. support_by_day: day -> votes (missing days
    repeat the previous day's support). Returns the activation day or None."""
    log("M-03 sim %s: required votes=%d, horizon=%d days" % (name, required, horizon_days))
    majority_since = None
    support = None
    activated = None
    for day in range(horizon_days + 1):
        if day in support_by_day:
            support = support_by_day[day]
        has_majority = support is not None and support >= required
        if has_majority and majority_since is None:
            majority_since = day
            log("M-03 sim %s: day %d support=%d/%d MAJORITY RECORDED" % (name, day, support, 25))
        elif not has_majority and majority_since is not None:
            log(
                "M-03 sim %s: day %d support=%d/%d MAJORITY LOST (was since day %d, "
                "clock resets)" % (name, day, support, 25, majority_since)
            )
            majority_since = None
        elif has_majority:
            log(
                "M-03 sim %s: day %d support=%d/%d majority held %d/%d days"
                % (name, day, support, 25, day - majority_since, 14)
            )
        else:
            log("M-03 sim %s: day %d support=%d/%d no majority" % (name, day, support, 25))
        if majority_since is not None and day - majority_since >= 14:
            activated = day
            log("M-03 sim %s: day %d ACTIVATED (majority held 14 days)" % (name, day))
            break
    if activated is None:
        log("M-03 sim %s: no activation within %d days" % (name, horizon_days))
    return activated


def main():
    features = load("features_current.json")["features"]
    close = load("close_sample.json")
    params = load("governance_params.json")
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("M-03 step 1: loaded %d features, close cadence mean=%.4f s (n=%d diffs)"
        % (len(features), close["close_step_mean_s"], close["n_diffs"]))
    fix_on = next(
        (v for v in features.values() if v.get("name") == "fixAmendmentMajorityCalc"), {}
    ).get("enabled")
    log("M-03 step 2: fixAmendmentMajorityCalc enabled=%s -> operative rule is post-fix 67/100 strict >" % fix_on)
    if not fix_on:
        print("M-03 FAIL: expected fixAmendmentMajorityCalc enabled on testnet")
        return 1

    # --- 1. required-vote tables ---
    log("M-03 step 3: building required-vote tables for trusted-set sizes 1..25")
    table = []
    for t in range(1, 26):
        th_post, req_post = required_votes_postfix(t)
        th_pre, req_pre = required_votes_prefix(t)
        row = {
            "effective_required_fraction_postfix": req_post / t,
            "effective_required_fraction_prefix": req_pre / t,
            "required_votes_postfix": req_post,
            "required_votes_prefix": req_pre,
            "threshold_postfix": th_post,
            "threshold_prefix": th_pre,
            "trusted_validations": t,
        }
        table.append(row)
        log(
            "M-03 table trusted=%d post-fix threshold=%d required=%d (%.2f%%) "
            "pre-fix threshold=%d required=%d (%.2f%%)"
            % (t, th_post, req_post, 100.0 * req_post / t, th_pre, req_pre, 100.0 * req_pre / t)
        )
    live = table[24]  # trusted = 25
    log(
        "M-03 step 4: live trusted set 25 -> post-fix required=%d votes (%.0f%%), "
        "pre-fix counterfactual required=%d votes"
        % (live["required_votes_postfix"], 100.0 * live["effective_required_fraction_postfix"],
           live["required_votes_prefix"])
    )

    # --- 2. activation timing ---
    cadence = close["close_step_mean_s"]
    ledgers = MAJORITY_HOLD_S / cadence
    flags = ledgers / FLAG_INTERVAL
    log("M-03 step 5: majority hold %d s at cadence %.4f s = %.1f ledgers = %.1f flag intervals"
        % (MAJORITY_HOLD_S, cadence, ledgers, flags))
    cadence_24h = 3.0243
    ledgers_24h = MAJORITY_HOLD_S / cadence_24h
    log("M-03 step 6: same hold at 24 h mean cadence %.4f s = %.1f ledgers = %.1f flag intervals "
        "(Task 11 window 2026-11-24 -> 25, 28,800 ledgers)"
        % (cadence_24h, ledgers_24h, ledgers_24h / FLAG_INTERVAL))
    timing = {
        "cadence_s": cadence,
        "cadence_sample": "11 headers, n=10 diffs, measured 2026-11-25 19:18 UTC",
        "flag_intervals_at_measured_cadence": flags,
        "flag_intervals_at_24h_cadence": ledgers_24h / FLAG_INTERVAL,
        "ledgers_at_24h_cadence": ledgers_24h,
        "ledgers_at_measured_cadence": ledgers,
        "majority_hold_seconds": MAJORITY_HOLD_S,
    }

    # --- 3. stalled-amendment simulations (trusted = 25, required = 17) ---
    req = live["required_votes_postfix"]
    log("M-03 step 7: day-tick simulations, trusted=25, required=%d votes" % req)
    scenarios = {}
    scenarios["S-a steady majority"] = simulate(
        "S-a steady majority", {0: 17}, req, 28, log
    )
    scenarios["S-b one vote short"] = simulate(
        "S-b one vote short", {0: 16}, req, 28, log
    )
    scenarios["S-c majority lost and regained"] = simulate(
        "S-c majority lost and regained", {0: 17, 7: 15, 9: 17}, req, 35, log
    )
    scenarios["S-d eight vetoes"] = simulate(
        "S-d eight vetoes (max support 17)", {0: 17}, req, 28, log
    )
    scenarios["S-e nine vetoes"] = simulate(
        "S-e nine vetoes (max support 16)", {0: 16}, req, 28, log
    )
    scenarios["S-f 24h expiry dip"] = simulate(
        "S-f 24h expiry dip", {0: 17, 5: 16, 6: 17}, req, 35, log
    )
    scenarios["S-g pre-fix rule at 17 votes"] = simulate(
        "S-g pre-fix rule at 17 votes",
        {0: 17},
        live["required_votes_prefix"],
        28,
        log,
    )
    log("M-03 step 8: scenario activations: %s"
        % {k: (("day %d" % v) if v is not None else "never") for k, v in scenarios.items()})

    # --- 4. rollback / negative cases ---
    log("M-03 step 9: rollback/negative cases")
    veto_block = 25 - req + 1  # vetoes needed so max support < required
    log("M-03 case veto-block: %d vetoes cap max support at %d < required %d -> never activates"
        % (veto_block, 25 - veto_block, req))
    log("M-03 case lost-majority-reset: S-c shows the 14-day clock restarts from the "
        "re-gained majority day, not the first majority day")
    log("M-03 case vote-expiry: a validator silent 24h flips to 'no' (TrustedVotes "
        "expiresAfter 24h); S-f shows a 1-day dip on day 5 discards 5 days of "
        "accumulated hold, moving activation from day 14 to day 20")
    log("M-03 case unsupported-activation: an unsupported amendment that reaches "
        "majority has firstUnsupportedExpected = majority time + 2 weeks; if it then "
        "activates, servers without code support are blocked (setAmendmentBlocked)")
    log("M-03 case single-validator: trusted=1 -> required=%d (exception: >= not >)"
        % required_votes_postfix(1)[1])
    log("M-03 case truncation: post-fix threshold uses integer division "
        "floor(t*67/100); effective required fraction at t=25 is %.0f%%, at t=24 is %.2f%%, "
        "at t=2 is %.0f%%" % (100.0 * 17 / 25, 100.0 * 17 / 24, 100.0 * 2 / 2))
    log("M-03 case one-way: once enabled an amendment can never be disabled, only "
        "superseded by a subsequent amendment")
    negative = {
        "one_way_enabled": True,
        "single_validator_required_votes": required_votes_postfix(1)[1],
        "unsupported_activation_blocks_server": True,
        "veto_block_count_at_trusted_25": veto_block,
    }

    model = {
        "activation_timing": timing,
        "live_trusted_set": 25,
        "negative_cases": negative,
        "operative_rule": "post-fix 67/100, strictly greater (fixAmendmentMajorityCalc enabled)",
        "required_votes_table": table,
        "scenarios": {
            k: (("activated_day_%d" % v) if v is not None else "never_activates")
            for k, v in scenarios.items()
        },
        "scenario_activation_days": {k: v for k, v in scenarios.items()},
    }
    with open(os.path.join(DATA, "lifecycle_model.json"), "w") as f:
        json.dump(model, f, indent=2, sort_keys=True)
        f.write("\n")
    log("M-03 step 10: wrote data/lifecycle_model.json")
    checks_ok = (
        live["required_votes_postfix"] == 17
        and live["required_votes_prefix"] == 19
        and scenarios["S-a steady majority"] == 14
        and scenarios["S-b one vote short"] is None
        and scenarios["S-c majority lost and regained"] == 23
        and scenarios["S-e nine vetoes"] is None
        and scenarios["S-g pre-fix rule at 17 votes"] is None
    )
    log("M-03 %s" % ("PASS" if checks_ok else "FAIL"))
    return 0 if checks_ok else 1


if __name__ == "__main__":
    sys.exit(main())
