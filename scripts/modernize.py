#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, datetime, fnmatch, hashlib, json, re, shutil, subprocess, sys

try:
    import yaml
except Exception as exc:
    raise SystemExit("Missing PyYAML. Run: python -m pip install -r scripts/requirements.txt") from exc

SKILL_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SKILL_ROOT))
from engine.state.machine import transition as modernization_transition, cutover_transition
from engine.evidence.verification import validate_gate_evidence, rel_ref
from engine.discovery import detect_adapter, model_current_system
from engine.assessment.architecture import assess as architecture_assess
from engine.framework import recommend as framework_recommend, select as framework_select
from engine.scope import add as scope_add
from engine.handoff import build as handoff_build
from engine.module_registry import create as module_create
from engine.assessment.domain_affinity import build as affinity_build
from engine.normalization import normalize as normalize_facts, remediation_from_assessment
from engine.command_discovery import discover as discover_commands
from engine.reporting import build_system as report_system
from engine.domain_registry import create as domain_create
from engine.capability_registry import approve as capability_approve
from engine.state.project_machine import transition as project_transition, PROJECT_STATES


def run(cmd,cwd=None,check=True):
    p=subprocess.run([str(x) for x in cmd],cwd=cwd,text=True)
    if check and p.returncode!=0: raise SystemExit(p.returncode)
    return p.returncode


def capture(cmd,cwd=None):
    p=subprocess.run([str(x) for x in cmd],cwd=cwd,text=True,capture_output=True)
    if p.returncode!=0: raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def load_yaml(path:Path): return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
def save_yaml(path:Path,data): path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')


def project_context(repo:Path):
    p=repo/'governance/project.yaml'
    if not p.exists(): raise SystemExit('Project is not bootstrapped. Run `modernize bootstrap` first.')
    data=load_yaml(p); sources=(data.get('repositories') or {}).get('sources') or []
    if not sources: raise SystemExit('governance/project.yaml has no legacy source')
    legacy=(repo/sources[0].get('path','')).resolve(); profile=load_yaml(repo/'governance/profile.yaml') if (repo/'governance/profile.yaml').exists() else {}
    return data,profile,legacy


def skill_name():
    text=(SKILL_ROOT/'SKILL.md').read_text(encoding='utf-8'); m=re.search(r'(?m)^name:\s*([^\s]+)',text); return m.group(1) if m else None


def doctor(args):
    errors=[]; warnings=[]; ok=[]; expected=skill_name()
    if SKILL_ROOT.name==expected:
        ok.append(f"skill folder: {SKILL_ROOT.name}")
    elif getattr(args,'fix_install_name',False):
        destination=SKILL_ROOT.parent/expected
        if destination.exists():
            errors.append(
                f"cannot repair skill folder name because destination already exists: {destination}"
            )
        else:
            try:
                SKILL_ROOT.rename(destination)
                ok.append(
                    f"renamed skill folder `{SKILL_ROOT.name}` -> `{expected}`; rerun doctor from {destination}"
                )
            except Exception as exc:
                errors.append(
                    f"automatic rename failed: {exc}; manually rename `{SKILL_ROOT.name}` -> `{expected}`"
                )
    else:
        errors.append(
            f"skill folder mismatch: expected `{expected}`, actual `{SKILL_ROOT.name}`; "
            f"run doctor again with `--fix-install-name`, or rename the installed folder exactly "
            f"to `{expected}` (for example: mv \"{SKILL_ROOT.name}\" {expected})"
        )
    for tool in ('git','node'):
        (ok if shutil.which(tool) else errors).append(f'{tool} available' if shutil.which(tool) else f'{tool} not found')
    if args.repo:
        repo=Path(args.repo).resolve()
        if not repo.exists(): errors.append(f'target repo not found: {repo}')
        elif (repo/'governance/project.yaml').exists():
            try:
                project,_,legacy=project_context(repo)
                if legacy.exists(): ok.append(f'legacy source reachable: {legacy}')
                else: errors.append(f'legacy source not reachable: {legacy}')
                scope=(project.get('modernization') or {}).get('scope_mode')
                if scope!='brownfield-new-repository': warnings.append(f'project scope is `{scope}`, expected brownfield-new-repository')
                fw=load_yaml(repo/'governance/framework-strategy.yaml') if (repo/'governance/framework-strategy.yaml').exists() else {}
                ok.append(f"framework strategy: {fw.get('status','MISSING')}")
            except Exception as exc: errors.append(str(exc))
        else: warnings.append('target repo is not bootstrapped')
    for x in ok: print('PASS:',x)
    for x in warnings: print('WARN:',x)
    for x in errors: print('FAIL:',x)
    return 1 if errors else 0


