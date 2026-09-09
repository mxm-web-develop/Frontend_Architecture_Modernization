from __future__ import annotations
from pathlib import Path, PurePosixPath
import json, yaml
from collections import defaultdict

SOURCE_FOLDER_DENY={
    'components','views','pages','utils','common','shared','assets','styles','hooks',
    'composables','store','router','api','services','config','data','lib','types',
    'requests','request','constants','helpers','plugins','directives','layouts'
}

def _json(path:Path,default):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return default

def _yaml(path:Path,default):
    if not path.exists(): return default
    try: return yaml.safe_load(path.read_text(encoding='utf-8')) or default
    except Exception: return default

def _dump_yaml(path:Path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')

def _first_segment(path:str):
    path=(path or '').split('?')[0].strip('/')
    if not path: return None
    seg=path.split('/')[0]
    if seg.startswith(':') or seg in {'api','login','auth'}: return None
    return seg

def _api_group(endpoint:str):
    if not endpoint or not endpoint.startswith('/'): return None
    stripped=endpoint.strip('/')
    if not stripped: return None
    first=stripped.split('/')[0]
    if first in {'api','v1','v2','v3'} and '/' in stripped:
        parts=stripped.split('/')
        return parts[1] if len(parts)>1 else first
    return first

def normalize(repo:Path):
    raw=repo/'migration/system/raw-analysis'
    current_path=repo/'governance/current-system.yaml'
    routes=_json(raw/'routes.json',{'routes':[]}).get('routes',[])
    apis=_json(raw/'apis.json',{'apis':[]}).get('apis',[])
    api_signals=_json(raw/'api-signals.json',{'signals':[]}).get('signals',[])
    files=_json(raw/'files.json',{'files':[]}).get('files',[])
    imports=_json(raw/'imports.json',{'edges':[]}).get('edges',[])
    manifest=_json(raw/'analysis-manifest.json',{})

    # Canonical API catalog: resolved endpoints + unresolved discovery debt.
    api_groups={}
    for item in apis:
        endpoint=item.get('endpoint') or item.get('url')
        if not endpoint: continue
        key=(str(item.get('method') or 'UNKNOWN').upper(),endpoint)
        row=api_groups.setdefault(key,{
            'id':f'API-{len(api_groups)+1:04d}',
            'method':key[0],'endpoint':endpoint,'sources':[],
            'confidence':((item.get('extraction') or {}).get('level') or 'STATIC_INFERRED')
        })
        src=item.get('file') or item.get('source')
        if src and src not in row['sources']: row['sources'].append(src)
    unresolved_api=[x for x in api_signals if not x.get('resolved')]
    api_catalog={
        'schema_version':'1',
        'apis':list(api_groups.values()),
        'discovery':{
            'signals':len(api_signals),
            'resolved_signals':len(api_signals)-len(unresolved_api),
            'unresolved_signals':len(unresolved_api),
            'status':'INCOMPLETE' if api_signals and not api_groups else ('PARTIAL' if unresolved_api else 'COMPLETE'),
        },
        'unknowns':[{
            'file':x.get('file'),'callee':x.get('callee'),'expression':x.get('expression'),
            'kind':x.get('kind')
        } for x in unresolved_api[:200]],
    }
    _dump_yaml(repo/'migration/system/api-catalog.yaml',api_catalog)

    # Domain/module candidates: route segments and workspace package boundaries are confirmable;
    # src folder hints are recorded separately and are NOT confirmable.
    evidence=defaultdict(lambda:{
        'routes':[],'files':[],'packages':[],'source_folders':[],
        'types':set()
    })

    for route in routes:
        if route.get('redirect'): continue
        seg=_first_segment(route.get('path'))
        if seg:
            evidence[seg]['routes'].append(route.get('path'))
            evidence[seg]['types'].add('ROUTE_SEGMENT')

    for f in files:
        rel=f.get('file') or ''
        parts=rel.split('/')
        if len(parts)>=3 and parts[0]=='packages':
            package=parts[1]
            if package:
                evidence[package]['files'].append(rel)
                evidence[package]['packages'].append(f'packages/{package}')
                evidence[package]['types'].add('PACKAGE_BOUNDARY')
        if len(parts)>=3 and parts[0]=='src':
            folder=parts[1]
            # Source folders are evidence only. Common infrastructure folders such as
            # config/data/lib/types/requests remain visible as Structural Hints but can
            # never be confirmed directly as Domains.
            if folder and folder in {'config','data','lib','types','requests','request'}:
                evidence[folder]['files'].append(rel)
                evidence[folder]['source_folders'].append(f'src/{folder}')
                evidence[folder]['types'].add('SOURCE_FOLDER_HINT')
            elif folder and folder not in SOURCE_FOLDER_DENY:
                evidence[folder]['files'].append(rel)
                evidence[folder]['source_folders'].append(f'src/{folder}')
                evidence[folder]['types'].add('SOURCE_FOLDER_HINT')

    modules=[]
    source_hints=[]
    for name,item in sorted(evidence.items()):
        types=set(item['types'])
        route_count=len(set(item['routes']))
        package_count=len(set(item['packages']))
        file_count=len(set(item['files']))
        eligible=('ROUTE_SEGMENT' in types) or ('PACKAGE_BOUNDARY' in types)
        candidate_type=(
            'ROUTE_AND_PACKAGE' if {'ROUTE_SEGMENT','PACKAGE_BOUNDARY'} <= types
            else 'PACKAGE_BOUNDARY' if 'PACKAGE_BOUNDARY' in types
            else 'ROUTE_SEGMENT' if 'ROUTE_SEGMENT' in types
            else 'SOURCE_FOLDER_HINT'
        )
        row={
            'id':f'MOD-CAND-{len(modules)+1:03d}' if eligible else f'MOD-HINT-{len(source_hints)+1:03d}',
            'name':name,
            'status':'CANDIDATE' if eligible else 'STRUCTURAL_HINT',
            'candidate_type':candidate_type,
            'eligible_for_confirmation':eligible,
            'confidence':'STATIC_INFERRED' if eligible else 'HEURISTIC',
            'evidence':{
                'routes':sorted(set(item['routes']))[:100],
                'packages':sorted(set(item['packages']))[:100],
                'files':sorted(set(item['files']))[:100],
                'source_folders':sorted(set(item['source_folders']))[:100],
            },
            'decision':'NEEDS_SEMANTIC_REVIEW',
        }
        if eligible: modules.append(row)
        else: source_hints.append(row)

    legacy_map_path=repo/'migration/system/legacy-system-map.yaml'
    legacy_map=_yaml(legacy_map_path,{'schema_version':'1'})
    legacy_map['summary']=(
        f"Detected {len(files)} source files, {len(routes)} routes, "
        f"{len(api_catalog['apis'])} resolved API endpoints, "
        f"{len(unresolved_api)} unresolved API signals and {len(imports)} import edges."
    )
    legacy_map['modules']=modules
    legacy_map['structural_hints']=source_hints
    legacy_map['analysis_adapter']=manifest.get('adapter')
    legacy_map['discovery_coverage']=manifest.get('coverage') or {}
    legacy_map['unknowns']=list(manifest.get('unknowns') or [])
    _dump_yaml(legacy_map_path,legacy_map)

    _dump_yaml(repo/'migration/system/domain-map.yaml',{
        'schema_version':'1',
        'domains':[],
        'candidates':[{k:v for k,v in m.items() if k in {
            'id','name','status','candidate_type','eligible_for_confirmation',
            'confidence','evidence','decision'
        }} for m in modules],
        'structural_hints':source_hints,
    })

    # Capability candidate queue: route behavior + resolved API clusters.
    candidate_caps=[]; seen_route=set()
    for route in routes:
        if route.get('redirect'): continue
        path=route.get('path')
        if not path or path in seen_route: continue
        seen_route.add(path)
        candidate_caps.append({
            'id':f'CAP-CAND-{len(candidate_caps)+1:04d}',
            'candidate_type':'ROUTE_BEHAVIOR',
            'inferred_intent':route.get('name') or f'Behavior reachable from {path}',
            'status':'NEEDS_SEMANTIC_REVIEW',
            'confidence':((route.get('extraction') or {}).get('level') or 'STATIC_INFERRED'),
            'evidence':{
                'routes':[path],
                'sources':[route.get('file')] if route.get('file') else [],
            },
        })

    api_clusters=defaultdict(lambda:{'apis':[],'sources':[]})
    for row in api_catalog['apis']:
        group=_api_group(row.get('endpoint'))
        if not group: continue
        api_clusters[group]['apis'].append(row.get('endpoint'))
        api_clusters[group]['sources'].extend(row.get('sources') or [])
    for group,data in sorted(api_clusters.items()):
        candidate_caps.append({
            'id':f'CAP-CAND-{len(candidate_caps)+1:04d}',
            'candidate_type':'API_CLUSTER',
            'inferred_intent':f'API-backed behavior around {group}',
            'status':'NEEDS_SEMANTIC_REVIEW',
            'confidence':'HEURISTIC',
            'evidence':{
                'apis':sorted(set(data['apis'])),
                'sources':sorted(set(data['sources'])),
            },
        })

    _dump_yaml(repo/'migration/system/capability-candidates.yaml',{
        'schema_version':'1',
        'note':'Candidates are discovery evidence, not approved CAP-* facts.',
        'candidates':candidate_caps,
    })

    if current_path.exists():
        current=_yaml(current_path,{})
        unknowns=list(current.get('runtime_unknowns') or [])
        for warning in manifest.get('warnings') or []:
            if warning not in unknowns: unknowns.append(warning)
        for unknown in manifest.get('unknowns') or []:
            if unknown not in unknowns: unknowns.append(unknown)
        coverage=manifest.get('coverage') or {}
        current['runtime_unknowns']=unknowns
        current['discovery']={
            'coverage':coverage,
            'warnings':manifest.get('warnings') or [],
            'unknowns':manifest.get('unknowns') or [],
            'api_status':api_catalog['discovery'],
        }
        _dump_yaml(current_path,current)

    return {
        'routes':len(routes),
        'apis':len(api_catalog['apis']),
        'api_signals':len(api_signals),
        'api_unresolved':len(unresolved_api),
        'files':len(files),
        'imports':len(imports),
        'module_candidates':len(modules),
        'structural_hints':len(source_hints),
        'capability_candidates':len(candidate_caps),
    }

def remediation_from_assessment(repo:Path):
    assessment=_yaml(repo/'governance/architecture-assessment.yaml',{})
    items=[]
    for dimension,detail in (assessment.get('dimensions') or {}).items():
        for finding in (detail or {}).get('findings') or []:
            evidence=dict(finding.get('evidence') or {})
            # Preserve file/source identity at top-level for human reports and remediation tooling.
            file_path=finding.get('file') or evidence.get('file') or finding.get('source')
            if file_path and 'file' not in evidence: evidence['file']=file_path
            items.append({
                'id':f'REM-{len(items)+1:04d}',
                'source':'architecture-assessment',
                'dimension':dimension,
                'type':finding.get('type'),
                'severity':finding.get('severity') or 'medium',
                'status':'OPEN',
                'file':file_path,
                'evidence':evidence,
            })
    data={'schema_version':'1','items':items}
    _dump_yaml(repo/'migration/system/architecture-remediation.yaml',data)
    return data
