from __future__ import annotations
from pathlib import Path
import yaml


def load(path: Path, default=None):
    if not path.exists(): return {} if default is None else default
    return yaml.safe_load(path.read_text(encoding='utf-8')) or ({} if default is None else default)


def save(path: Path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')


def approve(repo: Path, candidate_id: str, domain: str, capability_id: str, name: str, disposition: str='PRESERVE', decision: str|None=None):
    if not capability_id.startswith('CAP-') or capability_id.startswith('CAP-CAND-'):
        raise ValueError('approved capability id must be stable CAP-* and not CAP-CAND-*')
    d=repo/'migration/domains'/domain
    if not d.exists(): raise ValueError(f'confirmed domain not found: {domain}')
    cand_p=repo/'migration/system/capability-candidates.yaml'
    data=load(cand_p, {'candidates':[]})
    candidates={x.get('id'):x for x in data.get('candidates',[]) if x.get('id')}
    if candidate_id not in candidates: raise ValueError(f'candidate not found: {candidate_id}')
    candidate=candidates[candidate_id]
    cap_p=d/'capability-map.yaml'; caps=load(cap_p, {'schema_version':'1','domain':domain,'capabilities':[]})
    if any(x.get('id')==capability_id for x in caps.get('capabilities',[])):
        raise ValueError(f'capability already exists: {capability_id}')
    item={
      'id':capability_id,
      'name':name,
      'intent':candidate.get('inferred_intent') or name,
      'scope':{'type':'LEGACY_PARITY'},
      'legacy':candidate.get('evidence') or {},
      'migration':{'disposition':disposition},
      'ui':{'visual_policy':'STRICT_PRESERVE'},
      'origin':{'candidate':candidate_id,'decision':decision},
      'unknowns':[],
    }
    if disposition=='REMOVE':
        if not decision: raise ValueError('REMOVE requires --decision ADR-*')
        item['migration']['decision']=decision
    caps.setdefault('capabilities',[]).append(item); save(cap_p,caps)
    candidate['status']='CONFIRMED'; candidate['approved_as']=capability_id; candidate['domain']=domain
    if decision: candidate['decision']=decision
    save(cand_p,data)
    return item