def install_engine(args):
    if args.analyzer or (not args.analyzer and not args.visual):
        d=SKILL_ROOT/'engine/analyzers/vue2'; run(['npm','install','--no-audit','--no-fund'],cwd=d)
    if args.visual or (not args.analyzer and not args.visual):
        d=SKILL_ROOT/'scripts/visual'; run(['npm','install','--no-audit','--no-fund'],cwd=d)
        if args.install_browser: run(['npx','playwright','install','chromium'],cwd=d)
    return 0


def bootstrap(args):
    cmd=[sys.executable,SKILL_ROOT/'scripts/bootstrap.py','--target',args.target,'--legacy',args.legacy,'--profile',args.profile,'--mode',args.mode]
    if args.baseline: cmd += ['--baseline',args.baseline]
    if args.human_language: cmd += ['--human-language',args.human_language]
    if args.force: cmd.append('--force')
    return run(cmd,check=False)


def _typescript_available(legacy:Path):
    candidates=[SKILL_ROOT/'engine/analyzers/vue2/node_modules/typescript/lib/typescript.js',legacy/'node_modules/typescript/lib/typescript.js']
    if shutil.which('npm'):
        try: candidates.append(Path(capture(['npm','root','-g']))/'typescript/lib/typescript.js')
        except Exception: pass
    return any(x.exists() for x in candidates)


def _advance_project_if_possible(repo:Path,target_state:str):
    p=repo/'governance/project-status.yaml'
    if not p.exists(): return
    try:
        data,errors=project_transition(repo,target_state)
        if errors:
            for e in errors: print('WARN: project state not advanced:',e)
        else:
            print(f'PROJECT STATE: {target_state}')
    except ValueError:
        # Already ahead or not the immediate next state; artifact generation remains valid.
        pass


def analyze(args):
    repo=Path(args.repo).resolve(); _,profile,legacy=project_context(repo); adapter=args.adapter or detect_adapter(legacy)
    out=repo/'migration/system/raw-analysis'; out.mkdir(parents=True,exist_ok=True)
    if adapter=='vue2-ast':
        if not _typescript_available(legacy): raise SystemExit('TypeScript AST engine missing. Run `modernize install-engine --analyzer`.')
        rc=run(['node',SKILL_ROOT/'engine/analyzers/vue2/analyze.mjs','--legacy',legacy,'--output',out],check=False)
    else:
        rc=run([sys.executable,SKILL_ROOT/'engine/analyzers/generic/analyze.py','--legacy',legacy,'--output',out,'--adapter',adapter],check=False)
    if rc!=0: return rc
    manifest=out/'analysis-manifest.json'
    if manifest.exists():
        data=json.loads(manifest.read_text(encoding='utf-8')); data['adapter_version']='1.5.1'; manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    current=model_current_system(repo,legacy,out,adapter)
    normalized=normalize_facts(repo)
    current=load_yaml(repo/'governance/current-system.yaml')
    commands=discover_commands(repo,legacy)
    _advance_project_if_possible(repo,'CURRENT_SYSTEM_MODELED')
    report_system(repo)
    print(yaml.safe_dump({'current_system':current,'normalized_facts':normalized,'command_discovery':commands.get('discovery')},sort_keys=False,allow_unicode=True))
    return 0


def assess(args):
    repo=Path(args.repo).resolve(); _,_,legacy=project_context(repo)
    if not (repo/'governance/current-system.yaml').exists() or load_yaml(repo/'governance/current-system.yaml').get('status')!='MODELED':
        raise SystemExit('Current system is not modeled. Run `modernize analyze` first.')
    data=architecture_assess(repo,legacy); remediation=remediation_from_assessment(repo); _advance_project_if_possible(repo,'ARCHITECTURE_ASSESSED'); report_system(repo); print(yaml.safe_dump({'assessment':data,'remediation_items':len(remediation.get('items') or [])},sort_keys=False,allow_unicode=True)); return 0


