#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = parts[1]
    data = {}
    for key in ("id", "type", "status", "schema_version", "last_verified_commit"):
        m = re.search(rf"^{re.escape(key)}:\s*[\"']?([^\"'\n]+)[\"']?\s*$", fm, re.M)
        if m:
            data[key] = m.group(1).strip()
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs_root")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    root = Path(args.docs_root).resolve()
    out = Path(args.output).resolve()
    docs = []

    for p in sorted(root.rglob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        title = ""
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        docs.append({
            "path": str(p.relative_to(root)),
            "title": title,
            **meta,
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "schema_version": "1",
        "root": str(root),
        "documents": docs
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(docs)} documents -> {out}")

if __name__ == "__main__":
    main()
