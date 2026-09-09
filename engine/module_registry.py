from pathlib import Path
import re, yaml

def create(repo:Path,skill_root:Path,module_id:str,name:str|None=None,path:str|None=None):
    safe=re.sub(r'[^a-z0-9-]+','-',module_id.lower()).strip('-'); rel=path or f'modules/{safe}'; root=repo/rel; root.mkdir(parents=True,exist_ok=True)
    manifest=root/'module.manifest.yaml'; readme=root/'README.md'
    if manifest.exists(): raise ValueError(f'module manifest already exists: {manifest}')
    template=(skill_root/'assets/templates/module.manifest.yaml').read_text(encoding='utf-8').replace('__MODULE__',safe)
    data=yaml.safe_load(template) or {}; data['name']=name or safe; manifest.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')
    project=yaml.safe_load((repo/'governance/project.yaml').read_text(encoding='utf-8')) or {}; lang=(project.get('language') or {}).get('human_documentation') or 'en'
    if str(lang).lower().startswith('zh'):
        body=f'''---\nlanguage: {lang}\n---\n# {name or safe}\n\n## 模块职责\n\n## Capability 所有权\n\n## 公共集成接口\n\n## 依赖边界\n\n## 开发与验证\n'''
    else:
        body=f'''---\nlanguage: {lang}\n---\n# {name or safe}\n\n## Responsibilities\n\n## Capability ownership\n\n## Public integration surface\n\n## Dependency boundaries\n\n## Development and verification\n'''
    readme.write_text(body,encoding='utf-8')
    reg_p=repo/'governance/modules.yaml'; reg=yaml.safe_load(reg_p.read_text(encoding='utf-8')) if reg_p.exists() else {'schema_version':'1','modules':{}}; reg=reg or {'schema_version':'1','modules':{}}
    reg.setdefault('modules',{})[safe]={'name':name or safe,'manifest':str(manifest.relative_to(repo)).replace('\\','/'),'documentation':str(readme.relative_to(repo)).replace('\\','/'),'capabilities':[],'public_contracts':[]}; reg_p.write_text(yaml.safe_dump(reg,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return reg['modules'][safe]