def framework_cmd(args):
    repo=Path(args.repo).resolve(); p=repo/'governance/framework-strategy.yaml'
    if args.action=='recommend':
        assessment=load_yaml(repo/'governance/architecture-assessment.yaml') if (repo/'governance/architecture-assessment.yaml').exists() else {}
        if assessment.get('status') not in {'COMPLETE','APPROVED'}: raise SystemExit('Run `modernize assess` before framework recommendation.')
        data=framework_recommend(repo); print(yaml.safe_dump(data,sort_keys=False,allow_unicode=True)); return 0
    if args.action=='list':
        if not p.exists(): raise SystemExit('framework-strategy.yaml missing')
        print(p.read_text(encoding='utf-8')); return 0
    if args.action=='select':
        assessment=load_yaml(repo/'governance/architecture-assessment.yaml') if (repo/'governance/architecture-assessment.yaml').exists() else {}
        if assessment.get('status') not in {'COMPLETE','APPROVED'}: raise SystemExit('Architecture assessment must be COMPLETE/APPROVED before framework selection.')
        try: data=framework_select(repo,args.option,args.confirmed_by,args.decision,args.framework)
        except ValueError as exc: print('FAIL:',exc); return 1
        _advance_project_if_possible(repo,'FRAMEWORK_STRATEGY_CONFIRMED'); report_system(repo); print('PASS: framework strategy confirmed'); print(yaml.safe_dump(data,sort_keys=False,allow_unicode=True)); return 0
    return 1


def scope_cmd(args):
    repo=Path(args.repo).resolve(); p=repo/'governance/scope-register.yaml'
    if args.action=='list': print(p.read_text(encoding='utf-8') if p.exists() else 'schema_version: "1"\nitems: []'); return 0
    try: item=scope_add(repo,args.id,args.type,args.title,args.source,args.note)
    except ValueError as exc: print('FAIL:',exc); return 1
    print(yaml.safe_dump(item,sort_keys=False,allow_unicode=True)); return 0


def affinity_cmd(args):
    repo=Path(args.repo).resolve(); data=affinity_build(repo); print(yaml.safe_dump(data,sort_keys=False,allow_unicode=True)); return 0


def module_cmd(args):
    repo=Path(args.repo).resolve(); reg=repo/'governance/modules.yaml'
    if args.action=='list': print(reg.read_text(encoding='utf-8') if reg.exists() else 'schema_version: "1"\nmodules: {}'); return 0
    try: item=module_create(repo,SKILL_ROOT,args.id,args.name,args.path)
    except ValueError as exc: print('FAIL:',exc); return 1
    print(yaml.safe_dump(item,sort_keys=False,allow_unicode=True)); return 0


def validate(args):
    mode='all'
    if args.structure: mode='structure'
    elif args.state: mode='state'
    elif args.completeness: mode='completeness'
    elif args.all: mode='all'
    cmd=[sys.executable,SKILL_ROOT/'scripts/validate_governance.py',args.repo,'--mode',mode]
    if args.domain: cmd += ['--domain',args.domain]
    return run(cmd,check=False)


def project_cmd(args):
    repo=Path(args.repo).resolve()
    p=repo/'governance/project-status.yaml'
    if args.action=='status':
        print(p.read_text(encoding='utf-8') if p.exists() else 'state: MISSING')
        return 0
    try: data,errors=project_transition(repo,args.state)
    except ValueError as exc: print('FAIL:',exc); return 1
    if errors:
        for e in errors: print('ERROR:',e)
        return 1
    print(f'PASS: project -> {args.state}')
    return 0

def domain_cmd(args):
    repo=Path(args.repo).resolve()
    if args.action=='list':
        p=repo/'migration/registry.yaml'; print(p.read_text(encoding='utf-8') if p.exists() else 'domains: {}'); return 0
    try: item=domain_create(repo,SKILL_ROOT,args.id,args.name,args.candidate,args.decision)
    except ValueError as exc: print('FAIL:',exc); return 1
    print('PASS: confirmed domain scaffolded'); print(yaml.safe_dump(item,sort_keys=False,allow_unicode=True)); return 0

