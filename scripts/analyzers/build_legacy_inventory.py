#!/usr/bin/env python3
"""Compatibility wrapper for the v1.2 AST-first Vue2 analyzer."""
from pathlib import Path
import argparse, shutil, subprocess

SKILL_ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    if shutil.which("node") is None:
        raise SystemExit("Node.js is required by the v1.2 AST analyzer")
    script = SKILL_ROOT / "engine/analyzers/vue2/analyze.mjs"
    print("INFO: using v1.2 AST-first adapter (legacy regex analyzers were removed)")
    return subprocess.call(["node", str(script), "--legacy", args.legacy, "--output", args.output])

if __name__ == "__main__":
    raise SystemExit(main())
