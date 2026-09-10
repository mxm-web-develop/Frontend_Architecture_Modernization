#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, sys, yaml

try:
    from jsonschema import Draft202012Validator
except Exception as exc:
    raise SystemExit("Missing jsonschema. Install requirements first.") from exc

SKILL_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SKILL_ROOT))
from engine.state.machine import state_prerequisite_errors
from engine.state.project_machine import prerequisite_errors as project_prerequisite_errors, PROJECT_STATES
from engine.evidence.verification import validate_all_passed_gate_evidence

def yload(path,default=None):
    if not Path(path).exists(): return {} if default is None else default
    try: return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or ({} if default is None else default)
    except Exception: return {} if default is None else default

def jload(path,default=None):
    if not Path(path).exists(): return {} if default is None else default
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception: return {} if default is None else default

def schema_validate(repo:Path,path:Path,schema_name:str,errors:list[str]):
    if not path.exists():
        errors.append(f"{path.relative_to(repo)}: missing")
        return
    local=repo/"governance/schemas"/schema_name
    schema_p=local if local.exists() else SKILL_ROOT/"schemas"/schema_name
    if not schema_p.exists():
        errors.append(f"schema missing: {schema_name}")
        return
    try:
        schema=json.loads(schema_p.read_text(encoding="utf-8"))
        data=jload(path) if path.suffix==".json" else yload(path)
        for err in Draft202012Validator(schema).iter_errors(data):
            loc=".".join(str(x) for x in err.path)
            errors.append(f"{path.relative_to(repo)}{'.'+loc if loc else ''}: {err.message}")
    except Exception as exc:
        errors.append(f"{path.relative_to(repo)}: schema validation failed: {exc}")

def markdown_frontmatter(path:Path):
    text=path.read_text(encoding="utf-8",errors="replace")
    if not text.startswith("---\n"): return {}
    parts=text.split("---",2)
    if len(parts)<3: return {}
    try: return yaml.safe_load(parts[1]) or {}
    except Exception: return {}

def validate_language(repo:Path,project:dict,errors:list[str],warnings:list[str]):
    language=project.get("language") or {}
    if not language.get("enforce_human_documentation"): return
    expected=language.get("human_documentation")
    roots=language.get("governed_markdown") or ["docs","migration","handoff"]
    # AGENTS is always governed in v1.5.
    agents=repo/"AGENTS.md"
    if not agents.exists():
        errors.append("AGENTS.md: missing")
    for root_name in roots:
        base=repo/root_name
        if not base.exists(): continue
        for p in sorted(base.rglob("*.md")):
            if "evidence" in p.parts: continue
            fm=markdown_frontmatter(p)
            rel=str(p.relative_to(repo)).replace("\\","/")
            if not fm:
                errors.append(f"{rel}: governed Markdown requires frontmatter language={expected}")
            elif fm.get("language")!=expected:
                errors.append(f"{rel}: language={fm.get('language')!r}, expected {expected!r}")

def structure_checks(repo:Path,domain:str|None):
    errors=[]; warnings=[]
    files=[
      ("governance/project.yaml","project.schema.json"),
      ("governance/project-status.yaml","project-status.schema.json"),
      ("governance/current-system.yaml","current-system.schema.json"),
      ("governance/framework-strategy.yaml","framework-strategy.schema.json"),
      ("governance/architecture-assessment.yaml","architecture-assessment.schema.json"),
      ("governance/modernization-constitution.yaml","modernization-constitution.schema.json"),
      ("governance/human-documentation.yaml","human-documentation.schema.json"),
      ("migration/registry.yaml","registry.schema.json"),
      ("migration/system/legacy-system-map.yaml","legacy-system-map.schema.json"),
      ("migration/system/domain-map.yaml","domain-map.schema.json"),
      ("migration/system/api-catalog.yaml","api-catalog.schema.json"),
      ("migration/system/architecture-remediation.yaml","architecture-remediation.schema.json"),
    ]
    for rel,schema in files: schema_validate(repo,repo/rel,schema,errors)
    project=yload(repo/"governance/project.yaml")
    if project:
        validate_language(repo,project,errors,warnings)
        sources=(project.get("repositories") or {}).get("sources") or []
        if sources:
            legacy=(repo/sources[0].get("path","")).resolve()
            if legacy==repo.resolve(): errors.append("project boundary: legacy and target must be separate repositories")
            if not legacy.exists(): errors.append(f"legacy source unreachable: {legacy}")
    domains_root=repo/"migration/domains"
    candidates=[domains_root/domain] if domain else (sorted(x for x in domains_root.iterdir() if x.is_dir()) if domains_root.exists() else [])
    required={
      "status.yaml":"domain-status.schema.json",
      "legacy-baseline.yaml":"legacy-baseline.schema.json",
      "inventory.yaml":"inventory.schema.json",
      "route-map.yaml":"route-map.schema.json",
      "api-dataflow.yaml":"api-dataflow.schema.json",
      "responsibility-review.yaml":"responsibility-review.schema.json",
      "target-contract.yaml":"target-contract.schema.json",
      "capability-map.yaml":"capability-map.schema.json",
      "source-target-map.yaml":"source-target-map.schema.json",
      "parity-matrix.yaml":"parity-matrix.schema.json",
      "functional-scenarios.yaml":"functional-scenarios.schema.json",
      "visual-manifest.json":"visual-manifest.schema.json",
      "cutover-status.yaml":"cutover-status.schema.json",
    }
    for d in candidates:
        if not d.exists():
            errors.append(f"domain not found: {d}")
            continue
        for name,schema in required.items(): schema_validate(repo,d/name,schema,errors)
    return errors,warnings