def report_cmd(args):
    repo=Path(args.repo).resolve()
    if args.kind in {'system','all'}:
        out=report_system(repo); print(f'PASS: generated {out.relative_to(repo)}')
    return 0


def capability_cmd(args):
    repo=Path(args.repo).resolve()
    if args.action=='list':
        p=repo/'migration/system/capability-candidates.yaml'; print(p.read_text(encoding='utf-8') if p.exists() else 'schema_version: "1"\ncandidates: []'); return 0
    try:
        item=capability_approve(repo,args.candidate,args.domain,args.id,args.name,args.disposition,args.decision)
    except ValueError as exc:
        print('FAIL:',exc); return 1
    print('PASS: capability candidate approved'); print(yaml.safe_dump(item,sort_keys=False,allow_unicode=True)); return 0


def transition_cmd(args):
    repo=Path(args.repo).resolve()
    try: data,errors=modernization_transition(repo,args.domain,args.state)
    except ValueError as exc: print('FAIL:',exc); return 1
    if errors:
        for e in errors: print('ERROR:',e)
        return 1
    print(f'PASS: {args.domain} -> {args.state}'); return 0


def _sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def run_check(args):
    repo=Path(args.repo).resolve(); domain_dir=repo/'migration/domains'/args.domain
    if not domain_dir.exists(): raise SystemExit(f'domain not found: {domain_dir}')
    if bool(args.command)==bool(args.command_key): raise SystemExit('run-check requires exactly one of --command or --command-key')
    command_key=args.command_key; command=args.command
    if command_key:
        commands=load_yaml(repo/'governance/commands.yaml').get('commands') or {}; command=commands.get(command_key)
        if not command: raise SystemExit(f'command key not configured: {command_key}')
    started=datetime.datetime.now(datetime.timezone.utc); cwd=Path(args.cwd).resolve() if args.cwd else repo
    process=subprocess.run(command,cwd=cwd,shell=True,text=True,capture_output=True); ended=datetime.datetime.now(datetime.timezone.utc)
    stamp=started.strftime('%Y%m%dT%H%M%SZ'); evidence_dir=domain_dir/'evidence/gates'/args.gate; evidence_dir.mkdir(parents=True,exist_ok=True)
    stdout=evidence_dir/f'{stamp}.stdout.txt'; stderr=evidence_dir/f'{stamp}.stderr.txt'; evidence=evidence_dir/f'{stamp}.json'
    stdout.write_text(process.stdout or '',encoding='utf-8'); stderr.write_text(process.stderr or '',encoding='utf-8')
    try: commit=capture(['git','-C',repo,'rev-parse','HEAD'])
    except Exception: commit='UNKNOWN'
    data={'schema_version':'1','evidence_type':'command-run','domain':args.domain,'gate':args.gate,'command':command,'command_key':command_key,'cwd':str(cwd),'status':'PASS' if process.returncode==0 else 'FAIL','exit_code':process.returncode,'started_at':started.isoformat(),'ended_at':ended.isoformat(),'commit':commit,'stdout':rel_ref(repo,stdout),'stderr':rel_ref(repo,stderr),'stdout_sha256':_sha256(stdout),'stderr_sha256':_sha256(stderr)}
    evidence.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':data['status'],'evidence':rel_ref(repo,evidence)},ensure_ascii=False,indent=2)); return process.returncode


def gate(args):
    repo=Path(args.repo).resolve(); p=repo/'migration/domains'/args.domain/'status.yaml'
    if not p.exists(): raise SystemExit(f'status missing: {p}')
    data=load_yaml(p)
    if args.status=='PASS':
        if not args.evidence: print(f'FAIL: gate {args.gate}=PASS requires verifiable evidence'); return 1
        trial=json.loads(json.dumps(data)); trial.setdefault('gates',{})[args.gate]='PASS'; trial.setdefault('gate_evidence',{})[args.gate]=args.evidence
        errs=validate_gate_evidence(repo,args.domain,trial,args.gate)
        if errs:
            print(f'FAIL: gate {args.gate}=PASS evidence is invalid')
            for e in errs: print('ERROR:',e)
            return 1
    if args.status in {'WAIVED','NOT_APPLICABLE'} and not args.reason: print(f'FAIL: {args.status} requires --reason'); return 1
    if args.status=='NOT_APPLICABLE' and args.gate!='visual': print('FAIL: NOT_APPLICABLE only valid for visual'); return 1
    data.setdefault('gates',{})[args.gate]=args.status
    if args.evidence: data.setdefault('gate_evidence',{})[args.gate]=args.evidence
    elif args.status!='PASS': data.setdefault('gate_evidence',{}).pop(args.gate,None)
    if args.reason: data.setdefault('gate_reasons',{})[args.gate]=args.reason
    save_yaml(p,data); print(f'PASS: {args.domain} gate {args.gate}={args.status}'); return 0


