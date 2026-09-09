#!/usr/bin/env python3
from pathlib import Path
import argparse, re

NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_dir", nargs="?", default=".")
    args = ap.parse_args()
    root = Path(args.skill_dir).resolve()
    skill = root / "SKILL.md"
    errors = []
    if not skill.exists():
        errors.append("SKILL.md is missing")
    else:
        text = skill.read_text(encoding="utf-8")
        if not text.startswith("---\n"): errors.append("SKILL.md must start with YAML frontmatter")
        parts = text.split("---", 2)
        if len(parts) < 3: errors.append("SKILL.md frontmatter is not closed")
        else:
            fm = parts[1]
            m = re.search(r"^name:\s*([^\n]+?)\s*$", fm, re.M)
            if not m: errors.append("frontmatter.name missing")
            else:
                name = m.group(1).strip().strip('"\'')
                if len(name) > 64: errors.append("frontmatter.name exceeds 64 characters")
                if not NAME_RE.fullmatch(name): errors.append("frontmatter.name must use lowercase letters/numbers and single hyphens")
                if name != root.name: errors.append(f"name '{name}' must match folder '{root.name}'")
            if not re.search(r"^description:\s*(?:[>|]-?\s*$|\S+)", fm, re.M): errors.append("frontmatter.description missing")
        line_count = len(text.splitlines())
        if line_count >= 500: errors.append(f"SKILL.md has {line_count} lines; keep main skill under 500 lines")
    required_files = [
        "README.md", "README.zh-CN.md", "scripts/modernize.py", "scripts/bootstrap.py",
        "scripts/validate_governance.py", "scripts/visual/visual_harness.mjs",
        "engine/analyzers/protocol.md", "engine/analyzers/vue2/analyze.mjs", "engine/state/machine.py",
    ]
    for f in required_files:
        if not (root / f).exists(): errors.append(f"missing v1.2 asset: {f}")
    for d in ("references", "assets", "scripts", "schemas", "engine"):
        if not (root / d).exists(): errors.append(f"required v1.2 directory missing: {d}/")
    if errors:
        for e in errors: print("ERROR:", e)
        return 1
    print(f"PASS: {root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
