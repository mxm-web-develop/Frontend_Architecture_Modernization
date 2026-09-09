from __future__ import annotations
from pathlib import Path
import re, yaml

def load(path, default=None):
    if not Path(path).exists(): return {} if default is None else default
    return yaml.safe_load(Path(path).read_text(encoding='utf-8')) or ({} if default is None else default)

def human_replacements(lang):
    if str(lang).lower().startswith('zh'):
        return {
          'Modernization Plan':'现代化实施计划','Migration Plan':'现代化实施计划','Migration Decisions':'现代化决策',
          '## Scope':'## 范围','## Capability set':'## Capability 集合','## Target design':'## 目标实现设计',
          '## Functional parity':'## 功能一致性','## Visual parity':'## 视觉一致性','## Architecture gates':'## 架构门禁',
          '## Unknowns':'## 未知项','## Rollback / Cutover':'## 回滚 / 切流',
          'Record explicit product/architecture/design decisions. Do not use this file to hide unknowns.':'记录明确的产品、架构与设计决策。不要用本文件隐藏未知项。'
        }
    return {}

def create(repo:Path,skill_root:Path,domain:str,name:str|None=None,candidate:str|None=None,decision:str|None=None):
    safe=re.sub(r'[^a-z0-9-]+','-',domain.lower()).strip('-')
    if not safe: raise ValueError('invalid domain id')
    if not candidate and not decision: raise ValueError('domain confirmation requires --candidate MOD-CAND-* or --decision ADR-*')
    target=repo/'migration/domains'/safe
    if target.exists(): raise ValueError(f'domain already exists: {safe}')
    domain_map_p=repo/'migration/system/domain-map.yaml'; domain_map=load(domain_map_p,{'schema_version':'1','domains':[],'candidates':[]})
    source_candidate=None
    if candidate:
        source_candidate=next((x for x in domain_map.get('candidates',[]) if x.get('id')==candidate),None)
        if not source_candidate: raise ValueError(f'domain candidate not found: {candidate}')
        if not source_candidate.get('eligible_for_confirmation', False):
            raise ValueError(
                f'domain candidate {candidate} is only a structural hint '
                f'({source_candidate.get("candidate_type")}); confirm a route/package-backed candidate or use --decision ADR-*'
            )
    project=load(repo/'governance/project.yaml'); lang=(project.get('language') or {}).get('human_documentation') or 'en'
    legacy=((project.get('repositories') or {}).get('sources') or [{}])[0]; baseline=legacy.get('baseline_commit') or 'UNKNOWN'
    replacements={'__DOMAIN__':safe,'__LEGACY_BASE__':baseline,'__HUMAN_LANG__':lang,**human_replacements(lang)}
    target.mkdir(parents=True,exist_ok=False)
    for src in sorted((skill_root/'assets/templates/migration/domain').iterdir()):
        if not src.is_file(): continue
        text=src.read_text(encoding='utf-8')
        for k,v in replacements.items(): text=text.replace(k,str(v))
        (target/src.name).write_text(text,encoding='utf-8')
    reg_path=repo/'migration/registry.yaml'; reg=load(reg_path,{'schema_version':'1','domains':{}})
    reg.setdefault('domains',{})[safe]={'status_file':f'domains/{safe}/status.yaml','name':name or safe,'confirmed_from_candidate':candidate,'decision':decision}
    reg_path.write_text(yaml.safe_dump(reg,sort_keys=False,allow_unicode=True),encoding='utf-8')
    domain_map.setdefault('domains',[]).append({'id':safe,'name':name or safe,'status':'CONFIRMED','source_candidate':candidate,'decision':decision})
    if source_candidate:
        source_candidate['status']='CONFIRMED'; source_candidate['confirmed_as']=safe
    domain_map_p.write_text(yaml.safe_dump(domain_map,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return reg['domains'][safe]