def state_checks(repo:Path,domain:str|None):
    errors=[]; warnings=[]
    ps=yload(repo/"governance/project-status.yaml")
    state=ps.get("state")
    if state not in PROJECT_STATES:
        errors.append(f"project state invalid: {state}")
    elif state!="DISCOVERED":
        for e in project_prerequisite_errors(repo,state):
            errors.append(f"project/{state}: {e}")
    registry=yload(repo/"migration/registry.yaml",{"domains":{}})
    domains=list((registry.get("domains") or {}).keys())
    if domain: domains=[domain]
    for name in domains:
        p=repo/"migration/domains"/name/"status.yaml"
        if not p.exists():
            errors.append(f"{name}: status missing")
            continue
        s=yload(p); current=s.get("state")
        if current and current!="DISCOVERED":
            for e in state_prerequisite_errors(repo,name,current):
                errors.append(f"{name}/{current}: {e}")
        for e in validate_all_passed_gate_evidence(repo,name,s):
            errors.append(e)
    return errors,warnings

def completeness_checks(repo:Path,domain:str|None):
    errors=[]; warnings=[]
    current=yload(repo/"governance/current-system.yaml")
    raw=repo/"migration/system/raw-analysis"
    manifest=jload(raw/"analysis-manifest.json",{})
    routes=jload(raw/"routes.json",{"routes":[]}).get("routes",[])
    apis=jload(raw/"apis.json",{"apis":[]}).get("apis",[])
    api_signals_data=jload(raw/"api-signals.json",{"signals":[],"count":0,"unresolved":0})
    api_signals=api_signals_data.get("signals",[])
    files=jload(raw/"files.json",{"files":[]}).get("files",[])
    detected=current.get("detected") or {}
    router=detected.get("router")
    framework=detected.get("framework")
    if current.get("status")=="MODELED":
        if not manifest: errors.append("current system claims MODELED but analysis-manifest.json is missing")
        if not files: errors.append("current system claims MODELED but no source files were recovered")
        if router and not routes:
            errors.append(f"router `{router}` detected but routes=0; add analyzer support or runtime/custom route-manifest evidence")
        if framework in {"vue","react","nextjs"} and not manifest.get("adapter"):
            errors.append("recognized framework but analysis adapter is missing")
    api_catalog=yload(repo/"migration/system/api-catalog.yaml",{"apis":[]})
    if len(api_catalog.get("apis") or []) != len({(x.get("method"),x.get("endpoint")) for x in apis if x.get("endpoint")}):
        warnings.append("canonical api-catalog count differs from normalized raw API facts")
    unresolved_api=[x for x in api_signals if not x.get("resolved")]
    if api_signals and not (api_catalog.get("apis") or []):
        errors.append(
            f"{len(api_signals)} HTTP/API call signal(s) detected but canonical API catalog has 0 resolved endpoints; "
            "extend analyzer/custom wrapper hints or provide runtime evidence before claiming discovery completeness"
        )
    elif unresolved_api:
        warnings.append(
            f"{len(unresolved_api)} HTTP/API call signal(s) remain unresolved; API discovery is PARTIAL"
        )
    legacy_map=yload(repo/"migration/system/legacy-system-map.yaml")
    if current.get("status")=="MODELED" and not legacy_map.get("summary"):
        errors.append("legacy-system-map summary is empty after discovery")
    candidates=yload(repo/"migration/system/capability-candidates.yaml",{"candidates":[]})
    if routes and not candidates.get("candidates"):
        errors.append("routes were recovered but capability candidate queue is empty")
    commands=yload(repo/"governance/commands.yaml",{"commands":{}}).get("commands") or {}
    project_state=yload(repo/"governance/project-status.yaml").get("state")
    advanced_states={"TARGET_FOUNDATION_READY","MODERNIZATION_ACTIVE","HANDOFF_READY"}
    if project_state in advanced_states:
        for key in ("build","lint","typecheck"):
            if not commands.get(key): errors.append(f"project state {project_state} requires governance command `{key}` to be configured")
    elif project_state in {"CURRENT_SYSTEM_MODELED","ARCHITECTURE_ASSESSED","FRAMEWORK_STRATEGY_CONFIRMED"}:
        for key in ("build","lint","typecheck"):
            if not commands.get(key):
                warnings.append(f"governance command `{key}` is not configured yet; it becomes mandatory before TARGET_FOUNDATION_READY")
    registry=yload(repo/"migration/registry.yaml",{"domains":{}})
    names=list((registry.get("domains") or {}).keys())
    if domain: names=[domain]
    for name in names:
        d=repo/"migration/domains"/name
        status=yload(d/"status.yaml"); state=status.get("state")
        caps=yload(d/"capability-map.yaml",{"capabilities":[]}).get("capabilities") or []
        if state and state!="DISCOVERED" and not caps:
            errors.append(f"{name}: state={state} but approved capability ledger is empty")
        if state=="MODERNIZED":
            report=d/"modernization-plan.md"
            if not report.exists(): errors.append(f"{name}: MODERNIZED but modernization-plan.md missing")
    machine_report=repo/"migration/system/machine-analysis-report.md"
    human_root=repo/"docs/modernization"
    human_required=[
        human_root/"README.md",
        human_root/"project-overview.md",
        human_root/"architecture-modernization-plan.md",
        human_root/"progress.md",
        human_root/"technical-analysis.md",
    ]
    if project_state in {"CURRENT_SYSTEM_MODELED","ARCHITECTURE_ASSESSED","FRAMEWORK_STRATEGY_CONFIRMED","TARGET_FOUNDATION_READY","MODERNIZATION_ACTIVE","HANDOFF_READY"}:
        if not machine_report.exists():
            warnings.append("technical machine report has not been generated; run `modernize report system`")
        else:
            text=machine_report.read_text(encoding="utf-8",errors="replace")
            if text.count("## ")<18:
                errors.append("machine-analysis-report.md does not contain the required 18 technical sections")
        missing_human=[str(x.relative_to(repo)) for x in human_required if not x.exists()]
        if missing_human:
            errors.append(f"human modernization documentation missing: {missing_human}; run `modernize report system`")
        else:
            import re
            forbidden=[
                (r"\bNone\b","Python None"),
                (r"\bnull\b","raw null"),
                (r"\bCAP-CAND-[A-Z0-9-]+\b","Capability candidate ID"),
                (r"\bMOD-CAND-[A-Z0-9-]+\b","Domain candidate ID"),
                (r"\bREM-[A-Z0-9-]+\b","Remediation ID"),
            ]
            for human_doc in [human_root/"project-overview.md",human_root/"architecture-modernization-plan.md",human_root/"progress.md"]:
                content=human_doc.read_text(encoding="utf-8",errors="replace")
                for pattern,label in forbidden:
                    if re.search(pattern,content):
                        errors.append(f"{human_doc.relative_to(repo)} exposes {label} in primary human text")
    return errors,warnings

