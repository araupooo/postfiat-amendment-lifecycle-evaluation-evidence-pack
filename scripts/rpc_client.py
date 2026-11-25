"""Shared JSON-RPC client for the public PFTL testnet node.

Standard library only. Used by the build-time fetch step
(feature_inventory.py --fetch-live); the reproduce path runs offline
against the vendored data/*.json files and never touches the network.
"""

import json
import urllib.request

RPC_URL = "https://rpc.testnet.postfiat.org"


def rpc(method, params=None, url=RPC_URL, timeout=30):
    """POST one JSON-RPC call and return the `result` object."""
    body = json.dumps({"method": method, "params": params or [{}]}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    if "error" in payload:
        raise RuntimeError("RPC error for %s: %s" % (method, payload["error"]))
    return payload["result"]


def get_feature_inventory(url=RPC_URL):
    return rpc("feature", [{}], url=url)


def get_server_info(url=RPC_URL):
    return rpc("server_info", [{}], url=url)


def get_ledger_header(ledger_index, url=RPC_URL):
    return rpc(
        "ledger",
        [{"ledger_index": ledger_index, "transactions": False, "expand": False}],
        url=url,
    )["ledger"]
