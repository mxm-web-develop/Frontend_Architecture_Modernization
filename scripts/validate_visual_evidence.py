#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
from engine.evidence.verification import validate_visual_result

VALID_POLICIES = {
    "STRICT_PRESERVE",
    "STRUCTURE_PRESERVE",
    "APPROVED_REDESIGN",
    "NOT_VISUAL",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--result", required=True, help="visual harness result.json")
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    manifest = Path(args.manifest).resolve()
    repo = Path(args.repo).resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    errors = []

    if not data.get("domain"):
        errors.append("manifest.domain missing")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        errors.append("manifest.scenarios must be a list")
        scenarios = []
    for i, s in enumerate(scenarios):
        label = s.get("id") or f"scenario[{i}]"
        if s.get("policy") not in VALID_POLICIES:
            errors.append(f"{label}: invalid/missing policy")
        # === v1.6 P6：baseline_source 必填，且 STRICT_PRESERVE 必须为 live_runtime ===
        bs = s.get("baseline_source")
        if not bs:
            errors.append(f"{label}: baseline_source required (live_runtime | legacy_build)")
        elif bs not in {"live_runtime", "legacy_build"}:
            errors.append(f"{label}: baseline_source must be live_runtime or legacy_build (got {bs!r})")
        if s.get("policy") == "STRICT_PRESERVE":
            if not s.get("legacy_commit"):
                errors.append(f"{label}: legacy_commit required")
            if not s.get("fixture"):
                errors.append(f"{label}: deterministic fixture required")
            if bs != "live_runtime":
                errors.append(
                    f"{label}: STRICT_PRESERVE requires baseline_source=live_runtime "
                    "(legacy build alone is not authoritative; v1.6 P6)"
                )
            lr = s.get("live_runtime") or {}
            for k in ("url", "captured_at", "commit", "screenshot_sha256"):
                if not lr.get(k):
                    errors.append(f"{label}: STRICT_PRESERVE requires live_runtime.{k}")

    if not errors:
        errors.extend(validate_visual_result(repo, args.result, manifest.parent))

    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    print(f"PASS: {len(scenarios)} visual scenarios + result.json + PNG evidence")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