def evidence_checks(repo:Path,domain:str|None):
    errors=[]; warnings=[]
    registry=yload(repo/"migration/registry.yaml",{"domains":{}})
    names=list((registry.get("domains") or {}).keys())
    if domain: names=[domain]
    for name in names:
        p=repo/"migration/domains"/name/"status.yaml"
        if not p.exists(): continue
        for e in validate_all_passed_gate_evidence(repo,name,yload(p)): errors.append(e)
    return errors,warnings

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--domain")
    ap.add_argument("--mode",choices=["structure","state","completeness","all"],default="all")
    args=ap.parse_args(); repo=Path(args.repo).resolve()
    checks=[]
    if args.mode in {"structure","all"}: checks.append(("STRUCTURE",structure_checks))
    if args.mode in {"state","all"}: checks.append(("STATE",state_checks))
    if args.mode in {"completeness","all"}: checks.append(("COMPLETENESS",completeness_checks))
    if args.mode=="all": checks.append(("EVIDENCE",evidence_checks))
    total_errors=[]; total_warnings=[]
    for label,fn in checks:
        errors,warnings=fn(repo,args.domain)
        total_errors.extend([f"{label}: {x}" for x in errors])
        total_warnings.extend([f"{label}: {x}" for x in warnings])
        if errors:
            print(f"{label} FAIL: {len(errors)} error(s)")
        elif warnings:
            print(f"{label} PASS_WITH_WARNINGS: {len(warnings)} warning(s)")
        else:
            print(f"{label} PASS")
    for w in total_warnings: print("WARN:",w)
    for e in total_errors: print("ERROR:",e)
    if total_errors:
        print(f"VALIDATION FAIL: {len(total_errors)} error(s), {len(total_warnings)} warning(s)")
        return 1
    if total_warnings:
        print(f"VALIDATION PASS_WITH_WARNINGS: {len(total_warnings)} warning(s)")
        return 0
    print("VALIDATION PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
