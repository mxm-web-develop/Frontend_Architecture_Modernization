from pathlib import Path
import itertools, yaml

def _set(value):
    if value is None: return set()
    if isinstance(value,str): return {value}
    if isinstance(value,list):
        out=set()
        for x in value:
            if isinstance(x,str): out.add(x)
            elif isinstance(x,dict): out |= {str(v) for v in x.values() if isinstance(v,str)}
        return out
    if isinstance(value,dict):
        out=set()
        for v in value.values(): out |= _set(v)
        return out
    return set()

def jaccard(a,b):
    if not a and not b: return None
    return len(a&b)/len(a|b) if a|b else 0

def domain_features(domain_dir:Path):
    data=yaml.safe_load((domain_dir/'capability-map.yaml').read_text(encoding='utf-8')) if (domain_dir/'capability-map.yaml').exists() else {'capabilities':[]}; data=data or {'capabilities':[]}
    f={'sources':set(),'apis':set(),'state':set(),'permissions':set(),'entities':set(),'routes':set(),'capabilities':set()}
    for c in data.get('capabilities',[]):
        if c.get('id'): f['capabilities'].add(c['id'])
        f['sources'] |= _set((c.get('legacy') or {}).get('sources'))
        f['apis'] |= _set(c.get('apis') or c.get('api_refs'))
        f['state'] |= _set(c.get('state') or c.get('state_refs'))
        f['permissions'] |= _set(c.get('permissions'))
        f['entities'] |= _set(c.get('entities') or c.get('business_entities'))
        f['routes'] |= _set(c.get('routes'))
    return f

def build(repo:Path):
    root=repo/'migration/domains'; domains={d.name:domain_features(d) for d in root.iterdir() if d.is_dir() and (d/'capability-map.yaml').exists()} if root.exists() else {}
    weights={'sources':0.15,'apis':0.2,'state':0.15,'permissions':0.15,'entities':0.25,'routes':0.10}; pairs=[]
    for a,b in itertools.combinations(sorted(domains),2):
        signals={k:jaccard(domains[a][k],domains[b][k]) for k in weights}; known=[(weights[k],v) for k,v in signals.items() if v is not None]
        score=sum(w*v for w,v in known)/sum(w for w,_ in known) if known else 0
        recommendation='REVIEW'; confidence='LOW'
        if len(known)>=3:
            confidence='HIGH' if len(known)>=5 else 'MEDIUM'
            recommendation='MERGE_CANDIDATE' if score>=0.65 else ('SEPARATE_CANDIDATE' if score<=0.2 else 'REVIEW')
        pairs.append({'a':a,'b':b,'signals':signals,'affinity':round(score,4),'recommendation':recommendation,'confidence':confidence})
    out={'schema_version':'1','weights':weights,'pairs':pairs,'note':'Diagnostic affinity only; business semantics and runtime evidence remain required.'}
    path=repo/'migration/system/domain-affinity.yaml'; path.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8'); return out
