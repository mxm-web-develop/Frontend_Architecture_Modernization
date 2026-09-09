#!/usr/bin/env python3
"""live runtime capture 入口脚本 (v1.6.1)。

按 governance/project.yaml 的 live_runtime 配置，访问线上 URL 落 snapshot。

可选参数：
  --url <url>          覆盖 profile.url（调试 / 临时跑特定 URL）
  --driver <driver>    覆盖 profile.driver (playwright | puppeteer | cursor-browser | manual)
  --capability <id>    落 manifest 时给 manifest 的 capability_id 字段
  --scenario <id>      落 manifest 时给 scenario_id 字段
  --repo <path>        目标 repo 路径，默认 .

用法：

  python scripts/runtime_capture.py --capability CAP-DATA-001 --scenario home-default
  python scripts/runtime_capture.py --url https://staging.example.com --capability CAP-X

注意：playwright 是可选依赖；没安装会清晰报错。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

import yaml  # noqa: E402

from engine.runtime_capture import (  # noqa: E402
    LiveRuntimeSpec,
    SnapshotRecord,
    capture_snapshot_playwright,
    load_live_runtime,
    write_snapshot,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--url", default="")
    ap.add_argument("--driver", default="")
    ap.add_argument("--capability", default="")
    ap.add_argument("--scenario", default="")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    project_yaml = repo / "governance" / "project.yaml"
    if not project_yaml.exists():
        print(f"ERROR: governance/project.yaml not found: {project_yaml}", file=sys.stderr)
        return 2
    profile = yaml.safe_load(project_yaml.read_text(encoding="utf-8")) or {}
    spec = load_live_runtime(profile)
    if args.url:
        spec.url = args.url
    if args.driver:
        spec.driver = args.driver
    if not spec.enabled:
        print(
            "ERROR: live_runtime not enabled; set live_runtime.url and "
            "live_runtime.capture.driver in governance/project.yaml",
            file=sys.stderr,
        )
        return 2

    if spec.driver != "playwright":
        print(
            f"ERROR: this entrypoint supports only playwright driver; got {spec.driver!r}. "
            "Use engine.runtime_capture contracts directly for other drivers, "
            "or set live_runtime.capture.driver=playwright.",
            file=sys.stderr,
        )
        return 2

    rec: SnapshotRecord = capture_snapshot_playwright(
        repo,
        spec,
        scenario_id=args.scenario or "default",
        capability_id=args.capability or "",
    )
    manifest = write_snapshot(repo, spec, rec)
    print(f"OK wrote snapshot manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())