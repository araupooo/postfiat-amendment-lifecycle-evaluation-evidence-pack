"""M-02: governance-parameter audit against the pinned postfiatd source.

Verifies every governance parameter against the vendored source
excerpts in data/source_excerpts.json (exact lines captured from the
pinned postfiatd checkout, commit
0085a1ff885d6a446369cf73a4430f75af22be55, at build time), printing one
verbose line per check with the exact file:line and the matched text.
Writes data/governance_params.json.

The check reads NO live checkout: the first version of this script
grepped a local checkout path, which does not exist on a CI runner
(or any other machine), so CI failed with FileNotFoundError. The
excerpts are the evidence now; the optional --pin argument, when it
points at a real checkout, additionally cross-checks every excerpt
against that checkout and fails on any mismatch, without changing
the printed output.

Log lines use checkout-relative paths only, so reproduce output is
deterministic. Exit code 0 only if every check passes.
"""

import argparse
import json
import os
import re
import sys

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(PACK, "data")

# (check id, relative path, regex, description)
CHECKS = [
    (
        "G-01",
        "include/xrpl/protocol/SystemParameters.h",
        r"preFixAmendmentMajorityCalcThreshold;\s*$",
        "pre-fix threshold constant declared",
    ),
    (
        "G-02",
        "include/xrpl/protocol/SystemParameters.h",
        r"std::ratio<204, 256> preFixAmendmentMajorityCalcThreshold",
        "pre-fix threshold is 204/256",
    ),
    (
        "G-03",
        "include/xrpl/protocol/SystemParameters.h",
        r"std::ratio<67, 100> postFixAmendmentMajorityCalcThreshold",
        "post-fix threshold is 67/100",
    ),
    (
        "G-04",
        "include/xrpl/protocol/SystemParameters.h",
        r"defaultAmendmentMajorityTime = std::chrono::weeks\{2\}",
        "majority hold time is 2 weeks",
    ),
    (
        "G-05",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"threshold_ = !rules_\.enabled\(fixAmendmentMajorityCalc\)",
        "threshold rule selects on fixAmendmentMajorityCalc",
    ),
    (
        "G-06",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"return it->second > threshold_;",
        "passes() uses STRICTLY greater than when fix is enabled",
    ),
    (
        "G-07",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"trustedValidations_ == 1\)",
        "single-validator exception in passes()",
    ),
    (
        "G-08",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"static constexpr NetClock::duration expiresAfter = 24h;",
        "validator vote records expire after 24h",
    ),
    (
        "G-09",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"\(\(\*majorityTime \+ majorityTime_\) <= closeTime\)",
        "activation requires majority held for majorityTime_",
    ),
    (
        "G-10",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"actions\[entry\.first\] = tfGotMajority;",
        "got-majority action recorded",
    ),
    (
        "G-11",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"actions\[entry\.first\] = tfLostMajority;",
        "lost-majority action recorded",
    ),
    (
        "G-12",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"return \(\(ledgerSeq - 1\) / 256\) != \(\(lastUpdateSeq_ - 1\) / 256\);",
        "voting evaluated at 256-ledger flag boundaries",
    ),
    (
        "G-13",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"firstUnsupportedExpected_ = \*firstUnsupportedExpected_ \+ majorityTime_;",
        "unsupported-majority expected time adds majorityTime_",
    ),
    (
        "G-14",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"if \(!fs\.enabled && lastVote_ && isAdmin\)",
        "per-amendment vote counts are admin-only in getJson",
    ),
    (
        "G-15",
        "src/xrpld/app/misc/detail/AmendmentTable.cpp",
        r"Unknown amendments are effectively vetoed already",
        "unknown amendments are effectively vetoed",
    ),
    (
        "G-16",
        "include/xrpl/protocol/TxFlags.h",
        r"tfGotMajority\s+= 0x00010000;",
        "tfGotMajority flag value 0x00010000",
    ),
    (
        "G-17",
        "include/xrpl/protocol/TxFlags.h",
        r"tfLostMajority\s+= 0x00020000;",
        "tfLostMajority flag value 0x00020000",
    ),
    (
        "G-18",
        "src/xrpld/app/tx/detail/Change.cpp",
        r"entry\[sfCloseTime\] =",
        "got-majority records sfCloseTime in the ledger",
    ),
    (
        "G-19",
        "src/xrpld/app/tx/detail/Change.cpp",
        r"ctx_\.app\.getOPs\(\)\.setAmendmentBlocked\(\);",
        "unsupported activation blocks the server",
    ),
    (
        "G-20",
        "src/xrpld/core/Config.h",
        r"AMENDMENT_MAJORITY_TIME = defaultAmendmentMajorityTime;",
        "config default majority time is the 2-week constant",
    ),
    (
        "G-21",
        "src/xrpld/app/main/Application.cpp",
        r"config\(\)\.AMENDMENT_MAJORITY_TIME,",
        "majority time wired from config into the amendment table",
    ),
    (
        "G-22",
        "src/xrpld/app/misc/ValidatorVoteTracker.cpp",
        r"return rules\.enabled\(featurePF_ValidatorVoteTracking\);",
        "vote tracker gated on PF_ValidatorVoteTracking",
    ),
    (
        "G-23",
        "src/xrpld/app/misc/ExclusionManager.cpp",
        r"if \(!view\.rules\(\)\.enabled\(featurePF_AccountExclusion\)\)",
        "exclusion manager gated on PF_AccountExclusion",
    ),
]


