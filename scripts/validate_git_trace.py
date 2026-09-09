#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, re

TRAILERS = [
    "Migration-Domain",
    "Capability",
    "Legacy-Base",
]

def run(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("commit", nargs="?", default="HEAD")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    message = run(repo, "show", "-s", "--format=%B", args.commit)
    subject = message.splitlines()[0] if message else ""

    migration_like = re.match(r"^(migrate|verify|sync)\b", subject) is not None
    if not migration_like:
        print("SKIP: commit is not migrate/verify/sync:", subject)
        return 0

    missing = []
    for key in TRAILERS:
        if not re.search(rf"(?mi)^{re.escape(key)}:\s*\S+", message):
            missing.append(key)

    if missing:
        print("FAIL: missing migration trailers:", ", ".join(missing))
        return 1

    print("PASS: required migration trailers present")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
