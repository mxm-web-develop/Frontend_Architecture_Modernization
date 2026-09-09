from pathlib import Path
import yaml
VALID={'LEGACY_PARITY','LEGACY_DELTA','ARCHITECTURE_REMEDIATION','GOVERNANCE_ENABLEMENT','NEW_REQUIREMENT'}
def add(repo:Path,id:str,type_:str,title:str,source=None,notes=None):
    if type_ not in VALID: raise ValueError(f'invalid scope type: {type_}')
    p=repo/'governance/scope-register.yaml'; data=yaml.safe_load(p.read_text(encoding='utf-8')) if p.exists() else {'schema_version':'1','items':[]}; data=data or {'schema_version':'1','items':[]}
    if any(x.get('id')==id for x in data.get('items',[])): raise ValueError(f'duplicate scope id: {id}')
    item={'id':id,'type':type_,'title':title,'status':'DEFERRED' if type_=='NEW_REQUIREMENT' else 'ACTIVE','source':source,'notes':notes or []}; data.setdefault('items',[]).append(item)
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8'); return item
