from __future__ import annotations
from pathlib import Path
import datetime, subprocess, yaml

PROJECT_STATES=[
    "DISCOVERED",
    "CURRENT_SYSTEM_MODELED",
    "ARCHITECTURE_ASSESSED",
    "FRAMEWORK_STRATEGY_CONFIRMED",
    "TARGET_FOUNDATION_READY",
    "MODERNIZATION_ACTIVE",
    "HANDOFF_READY",
]

def load(path:Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def save(path:Path,data):
    path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding="utf-8")

def git_sha(repo:Path):
    try:
        return subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"

def _framework_confirmed(repo:Path):
    p=repo/"governance/framework-strategy.yaml"
    if not p.exists(): return False
    data=load(p); c=data.get("confirmation") or {}
    return data.get("status")=="CONFIRMED" and c.get("confirmed_by")=="human" and bool(c.get("decision"))

def prerequisite_errors(repo:Path,target:str):
    errors=[]
    current=load(repo/"governance/project-status.yaml") if (repo/"governance/project-status.yaml").exists() else {}
    if target=="CURRENT_SYSTEM_MODELED":
        p=repo/"governance/current-system.yaml"
        if not p.exists() or load(p).get("status")!="MODELED": errors.append("current-system.yaml must be MODELED")
        if not (repo/"migration/system/raw-analysis/analysis-manifest.json").exists(): errors.append("raw analysis missing")
    elif target=="ARCHITECTURE_ASSESSED":
        p=repo/"governance/architecture-assessment.yaml"
        if not p.exists() or load(p).get("status") not in {"COMPLETE","APPROVED"}: errors.append("architecture-assessment.yaml must be COMPLETE/APPROVED")
    elif target=="FRAMEWORK_STRATEGY_CONFIRMED":
        if not _framework_confirmed(repo): errors.append("framework strategy requires human confirmation + ADR")
    elif target=="TARGET_FOUNDATION_READY":
        if not _framework_confirmed(repo): errors.append("framework strategy must be confirmed")
        if not (repo/"governance/modernization-constitution.yaml").exists(): errors.append("modernization constitution missing")
        if not (repo/"governance/dependency-rules.yaml").exists(): errors.append("dependency rules missing")
    elif target=="MODERNIZATION_ACTIVE":
        registry=load(repo/"migration/registry.yaml") if (repo/"migration/registry.yaml").exists() else {"domains":{}}
        if not (registry.get("domains") or {}): errors.append("at least one confirmed domain is required")
    elif target=="HANDOFF_READY":
        h=repo/"handoff/handoff-status.yaml"
        if not h.exists() or load(h).get("status")!="READY_TO_TRANSITION": errors.append("run `modernize handoff build` first")
        registry=load(repo/"migration/registry.yaml") if (repo/"migration/registry.yaml").exists() else {"domains":{}}
        for domain in (registry.get("domains") or {}):
            s=repo/"migration/domains"/domain/"status.yaml"
            state=load(s).get("state") if s.exists() else None
            if state!="MODERNIZED": errors.append(f"domain {domain} is {state}, expected MODERNIZED")
    return errors

def transition(repo:Path,target:str):
    path=repo/"governance/project-status.yaml"
    if not path.exists(): raise ValueError("project-status.yaml missing")
    data=load(path); current=data.get("state")
    if current not in PROJECT_STATES or target not in PROJECT_STATES: raise ValueError(f"unknown project state: {current} -> {target}")
    if current==target: return data,[]
    idx=PROJECT_STATES.index(current)
    if idx+1>=len(PROJECT_STATES) or PROJECT_STATES[idx+1]!=target: raise ValueError(f"invalid project transition: {current} -> {target}")
    errors=prerequisite_errors(repo,target)
    if errors: return data,errors
    data["state"]=target
    data["state_commit"]=git_sha(repo)
    data.setdefault("history",[]).append({"from":current,"to":target,"at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"commit":data["state_commit"]})
    save(path,data)
    return data,[]