def visual(args):
    if not (SKILL_ROOT/'scripts/visual/node_modules/playwright').exists(): raise SystemExit('Visual dependencies missing. Run `modernize install-engine --visual --install-browser`.')
    return run(['node',SKILL_ROOT/'scripts/visual/visual_harness.mjs',args.action,'--config',args.config],check=False)


def _legacy_patterns(value):
    patterns=[]
    if isinstance(value,str): patterns.append(value)
    elif isinstance(value,list):
        for x in value: patterns.extend(_legacy_patterns(x))
    elif isinstance(value,dict):
        for k,v in value.items():
            if k in {'file','path','source','sources','files','paths'}: patterns.extend(_legacy_patterns(v))
    return [p.replace('\\','/').lstrip('./') for p in patterns if p]


def map_changed_files_to_capabilities(repo:Path,domain:str,changed:list[dict]):
    d=repo/'migration/domains'/domain; mappings=load_yaml(d/'source-target-map.yaml') if (d/'source-target-map.yaml').exists() else {'mappings':[]}; caps=load_yaml(d/'capability-map.yaml') if (d/'capability-map.yaml').exists() else {'capabilities':[]}; index=[]
    for m in mappings.get('mappings',[]):
        for pat in _legacy_patterns(m.get('legacy') or {}): index.append((m.get('capability_id'),pat,'source-target-map'))
    for c in caps.get('capabilities',[]):
        for pat in _legacy_patterns(c.get('legacy') or {}): index.append((c.get('id'),pat,'capability-map'))
    affected=set(); matches=[]; unresolved=[]
    for item in changed:
        path=(item.get('path') or '').replace('\\','/').lstrip('./'); found=[]
        for cid,pat,source in index:
            prefix=pat.rstrip('/'); matched=fnmatch.fnmatch(path,pat) or path==prefix or (prefix and path.startswith(prefix+'/'))
            if matched and cid: affected.add(cid); found.append({'capability':cid,'pattern':pat,'source':source})
        (matches if found else unresolved).append({'path':path,'matches':found} if found else path)
    return sorted(affected),matches,unresolved


def sync(args):
    repo=Path(args.repo).resolve(); _,_,legacy=project_context(repo); status_path=repo/'migration/domains'/args.domain/'status.yaml'; status=load_yaml(status_path); legacy_state=status.setdefault('legacy',{}); last=legacy_state.get('last_checked_commit') or legacy_state.get('baseline_commit'); head=capture(['git','-C',legacy,'rev-parse','HEAD']); log=repo/'migration/domains'/args.domain/'delta-log.jsonl'
    if args.action=='scan':
        if not last: raise SystemExit('last_checked_commit/baseline_commit missing')
        diff=capture(['git','-C',legacy,'diff','--name-status',f'{last}..{head}']) if last!=head else ''; files=[]
        for line in diff.splitlines():
            parts=line.split('\t');
            if parts: files.append({'status':parts[0],'path':parts[-1]})
        caps,matches,unresolved=map_changed_files_to_capabilities(repo,args.domain,files)
        record={'id':f"DELTA-{args.domain.upper()}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",'scope_type':'LEGACY_DELTA','from_commit':last,'to_commit':head,'affected_files':files,'affected_capabilities':caps,'capability_matches':matches,'unresolved_files':unresolved,'classification':'UNKNOWN' if files else 'ALREADY_COVERED','status':'PENDING' if files else 'RESOLVED'}
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('a',encoding='utf-8') as fh: fh.write(json.dumps(record,ensure_ascii=False)+'\n')
        print(json.dumps(record,ensure_ascii=False,indent=2)); return 0
    records=[json.loads(x) for x in log.read_text(encoding='utf-8').splitlines() if x.strip()] if log.exists() else []; unresolved=[r for r in records if r.get('to_commit')==head and r.get('status') not in {'RESOLVED','WAIVED'}]
    if unresolved: print('FAIL: unresolved legacy delta records'); return 1
    legacy_state['last_checked_commit']=head; save_yaml(status_path,status); print('PASS: last_checked_commit ->',head); return 0


