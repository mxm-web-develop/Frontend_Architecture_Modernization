#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, datetime, json, os, re, shutil, subprocess

try:
    import yaml
except Exception as exc:
    raise SystemExit("Missing PyYAML. Run: python -m pip install -r scripts/requirements.txt") from exc

SKILL_ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args, check=True):
    p = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def git_sha(repo: Path):
    try:
        return git(repo, "rev-parse", "HEAD")
    except Exception:
        return "UNKNOWN"


def copy_template(src: Path, dst: Path, replacements=None, force=False):
    if dst.exists() and not force:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        data = data.replace(key, value)
    dst.write_text(data, encoding="utf-8")
    return True


def human_template_replacements(language: str):
    if str(language).lower().startswith("zh"):
        return {
            "Migration Master Report": "现代化总报告",
            "Migration Plan": "现代化实施计划",
            "Migration Decisions": "现代化决策",
            "## Scope": "## 范围",
            "## Capability set": "## Capability 集合",
            "## Target design": "## 目标实现设计",
            "## Functional parity": "## 功能一致性",
            "## Visual parity": "## 视觉一致性",
            "## Architecture gates": "## 架构门禁",
            "## Unknowns": "## 未知项",
            "## Rollback / Cutover": "## 回滚 / 切流",
            "GENERATED / MILESTONE REPORT. Source of truth is `governance/` + `migration/`.": "生成的里程碑报告。机器事实来源为 `governance/` + `migration/`。",
            "Record explicit product/architecture/design decisions. Do not use this file to hide unknowns.": "记录明确的产品、架构与设计决策。不要用本文件隐藏未知项。",
        }
    return {}


