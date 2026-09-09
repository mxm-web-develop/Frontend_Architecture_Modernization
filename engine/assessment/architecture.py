from pathlib import Path
import json, yaml
from engine.assessment.code_health import scan as scan_code_health


def _count_raw(raw: Path, name: str, key: str):
    p=raw/name
    if not p.exists(): return 0
    try: d=json.loads(p.read_text(encoding='utf-8'))
    except Exception: return 0
    if 'count' in d: return int(d.get('count') or 0)
    v=d.get(key); return len(v) if isinstance(v,list) else 0


def assess(repo: Path, legacy: Path):
    raw=repo/'migration/system/raw-analysis'; health=scan_code_health(legacy)
    health_path=raw/'code-health.json'; health_path.parent.mkdir(parents=True,exist_ok=True)
    health_path.write_text(json.dumps(health,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    has_agents=(legacy/'AGENTS.md').exists(); has_gov=(legacy/'governance').exists()
    doc_files=[]
    if (legacy/'docs').exists(): doc_files.extend(legacy.joinpath('docs').rglob('*.md'))
    for name in ('README.md','CLAUDE.md','ARCHITECTURE.md','CONTRIBUTING.md'):
        if (legacy/name).exists(): doc_files.append(legacy/name)
    docs_count=len({str(x) for x in doc_files})
    legacy_doc_names=[str(x.relative_to(legacy)).replace('\\','/') for x in doc_files[:50]]
    imports=_count_raw(raw,'imports.json','edges'); apis=_count_raw(raw,'apis.json','apis'); routes=_count_raw(raw,'routes.json','routes')
    api_signals_data={}
    api_signals_p=raw/'api-signals.json'
    if api_signals_p.exists():
        try: api_signals_data=json.loads(api_signals_p.read_text(encoding='utf-8'))
        except Exception: api_signals_data={}
    api_signals=int(api_signals_data.get('count') or 0)
    api_unresolved=int(api_signals_data.get('unresolved') or 0)
    large=health['summary']['large_files']; code_score=health['summary']['score']
    ai_score=min(100,(35 if has_agents else 0)+(45 if has_gov else 0)+(20 if docs_count else 0))
    modularity=max(20,80-min(50,large*5)-min(30,imports//250))
    dependency=max(20,85-min(65,imports//150))
    # API architecture quality cannot be scored honestly while static discovery is partial.
    # Endpoint count is discovery volume, not architecture quality.
    api_score = None if (api_unresolved > 0 or (api_signals > 0 and apis == 0)) else (
        max(25,85-min(60,apis//50)) if apis > 0 else None
    )
    api_findings=[]
    if api_signals > 0 and apis == 0:
        api_findings.append({
            'type':'API_DISCOVERY_INCOMPLETE','severity':'high',
            'evidence':{'api_signals':api_signals,'resolved_endpoints':apis,'unresolved_signals':api_unresolved}
        })
    elif api_unresolved > 0:
        api_findings.append({
            'type':'API_DISCOVERY_PARTIAL','severity':'medium',
            'evidence':{'api_signals':api_signals,'resolved_endpoints':apis,'unresolved_signals':api_unresolved}
        })
    elif apis > 0:
        api_findings.append({'type':'API_OWNERSHIP_REVIEW','severity':'medium','evidence':{'api_usages':apis}})
    else:
        api_findings.append({'type':'API_DISCOVERY_NO_SIGNAL','severity':'medium','evidence':{'api_signals':0,'resolved_endpoints':0}})
    integration=max(25,75-min(35,large*3))
    documentation=min(100,20+min(60,docs_count*4)+(20 if has_agents else 0))
    data={
      'schema_version':'1','status':'COMPLETE','constitution':'governance/modernization-constitution.yaml',
      'dimensions':{
        'ai_native':{'score':ai_score,'findings':([] if ai_score>=70 else [{'type':'AI_NATIVE_GOVERNANCE_GAP','severity':'high','evidence':{'AGENTS.md':has_agents,'governance':has_gov,'legacy_docs_count':docs_count,'legacy_docs':legacy_doc_names,'note':'Legacy documentation may exist even when modernization governance is absent.'}}])},
        'capability_modularity':{'score':modularity,'findings':[{'type':'LEGACY_STRUCTURE_REQUIRES_CAPABILITY_REVIEW','severity':'medium','evidence':{'routes':routes,'imports':imports}}]},
        'dependency_governance':{'score':dependency,'findings':[{'type':'IMPORT_GRAPH_REVIEW','severity':'medium','evidence':{'imports':imports}}]},
        'state_isolation':{'score':None,'findings':[{'type':'REQUIRES_SEMANTIC_REVIEW','severity':'medium'}]},
        'api_data_flow':{'score':api_score,'findings':api_findings},
        'code_health':{'score':code_score,'findings':health['findings']},
        'documentation':{'score':documentation,'findings':([] if documentation>=70 else [{'type':'DOCUMENTATION_GAP','severity':'high','evidence':{'docs_count':docs_count}}])},
        'integration_readiness':{'score':integration,'findings':[{'type':'PUBLIC_MODULE_CONTRACTS_REQUIRED','severity':'high'}]},
        'framework_lifecycle':{'score':None,'findings':[{'type':'FRAMEWORK_STRATEGY_REQUIRES_RECOMMENDATION','severity':'medium'}]},
      },
      'remediation_backlog':[]
    }
    out=repo/'governance/architecture-assessment.yaml'; out.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return data