def cutover(args):
    repo=Path(args.repo).resolve()
    if args.action=='status':
        p=repo/'migration/domains'/args.domain/'cutover-status.yaml'; print(p.read_text(encoding='utf-8') if p.exists() else 'NOT_INITIALIZED'); return 0
    try: _,errors=cutover_transition(repo,args.domain,args.state,reason=args.reason)
    except ValueError as exc: print('FAIL:',exc); return 1
    if errors:
        for e in errors: print('ERROR:',e)
        return 1
    print(f'PASS: cutover {args.domain} -> {args.state}'); return 0


def handoff_cmd(args):
    repo=Path(args.repo).resolve()
    if args.action=='status':
        p=repo/'handoff/handoff-status.yaml'; print(p.read_text(encoding='utf-8') if p.exists() else 'NOT_READY'); return 0
    pre=subprocess.run([sys.executable,str(SKILL_ROOT/'scripts/validate_governance.py'),str(repo)],text=True,capture_output=True)
    if pre.returncode!=0:
        print('FAIL: governance/evidence validation must pass before handoff build')
        print(pre.stdout.strip())
        return 1
    try: data=handoff_build(repo,SKILL_ROOT)
    except ValueError as exc: print('FAIL:',exc); return 1
    print('PASS: handoff package built'); print(yaml.safe_dump(data,sort_keys=False,allow_unicode=True)); return 0


def status_cmd(args):
    repo=Path(args.repo).resolve()
    project_status=load_yaml(repo/'governance/project-status.yaml') if (repo/'governance/project-status.yaml').exists() else {}
    rows=[]; registry=load_yaml(repo/'migration/registry.yaml') if (repo/'migration/registry.yaml').exists() else {'domains':{}}
    for dname in (registry.get('domains') or {}):
        p=repo/'migration/domains'/dname/'status.yaml'
        s=load_yaml(p) if p.exists() else {}
        rows.append({'domain':dname,'state':s.get('state'),'gates':s.get('gates',{}),'legacy':s.get('legacy',{})})
    current=load_yaml(repo/'governance/current-system.yaml') if (repo/'governance/current-system.yaml').exists() else {}
    fw=load_yaml(repo/'governance/framework-strategy.yaml') if (repo/'governance/framework-strategy.yaml').exists() else {}
    scope=load_yaml(repo/'governance/scope-register.yaml') if (repo/'governance/scope-register.yaml').exists() else {'items':[]}
    candidates=load_yaml(repo/'migration/system/capability-candidates.yaml') if (repo/'migration/system/capability-candidates.yaml').exists() else {'candidates':[]}
    report=repo/'migration/system/migration-master-report.md'
    print(json.dumps({
      'project_state':project_status.get('state'),
      'current_system':current.get('status'),
      'detected_framework':(current.get('detected') or {}).get('framework'),
      'framework_strategy':fw.get('status'),
      'selected_framework':(fw.get('selected') or {}).get('framework'),
      'capability_candidates':len(candidates.get('candidates') or []),
      'domains':rows,
      'system_report':str(report.relative_to(repo)) if report.exists() else None,
      'deferred_new_requirements':[x.get('id') for x in scope.get('items',[]) if x.get('type')=='NEW_REQUIREMENT']
    },ensure_ascii=False,indent=2))
    return 0

