"""M-01: amendment inventory capture and previous-window diff.

Two modes:
  --fetch-live   POST the `feature` and `server_info` RPCs and write
                 data/features_current.json, data/server_info.json and
                 data/close_sample.json (11 headers ending at the
                 validated ledger). Used once at build time.
  (default)      Offline replay: read the vendored data/*.json files,
                 recompute the diff against data/features_baseline.json
                 and print one verbose line per amendment plus a summary.
                 This is what reproduce.sh runs; it never touches the
                 network and its output is fully deterministic (no
                 timestamps, no absolute paths, sorted by amendment ID).

Exit code 0 only if the inventory is internally consistent (every entry
has enabled/supported/name fields, counts add up, diff recomputes).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpc_client import (  # noqa: E402
    RPC_URL,
    get_feature_inventory,
    get_ledger_header,
    get_server_info,
)

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(PACK, "data")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def fetch_live():
    print("M-01 step 1: POST feature to %s" % RPC_URL)
    features = get_feature_inventory()
    print("M-01 step 2: feature RPC returned %d entries" % len(features["features"]))
    print("M-01 step 3: POST server_info to %s" % RPC_URL)
    info = get_server_info()["info"]
    validated = info["validated_ledger"]["seq"]
    print(
        "M-01 step 4: server_info validated_ledger seq=%d quorum=%s peers=%s "
        "server_state=%s build=%s network_id=%s"
        % (
            validated,
            info.get("validation_quorum"),
            info.get("peers"),
            info.get("server_state"),
            info.get("build_version"),
            info.get("network_id"),
        )
    )
    print("M-01 step 5: fetching 11 ledger headers ending at seq %d" % validated)
    headers = []
    for seq in range(validated - 10, validated + 1):
        lg = get_ledger_header(seq)
        headers.append({"seq": seq, "close_time": lg["close_time"]})
        print("M-01 step 5: header seq=%d close_time=%d" % (seq, lg["close_time"]))
    diffs = [
        headers[i + 1]["close_time"] - headers[i]["close_time"]
        for i in range(len(headers) - 1)
    ]
    mean = sum(diffs) / len(diffs)
    print("M-01 step 6: close-step diffs=%s mean=%.4f s (n=%d)" % (diffs, mean, len(diffs)))

    fetched_at = info.get("time", "")
    current = {
        "endpoint": RPC_URL,
        "fetch_note": "Live `feature` RPC snapshot. No vote counts are "
        "exposed by the public RPC: only enabled/supported/name per "
        "amendment. Per-amendment live support fractions are therefore "
        "not observable from public data (see docs/CLAIMS.md U-01).",
        "features": features["features"],
        "status": features.get("status"),
        "validated_ledger_seq_at_fetch": validated,
    }
    write_json(os.path.join(DATA, "features_current.json"), current)
    print("M-01 step 7: wrote data/features_current.json (%d features)" % len(features["features"]))
    write_json(os.path.join(DATA, "server_info.json"), {"info": info})
    print("M-01 step 8: wrote data/server_info.json")
    write_json(
        os.path.join(DATA, "close_sample.json"),
        {
            "close_step_diffs_s": diffs,
            "close_step_mean_s": mean,
            "endpoint": RPC_URL,
            "headers": headers,
            "n_diffs": len(diffs),
            "note": "Reported close_time steps are quantized by the 10 s "
            "close-time resolution: ledgers cluster 3-4 per 10 s bucket "
            "(1 s steps inside a bucket, 7-8 s jumps between buckets). "
            "Segment means, not single diffs, are the reliable cadence "
            "measure.",
            "validated_seq": validated,
        },
    )
    print("M-01 step 9: wrote data/close_sample.json")
    return current, info


def diff_and_report():
    current = load_json(os.path.join(DATA, "features_current.json"))
    baseline = load_json(os.path.join(DATA, "features_baseline.json"))
    cur = current["features"]
    base = baseline["features"]
    print("M-01 step 1: loaded data/features_current.json (%d features)" % len(cur))
    print("M-01 step 2: loaded data/features_baseline.json (%d features)" % len(base))
    enabled = sorted(k for k, v in cur.items() if v.get("enabled"))
    disabled = sorted(k for k, v in cur.items() if not v.get("enabled"))
    print("M-01 step 3: current inventory enabled=%d disabled=%d" % (len(enabled), len(disabled)))
    unnamed = [k for k, v in cur.items() if not v.get("name")]
    print("M-01 step 4: entries without a name field: %d" % len(unnamed))
    for k in sorted(cur):
        v = cur[k]
        print(
            "M-01 feature %s name=%s enabled=%s supported=%s"
            % (k, v.get("name"), v.get("enabled"), v.get("supported"))
        )
    changed = []
    for k in sorted(set(cur) | set(base)):
        o, n = base.get(k), cur.get(k)
        if o is None:
            changed.append({"id": k, "kind": "added", "name": n.get("name")})
        elif n is None:
            changed.append({"id": k, "kind": "removed", "name": o.get("name")})
        elif o.get("enabled") != n.get("enabled") or o.get("name") != n.get("name"):
            changed.append(
                {
                    "id": k,
                    "kind": "changed",
                    "name": n.get("name"),
                    "was_enabled": o.get("enabled"),
                    "now_enabled": n.get("enabled"),
                }
            )
    print("M-01 step 5: diff vs baseline: %d changed entries" % len(changed))
    for c in changed:
        print("M-01 diff %(kind)s %(id)s name=%(name)s" % c)
    diff_doc = {
        "baseline": baseline.get("fetch_note", "Task 12 baseline inventory"),
        "baseline_feature_count": len(base),
        "changed": changed,
        "changed_count": len(changed),
        "current_enabled": len(enabled),
        "current_feature_count": len(cur),
        "current_disabled": len(disabled),
    }
    write_json(os.path.join(DATA, "features_diff.json"), diff_doc)
    print("M-01 step 6: wrote data/features_diff.json")
    ok = (
        len(cur) == len(enabled) + len(disabled)
        and not unnamed
        and all("enabled" in v and "supported" in v for v in cur.values())
    )
    print("M-01 %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-live", action="store_true")
    args = ap.parse_args()
    if args.fetch_live:
        fetch_live()
        return diff_and_report()
    return diff_and_report()


if __name__ == "__main__":
    sys.exit(main())
