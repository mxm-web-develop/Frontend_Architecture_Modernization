from __future__ import annotations
from pathlib import Path
import json, datetime, subprocess, yaml
from engine.evidence.verification import validate_all_passed_gate_evidence, validate_gate_evidence
from engine.runtime_capture import (
    LiveRuntimeSpec,
    capability_live_evidence_paths,
    load_live_runtime,
)

DOMAIN_STATES=[
    'DISCOVERED','CAPABILITY_MODELED','RESPONSIBILITY_REVIEWED','TARGET_CONTRACT_DEFINED',
    'REMEDIATION_PLANNED','IMPLEMENTING','FUNCTIONAL_PARITY_CHECK','VISUAL_PARITY_CHECK',
    'ARCHITECTURE_CHECK','TRACEABILITY_CHECK','MODERNIZED','SYNCING'
]
MODERNIZATION_STATES=DOMAIN_STATES
MIGRATION_STATES=DOMAIN_STATES
CUTOVER_STATES=['NOT_READY','CUTOVER_READY','PILOT','ROLLOUT','CUTOVER_VERIFIED','LEGACY_FROZEN']


def git_sha(repo:Path):
    try: return subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
    except Exception: return 'UNKNOWN'

def transition_event(repo:Path,old:str,new:str):
    return {'from':old,'to':new,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':git_sha(repo)}

def load_yaml(path:Path): return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
def save_yaml(path:Path,data): path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')
def _nonempty_list(data,key): return isinstance(data.get(key),list) and len(data.get(key))>0

def _gate_ok(value,allow_na=False):
    allowed={'PASS','WAIVED'}
    if allow_na: allowed.add('NOT_APPLICABLE')
    return value in allowed

def _target_source_paths(source_target:dict):
    paths=[]
    for mapping in source_target.get('mappings',[]):
        target=mapping.get('target') or {}; candidates=target.get('sources') or target.get('paths') or []
        if isinstance(candidates,str): candidates=[candidates]
        for item in candidates:
            if isinstance(item,str): paths.append(item)
            elif isinstance(item,dict):
                value=item.get('file') or item.get('path')
                if value: paths.append(value)
    return paths

def _existing_target_sources(repo:Path,source_target:dict):
    out=[]
    for value in _target_source_paths(source_target):
        p=Path(value); candidate=p if p.is_absolute() else repo/p
        if candidate.exists(): out.append(value)
    return out

def _load_live_runtime_spec(repo:Path) -> LiveRuntimeSpec:
    """读 governance/project.yaml 的 live_runtime 块；缺省给空 spec。"""
    p = repo / 'governance' / 'project.yaml'
    if not p.exists():
        return LiveRuntimeSpec()
    try:
        data = yaml.safe_load(p.read_text(encoding='utf-8')) or {}
    except Exception:
        return LiveRuntimeSpec()
    return load_live_runtime(data)

def _has_live_runtime_evidence(repo:Path, domain:str, cap_id:str) -> bool:
    """domain/live-runtime/<cap_id>*.json 是否存在（snapshot 或 flow）。"""
    d = repo / 'migration' / 'domains' / domain / 'live-runtime'
    if not d.exists() or not cap_id:
        return False
    cap_id = cap_id.lower()
    return any(
        p.is_file() and cap_id in p.name.lower()
        for p in d.rglob('*.json')
    )

def _load_route_coverage(repo:Path, domain:str) -> dict:
    p = repo / 'migration' / 'domains' / domain / 'route-coverage.yaml'
    if not p.exists(): return {'covered': 0, 'total': 0}
    try:
        return yaml.safe_load(p.read_text(encoding='utf-8')) or {'covered': 0, 'total': 0}
    except Exception:
        return {'covered': 0, 'total': 0}

def _load_capability_completeness(repo:Path, domain:str, cap_id:str) -> dict:
    p = repo / 'migration' / 'domains' / domain / 'completeness' / f'{cap_id}.yaml'
    if not p.exists(): return {}
    try:
        return yaml.safe_load(p.read_text(encoding='utf-8')) or {}
    except Exception:
        return {}

def _capability_has_live_evidence(repo:Path, domain:str, cap_id:str) -> bool:
    """如果 profile.live_runtime.required=true，capability 必须有 live evidence。"""
    paths = capability_live_evidence_paths(repo, domain)
    if not paths:
        return False
    cap_id = cap_id.lower()
    return any(cap_id in p.name.lower() for p in paths)

def _framework_confirmed(repo:Path):
    p=repo/'governance/framework-strategy.yaml'
    if not p.exists(): return False,'framework-strategy.yaml missing'
    data=load_yaml(p); confirmation=data.get('confirmation') or {}
    if data.get('status')!='CONFIRMED': return False,'framework strategy must be CONFIRMED at project level'
    if confirmation.get('confirmed_by')!='human': return False,'framework strategy requires human confirmation'
    if not confirmation.get('decision'): return False,'framework strategy requires decision/ADR'
    return True,None


def state_prerequisite_errors(repo:Path,domain:str,target_state:str):
    d=repo/'migration/domains'/domain; errors=[]
    if not d.exists(): return [f'domain directory missing: {d}']
    status=load_yaml(d/'status.yaml') if (d/'status.yaml').exists() else {}
    capabilities=load_yaml(d/'capability-map.yaml') if (d/'capability-map.yaml').exists() else {'capabilities':[]}
    parity=load_yaml(d/'parity-matrix.yaml') if (d/'parity-matrix.yaml').exists() else {'capabilities':[]}
    responsibility=load_yaml(d/'responsibility-review.yaml') if (d/'responsibility-review.yaml').exists() else {}
    target_contract=load_yaml(d/'target-contract.yaml') if (d/'target-contract.yaml').exists() else {}
    functional=load_yaml(d/'functional-scenarios.yaml') if (d/'functional-scenarios.yaml').exists() else {'scenarios':[]}
    source_target=load_yaml(d/'source-target-map.yaml') if (d/'source-target-map.yaml').exists() else {'mappings':[]}

    if target_state=='CAPABILITY_MODELED':
        if not _nonempty_list(capabilities,'capabilities'): errors.append('capability-map.yaml must contain at least one approved capability')
        for cap in capabilities.get('capabilities',[]):
            scope=((cap.get('scope') or {}).get('type')) or 'LEGACY_PARITY'
            if scope=='NEW_REQUIREMENT': errors.append(f"{cap.get('id')}: NEW_REQUIREMENT must not be part of capability reproduction ledger")
    elif target_state=='RESPONSIBILITY_REVIEWED':
        if responsibility.get('status') not in {'complete','approved'}: errors.append('responsibility-review.yaml status must be complete/approved')
    elif target_state=='TARGET_CONTRACT_DEFINED':
        ok,msg=_framework_confirmed(repo)
        if not ok: errors.append(msg)
        if target_contract.get('status') not in {'complete','approved'}: errors.append('target-contract.yaml status must be complete/approved')
        manifest=target_contract.get('module_manifest')
        if not manifest: errors.append('target-contract.yaml must reference module_manifest')
        elif not (repo/manifest).exists(): errors.append(f'module manifest missing: {manifest}')
    elif target_state=='REMEDIATION_PLANNED':
        plan=d/'modernization-plan.md'
        if not plan.exists(): errors.append('modernization-plan.md missing')
        else:
            text=plan.read_text(encoding='utf-8',errors='replace')
            if 'status: planned' not in text and 'status: approved' not in text: errors.append('modernization-plan.md frontmatter status must be planned/approved')
        if not _nonempty_list(source_target,'mappings'): errors.append('source-target-map.yaml must contain mappings')
    elif target_state=='IMPLEMENTING':
        paths=_target_source_paths(source_target)
        if not paths: errors.append('source-target-map target.sources/paths must identify target code locations before IMPLEMENTING')
        elif not _existing_target_sources(repo,source_target): errors.append('IMPLEMENTING requires at least one mapped target source path to exist')
        # === v1.6 P4：live_runtime.required=true 时，IMPLEMENTING 必须已落 live baseline ===
        live_spec = _load_live_runtime_spec(repo)
        if live_spec.required and live_spec.url:
            lb = repo / 'migration' / 'domains' / domain / 'live-runtime'
            if not lb.exists() or not any(lb.glob('*.json')):
                errors.append(
                    f"IMPLEMENTING requires live-runtime baseline under migration/domains/{domain}/live-runtime/ "
                    "(profile.live_runtime.required=true)"
                )
    elif target_state=='FUNCTIONAL_PARITY_CHECK':
        if not _nonempty_list(functional,'scenarios'): errors.append('functional-scenarios.yaml must contain scenarios')
    elif target_state=='VISUAL_PARITY_CHECK':
        strict=any(((c.get('ui') or {}).get('visual_policy')=='STRICT_PRESERVE') for c in capabilities.get('capabilities',[]))
        visual=d/'visual-manifest.json'
        if strict:
            if not visual.exists(): errors.append('visual-manifest.json missing for STRICT_PRESERVE capability')
            else:
                data=json.loads(visual.read_text(encoding='utf-8'))
                if not data.get('scenarios'): errors.append('visual-manifest.json must contain scenarios for STRICT_PRESERVE capability')
    elif target_state=='ARCHITECTURE_CHECK':
        if not _gate_ok((status.get('gates') or {}).get('functional')): errors.append('functional gate must PASS/WAIVED before ARCHITECTURE_CHECK')
        errors.extend(validate_gate_evidence(repo,domain,status,'functional'))
    elif target_state=='TRACEABILITY_CHECK':
        gates=status.get('gates') or {}
        if not _gate_ok(gates.get('architecture')): errors.append('architecture gate must PASS/WAIVED before TRACEABILITY_CHECK')
        strict=any(((c.get('ui') or {}).get('visual_policy')=='STRICT_PRESERVE') for c in capabilities.get('capabilities',[]))
        if strict and not _gate_ok(gates.get('visual')): errors.append('visual gate must PASS/WAIVED before TRACEABILITY_CHECK')
        errors.extend(validate_gate_evidence(repo,domain,status,'architecture'))
        if strict: errors.extend(validate_gate_evidence(repo,domain,status,'visual'))
    elif target_state=='MODERNIZED':
        gates=status.get('gates') or {}
        for gate in ('functional','architecture','traceability'):
            if not _gate_ok(gates.get(gate)): errors.append(f'{gate} gate must PASS/WAIVED')
        if not _gate_ok(gates.get('visual'),allow_na=True): errors.append('visual gate must PASS/WAIVED/NOT_APPLICABLE')
        # === v1.6 P3：live baseline + 100% 路由覆盖 + capability 完整度 ===
        live_spec = _load_live_runtime_spec(repo)
        coverage = _load_route_coverage(repo, domain)
        total = int(coverage.get('total', 0))
        covered = int(coverage.get('covered', 0))
        if total > 0 and covered < total:
            errors.append(f'route coverage {covered}/{total} must be 100% before MODERNIZED')
        for cap in capabilities.get('capabilities', []):
            cap_id = cap.get('id') or ''
            if not cap_id:
                continue
            comp = _load_capability_completeness(repo, domain, cap_id)
            for k in ('route', 'ui', 'api', 'flow'):
                v = comp.get(k)
                if v is not True:
                    errors.append(f'{cap_id}: completeness.{k} must be true (got {v!r})')
            if live_spec.required and live_spec.url:
                if not _capability_has_live_evidence(repo, domain, cap_id):
                    errors.append(
                        f'{cap_id}: missing live-runtime evidence under '
                        f'migration/domains/{domain}/live-runtime/{cap_id}*.json'
                    )
        cap_ids={c.get('id') for c in capabilities.get('capabilities',[]) if c.get('id')}
        parity_ids={c.get('id') for c in parity.get('capabilities',[]) if c.get('id')}
        missing=sorted(cap_ids-parity_ids)
        if missing: errors.append(f'parity entries missing for capabilities: {missing}')
        errors.extend(validate_all_passed_gate_evidence(repo,domain,status))
    elif target_state=='SYNCING':
        if status.get('state') not in {'MODERNIZED','SYNCING'}: errors.append('SYNCING can only start from MODERNIZED')
    return errors


def transition(repo:Path,domain:str,target_state:str):
    d=repo/'migration/domains'/domain; status_path=d/'status.yaml'
    if not status_path.exists(): raise ValueError(f'status file missing: {status_path}')
    status=load_yaml(status_path); current=status.get('state')
    if target_state not in DOMAIN_STATES: raise ValueError(f'unknown domain state: {target_state}')
    if current not in DOMAIN_STATES: raise ValueError(f'unknown current domain state: {current}')
    if current==target_state: return status,[]
    if current=='MODERNIZED' and target_state=='SYNCING': pass
    elif current=='SYNCING' and target_state=='MODERNIZED': pass
    else:
        ordered=[s for s in DOMAIN_STATES if s!='SYNCING']; idx=ordered.index(current)
        if idx+1>=len(ordered) or ordered[idx+1]!=target_state: raise ValueError(f'invalid domain transition: {current} -> {target_state}')
    errors=state_prerequisite_errors(repo,domain,target_state)
    if errors: return status,errors
    status['state']=target_state; status['state_commit']=git_sha(repo); status.setdefault('state_history',[]).append(transition_event(repo,current,target_state)); save_yaml(status_path,status); return status,[]


def cutover_transition(repo:Path,domain:str,target_state:str,reason:str|None=None):
    d=repo/'migration/domains'/domain; path=d/'cutover-status.yaml'
    if not path.exists(): raise ValueError(f'cutover status missing: {path}')
    data=load_yaml(path); current=data.get('state')
    if target_state=='ROLLED_BACK':
        if current not in {'PILOT','ROLLOUT','CUTOVER_VERIFIED','LEGACY_FROZEN'}: raise ValueError(f'cannot rollback from {current}')
        if not reason: return data,['rollback requires an explicit reason']
    else:
        if current not in CUTOVER_STATES or target_state not in CUTOVER_STATES: raise ValueError(f'unknown cutover state: {current} -> {target_state}')
        if CUTOVER_STATES.index(target_state)!=CUTOVER_STATES.index(current)+1: raise ValueError(f'invalid cutover transition: {current} -> {target_state}')
    if target_state=='CUTOVER_READY':
        status=load_yaml(d/'status.yaml')
        if status.get('state')!='MODERNIZED': return data,['domain must be MODERNIZED before CUTOVER_READY']
        if any((status.get('gates') or {}).get(g) not in {'PASS','WAIVED','NOT_APPLICABLE'} for g in ('functional','visual','architecture','traceability')): return data,['all modernization gates must pass/waive before CUTOVER_READY']
    data['state']=target_state; data['last_transition_commit']=git_sha(repo); event=transition_event(repo,current,target_state)
    if reason: event['reason']=reason
    data.setdefault('history',[]).append(event); save_yaml(path,data); return data,[]