def upgrade_control_plane(args):
    repo=Path(args.repo).resolve(); marker=repo/'.modernization.json'
    if not marker.exists(): raise SystemExit('not an existing modernization project')
    if not (repo/'governance/project-status.yaml').exists(): save_yaml(repo/'governance/project-status.yaml',{'schema_version':'1','state':'DISCOVERED','state_commit':None,'history':[]})
    project=load_yaml(repo/'governance/project.yaml'); project.setdefault('modernization',{'scope_mode':'brownfield-new-repository','new_requirements':'defer','framework_strategy':'undecided-until-confirmed'}); save_yaml(repo/'governance/project.yaml',project); lang=(project.get('language') or {}).get('human_documentation') or 'en'; replacements={'__HUMAN_LANG__':lang}
    for name in ('modernization-constitution.yaml','current-system.yaml','framework-strategy.yaml','architecture-assessment.yaml','scope-register.yaml','modules.yaml'):
        src=SKILL_ROOT/'assets/templates/governance'/name; dst=repo/'governance'/name
        if not dst.exists(): dst.write_text(src.read_text(encoding='utf-8').replace('__HUMAN_LANG__',lang),encoding='utf-8')
    mappings={'ANALYZED':'CURRENT_SYSTEM_MODELED','MIGRATION_PLANNED':'REMEDIATION_PLANNED','MIGRATED':'MODERNIZED'}
    domains=repo/'migration/domains'
    if domains.exists():
        for d in (x for x in domains.iterdir() if x.is_dir()):
            p=d/'status.yaml'
            if p.exists():
                s=load_yaml(p); old=s.get('state'); s['state']=mappings.get(old,old); save_yaml(p,s)
    data=json.loads(marker.read_text(encoding='utf-8')); data['skill_version']='1.5.1'; data['scope']='brownfield-new-repository'; marker.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('PASS: control plane upgraded. Run analyze/assess/framework recommend, then explicitly confirm framework strategy before advancing target design.'); return 0