def main():
    ap = argparse.ArgumentParser(description="Initialize discovery-first frontend modernization control plane.")
    ap.add_argument("--target", required=True, help="new target repository")
    ap.add_argument("--legacy", required=True, help="existing legacy repository; read-only")
    ap.add_argument("--profile", default=str(SKILL_ROOT / "assets/profiles/brownfield-modernization.yaml"))
    ap.add_argument("--baseline")
    ap.add_argument("--human-language")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--mode", choices=["cross-repository", "in-place"], default="cross-repository")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    legacy = Path(args.legacy).resolve()
    if not target.exists():
        raise SystemExit(f"ERROR MOD-BOOT-001: target repository not found: {target}")
    if not legacy.exists():
        raise SystemExit(f"ERROR MOD-BOOT-002: legacy repository not found: {legacy}")
    if target == legacy or args.mode != "cross-repository":
        raise SystemExit("ERROR MOD-BOOT-003: v1.3 scope is brownfield reconstruction into a NEW repository; in-place modernization is out of scope")

    profile_src = Path(args.profile).resolve()
    if not profile_src.exists():
        raise SystemExit(f"ERROR MOD-BOOT-004: profile not found: {profile_src}")
    profile = yaml.safe_load(profile_src.read_text(encoding="utf-8")) or {}
    language = profile.get("language") or {}
    human_lang = args.human_language or language.get("human_documentation") or "en"
    baseline = args.baseline or git_sha(legacy)
    legacy_ref = os.path.relpath(legacy, target).replace("\\", "/")
    replacements = {"__LEGACY_BASE__": baseline, "__HUMAN_LANG__": human_lang, **human_template_replacements(human_lang)}
    created = []

    # Framework-independent governance. No target framework is selected here.
    for src in sorted((SKILL_ROOT / "assets/templates/governance").iterdir()):
        if src.is_file() and src.name != "project.yaml":
            dst = target / "governance" / src.name
            if copy_template(src, dst, replacements, args.force):
                created.append(dst)

    project_data = {
        "schema_version": "1",
        "project_id": target.name,
        "profile": profile_src.stem,
        "migration_mode": "cross-repository",
        "modernization": {
            "scope_mode": "brownfield-new-repository",
            "new_requirements": "defer",
            "framework_strategy": "undecided-until-confirmed",
        },
        "language": {
            "interaction": language.get("interaction") or human_lang,
            "human_documentation": human_lang,
            "enforce_human_documentation": bool(language.get("enforce_human_documentation", True)),
            "machine_protocol": language.get("machine_protocol") or "en",
            "code_identifiers": language.get("code_identifiers") or "en",
            "code_comments": language.get("code_comments") or human_lang,
            "governed_markdown": language.get("governed_markdown") or ["docs", "migration", "handoff"],
        },
        "repositories": {
            "sources": [{
                "id": "legacy-frontend", "type": "frontend", "path": legacy_ref,
                "mode": "read-only", "baseline_commit": baseline,
            }],
            "target": {"id": target.name, "type": "frontend", "path": ".", "mode": "read-write"},
        },
    }
    project = target / "governance/project.yaml"
    if not project.exists() or args.force:
        project.parent.mkdir(parents=True, exist_ok=True)
        project.write_text(yaml.safe_dump(project_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        created.append(project)

    profile_dst = target / "governance/profile.yaml"
    if not profile_dst.exists() or args.force:
        shutil.copy2(profile_src, profile_dst)
        created.append(profile_dst)

    agents = target / "AGENTS.md"
    if not agents.exists() or args.force:
        if str(human_lang).lower().startswith("zh"):
            agents_body = f"""# Agent 项目入口

这是一个 brownfield 前端架构现代化项目。

## 必须先读
1. `governance/project.yaml`
2. `governance/project-status.yaml`
3. `governance/modernization-constitution.yaml`
4. `governance/current-system.yaml`
5. `governance/framework-strategy.yaml`
6. 与当前任务相关的 Domain / Module Manifest

## 核心边界
- Legacy 仓库只读，是产品行为事实来源。
- Target 新仓用于架构现代化重构和完整功能复现。
- `NEW_REQUIREMENT` 不在本 Skill 中实现，必须延期到 Handoff 后的正常开发流程。
- 不允许按 Legacy 文件夹或一级路由直接认定 Target Domain。
- 不允许手工伪造 Gate PASS；必须绑定真实 Evidence。

## 常用命令
优先使用 `modernize <command>` 这一逻辑命令。Skill Runtime 负责解析实际安装路径。
运行 `modernize status --repo .` 查看项目和 Domain 状态。
"""
        else:
            agents_body = """# Agent Project Entry

This is a brownfield frontend architecture modernization project.

## Read first
1. `governance/project.yaml`
2. `governance/project-status.yaml`
3. `governance/modernization-constitution.yaml`
4. `governance/current-system.yaml`
5. `governance/framework-strategy.yaml`
6. The relevant Domain / Module manifest

## Scope boundary
- Legacy is read-only and is the product-behavior truth source.
- Target is a new repository for architectural reconstruction and functional reproduction.
- `NEW_REQUIREMENT` is deferred to post-handoff product development.
- Do not treat a legacy folder or top-level route as a confirmed target domain.
- Do not fabricate gate PASS; real evidence is mandatory.

Use the logical `modernize <command>` interface. Run `modernize status --repo .`.
"""
        agents.write_text(agents_body, encoding="utf-8")
        created.append(agents)

    # Framework strategy must remain undecided after bootstrap.
    fw = target / "governance/framework-strategy.yaml"
    if fw.exists():
        data = yaml.safe_load(fw.read_text(encoding="utf-8")) or {}
        data["status"] = "UNDECIDED"; data["selected"] = None; data["confirmation"] = None
        fw.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    reg_src = SKILL_ROOT / "assets/templates/migration/registry.yaml"
    reg_dst = target / "migration/registry.yaml"
    if copy_template(reg_src, reg_dst, replacements, False): created.append(reg_dst)

    for src in sorted((SKILL_ROOT / "assets/templates/migration/system").iterdir()):
        if src.is_file():
            dst = target / "migration/system" / src.name
            if copy_template(src, dst, replacements, False): created.append(dst)


    project_status = target / "governance/project-status.yaml"
    if not project_status.exists() or args.force:
        project_status.write_text(yaml.safe_dump({
            "schema_version":"1",
            "state":"DISCOVERED",
            "state_commit":git_sha(target),
            "history":[],
        }, sort_keys=False, allow_unicode=True), encoding="utf-8")
        created.append(project_status)

    schema_dst = target / "governance/schemas"; schema_dst.mkdir(parents=True, exist_ok=True)
    for src in (SKILL_ROOT / "schemas").glob("*.json"):
        dst = schema_dst / src.name
        if not dst.exists() or args.force:
            shutil.copy2(src, dst); created.append(dst)

    marker = target / ".modernization.json"
    marker.write_text(json.dumps({
        "schema_version":"1",
        "skill":"frontend-architecture-modernization",
        "skill_version":"1.5.1",
        "scope":"brownfield-new-repository",
        "legacy_repository":str(legacy),
        "legacy_baseline":baseline,
        "framework_strategy":"UNDECIDED",
        "initialized_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }, indent=2)+"\n", encoding="utf-8")
    created.append(marker)

    print(f"PASS: discovery-first modernization initialized target={target}")
    print(f"Legacy baseline: {baseline}")
    print("Framework strategy: UNDECIDED")
    for item in created:
        try: shown=item.relative_to(target)
        except ValueError: shown=item
        print("+", shown)

if __name__ == "__main__":
    main()