def find_in_excerpts(excerpts, relpath, pattern):
    """First excerpt line for relpath whose text matches pattern."""
    lines = excerpts["files"].get(relpath, {})
    hits = []
    for lineno_s in sorted(lines, key=lambda s: int(s)):
        text = lines[lineno_s]
        if re.search(pattern, text):
            hits.append((int(lineno_s), text))
    return hits


def grep_lines(pin, relpath, pattern):
    path = os.path.join(pin, relpath)
    hits = []
    with open(path, errors="replace") as f:
        for i, line in enumerate(f, start=1):
            if re.search(pattern, line):
                hits.append((i, line.rstrip("\n")))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pin",
        default=os.path.expanduser("~/workspace/postfiatd-pin-0085a1f"),
        help="optional pinned postfiatd checkout; when present, every "
        "excerpt is cross-checked against it (no output change)",
    )
    args = ap.parse_args()
    pin = args.pin
    with open(os.path.join(DATA, "source_excerpts.json")) as f:
        excerpts = json.load(f)
    print(
        "M-02 step 1: auditing vendored source excerpts (pinned commit %s)"
        % excerpts["pinned_commit"]
    )
    pin_present = os.path.isdir(pin)
    params = {
        "amendment_majority_time_seconds": 1209600,
        "amendment_majority_time_weeks": 2,
        "checks": {},
        "flag_ledger_interval": 256,
        "post_fix_threshold_num": 67,
        "post_fix_threshold_den": 100,
        "pre_fix_threshold_den": 256,
        "pre_fix_threshold_num": 204,
        "source": "postfiatd 0085a1ff885d6a446369cf73a4430f75af22be55",
        "tf_got_majority": "0x00010000",
        "tf_lost_majority": "0x00020000",
        "vote_record_expiry_hours": 24,
    }
    failures = 0
    for check_id, relpath, pattern, desc in CHECKS:
        hits = find_in_excerpts(excerpts, relpath, pattern)
        if not hits:
            print("M-02 %s FAIL %s: no match for /%s/ -- %s" % (check_id, relpath, pattern, desc))
            failures += 1
            params["checks"][check_id] = {"pass": False, "path": relpath}
            continue
        lineno, text = hits[0]
        if pin_present:
            live = grep_lines(pin, relpath, pattern)
            if not live or live[0][0] != lineno or live[0][1] != text:
                print(
                    "M-02 %s FAIL %s: excerpt %s:%d does not match the pinned checkout -- %s"
                    % (check_id, relpath, relpath, lineno, desc)
                )
                failures += 1
                params["checks"][check_id] = {"pass": False, "path": relpath}
                continue
        lineno, text = hits[0]
        print("M-02 %s PASS %s:%d: %s -- %s" % (check_id, relpath, lineno, text.strip(), desc))
        params["checks"][check_id] = {
            "line": lineno,
            "pass": True,
            "path": relpath,
            "text": text.strip(),
        }
    with open(os.path.join(DATA, "governance_params.json"), "w") as f:
        json.dump(params, f, indent=2, sort_keys=True)
        f.write("\n")
    print("M-02 step 2: wrote data/governance_params.json (%d checks)" % len(CHECKS))
    print("M-02 %s" % ("PASS" if failures == 0 else "FAIL"))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