def build_parser():
    p=argparse.ArgumentParser(prog='modernize',description='Frontend Architecture Modernization v1.5.1 control plane'); sub=p.add_subparsers(dest='command',required=True)
    d=sub.add_parser('doctor'); d.add_argument('--repo'); d.add_argument('--fix-install-name',action='store_true'); d.set_defaults(func=doctor)
    ie=sub.add_parser('install-engine'); ie.add_argument('--analyzer',action='store_true'); ie.add_argument('--visual',action='store_true'); ie.add_argument('--install-browser',action='store_true'); ie.set_defaults(func=install_engine)
    b=sub.add_parser('bootstrap'); b.add_argument('--target',required=True); b.add_argument('--legacy',required=True); b.add_argument('--profile',default=str(SKILL_ROOT/'assets/profiles/brownfield-modernization.yaml')); b.add_argument('--mode',default='cross-repository',choices=['cross-repository','in-place']); b.add_argument('--baseline'); b.add_argument('--human-language'); b.add_argument('--force',action='store_true'); b.set_defaults(func=bootstrap)
    a=sub.add_parser('analyze'); a.add_argument('--repo',default='.'); a.add_argument('--adapter'); a.set_defaults(func=analyze)
    ass=sub.add_parser('assess'); ass.add_argument('--repo',default='.'); ass.set_defaults(func=assess)
    fw=sub.add_parser('framework'); fw.add_argument('action',choices=['recommend','list','select']); fw.add_argument('option',nargs='?'); fw.add_argument('--confirmed-by'); fw.add_argument('--decision'); fw.add_argument('--framework'); fw.add_argument('--repo',default='.'); fw.set_defaults(func=framework_cmd)
    sc=sub.add_parser('scope'); sc.add_argument('action',choices=['add','list']); sc.add_argument('--id'); sc.add_argument('--type',choices=['LEGACY_PARITY','LEGACY_DELTA','ARCHITECTURE_REMEDIATION','GOVERNANCE_ENABLEMENT','NEW_REQUIREMENT']); sc.add_argument('--title'); sc.add_argument('--source'); sc.add_argument('--note',action='append',default=[]); sc.add_argument('--repo',default='.'); sc.set_defaults(func=scope_cmd)
    af=sub.add_parser('affinity'); af.add_argument('--repo',default='.'); af.set_defaults(func=affinity_cmd)
    mo=sub.add_parser('module'); mo.add_argument('action',choices=['create','list']); mo.add_argument('id',nargs='?'); mo.add_argument('--name'); mo.add_argument('--path'); mo.add_argument('--repo',default='.'); mo.set_defaults(func=module_cmd)
    v=sub.add_parser('validate'); v.add_argument('--repo',default='.'); v.add_argument('--domain'); v.add_argument('--structure',action='store_true'); v.add_argument('--state',action='store_true'); v.add_argument('--completeness',action='store_true'); v.add_argument('--all',action='store_true'); v.set_defaults(func=validate)
    pj=sub.add_parser('project'); pj.add_argument('action',choices=['status','transition']); pj.add_argument('state',nargs='?'); pj.add_argument('--repo',default='.'); pj.set_defaults(func=project_cmd)
    dm=sub.add_parser('domain'); dm.add_argument('action',choices=['create','list']); dm.add_argument('id',nargs='?'); dm.add_argument('--name'); dm.add_argument('--candidate'); dm.add_argument('--decision'); dm.add_argument('--repo',default='.'); dm.set_defaults(func=domain_cmd)
    cp=sub.add_parser('capability'); cp.add_argument('action',choices=['list','approve']); cp.add_argument('candidate',nargs='?'); cp.add_argument('--domain'); cp.add_argument('--id'); cp.add_argument('--name'); cp.add_argument('--disposition',default='PRESERVE',choices=['PRESERVE','REPLACE','REMOVE']); cp.add_argument('--decision'); cp.add_argument('--repo',default='.'); cp.set_defaults(func=capability_cmd)
    rp=sub.add_parser('report'); rp.add_argument('kind',choices=['system','all'],default='system',nargs='?'); rp.add_argument('--repo',default='.'); rp.set_defaults(func=report_cmd)
    t=sub.add_parser('transition'); t.add_argument('domain'); t.add_argument('state'); t.add_argument('--repo',default='.'); t.set_defaults(func=transition_cmd)
    rc=sub.add_parser('run-check'); rc.add_argument('gate',choices=['functional','architecture','traceability']); rc.add_argument('domain'); rc.add_argument('--command'); rc.add_argument('--command-key'); rc.add_argument('--cwd'); rc.add_argument('--repo',default='.'); rc.set_defaults(func=run_check)
    g=sub.add_parser('gate'); g.add_argument('domain'); g.add_argument('gate',choices=['functional','visual','architecture','traceability']); g.add_argument('status',choices=['PENDING','PASS','FAIL','WAIVED','NOT_APPLICABLE']); g.add_argument('--evidence',action='append',default=[]); g.add_argument('--reason'); g.add_argument('--repo',default='.'); g.set_defaults(func=gate)
    vi=sub.add_parser('visual'); vi.add_argument('action',choices=['doctor','capture-legacy','capture-target','compare','all']); vi.add_argument('--config',required=True); vi.set_defaults(func=visual)
    sy=sub.add_parser('sync'); sy.add_argument('action',choices=['scan','advance']); sy.add_argument('domain'); sy.add_argument('--repo',default='.'); sy.set_defaults(func=sync)
    c=sub.add_parser('cutover'); c.add_argument('action',choices=['status','transition']); c.add_argument('domain'); c.add_argument('state',nargs='?'); c.add_argument('--reason'); c.add_argument('--repo',default='.'); c.set_defaults(func=cutover)
    h=sub.add_parser('handoff'); h.add_argument('action',choices=['build','status']); h.add_argument('--repo',default='.'); h.set_defaults(func=handoff_cmd)
    s=sub.add_parser('status'); s.add_argument('--repo',default='.'); s.set_defaults(func=status_cmd)
    u=sub.add_parser('upgrade-control-plane'); u.add_argument('--repo',default='.'); u.set_defaults(func=upgrade_control_plane)
    return p


def main():
    args=build_parser().parse_args()
    if args.command=='framework' and args.action=='select' and not args.option: raise SystemExit('framework select requires <OPTION_ID>')
    if args.command=='module' and args.action=='create' and not args.id: raise SystemExit('module create requires <id>')
    if args.command=='domain' and args.action=='create' and not args.id: raise SystemExit('domain create requires <id>')
    if args.command=='capability' and args.action=='approve' and not all([args.candidate,args.domain,args.id,args.name]): raise SystemExit('capability approve requires <candidate> --domain --id --name')
    if args.command=='project' and args.action=='transition' and not args.state: raise SystemExit('project transition requires <state>')
    if args.command=='scope' and args.action=='add' and not all([args.id,args.type,args.title]): raise SystemExit('scope add requires --id --type --title')
    if args.command=='cutover' and args.action=='transition' and not args.state: raise SystemExit('cutover transition requires <state>')
    return args.func(args)

if __name__=='__main__': raise SystemExit(main())
