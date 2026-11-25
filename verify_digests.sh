#!/usr/bin/env bash
# Verify every file listed in SHA256SUMS. The manifest covers all pack
# files except itself and outputs/reproduce_selfcheck.log: the manifest
# cannot verify itself, and the self-check log embeds the digest
# verification output, so it cannot be part of its own digest set.
# The self-check log is instead verified by re-running reproduce.sh:
# a fresh run must regenerate it byte-identically (same SHA-256).
# Run from the pack root.
set -e
cd "$(dirname "$0")"
sha256sum -c SHA256SUMS
