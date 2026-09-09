from pathlib import Path
import json, re, yaml


def package_data(repo: Path):
    p=repo/'package.json'
    if not p.exists(): return {},{}
    try: pkg=json.loads(p.read_text(encoding='utf-8'))
    except Exception: pkg={}
    return pkg,{**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})}


def major(version):
    m=re.search(r'(\d+)',str(version or '')); return int(m.group(1)) if m else None


def detect_adapter(legacy: Path):
    _,deps=package_data(legacy)
    if 'next' in deps: return 'nextjs-generic'
    if 'vue' in deps and major(deps.get('vue'))==2: return 'vue2-ast'
    if 'vue' in deps: return 'vue3-generic'
    if 'react' in deps: return 'react-generic'
    return 'generic-static'


def package_manager(repo: Path):
    for name,value in [('pnpm-lock.yaml','pnpm'),('yarn.lock','yarn'),('package-lock.json','npm'),('bun.lockb','bun')]:
        if (repo/name).exists(): return value
    return None


def model_current_system(repo: Path, legacy: Path, raw_dir: Path, adapter: str):
    project={}
    p=raw_dir/'project.json'
    if p.exists(): project=json.loads(p.read_text(encoding='utf-8'))
    framework='unknown'; version=None; router=None; state=None; build=None
    fw=project.get('framework')
    if isinstance(fw,dict) and 'name' in fw:
        framework=fw.get('name') or 'unknown'; version=fw.get('version')
    elif isinstance(fw,dict):
        if fw.get('vue'):
            framework='vue'; version=fw.get('vue'); router=fw.get('vue_router'); state=fw.get('vuex')
    router=project.get('router') or router
    state=project.get('state') or state
    b=project.get('build')
    if isinstance(b,str): build=b
    elif isinstance(b,dict):
        build=next((k for k,v in b.items() if v),None)
    manifest=raw_dir/'analysis-manifest.json'
    data={
      'schema_version':'1','status':'MODELED','source_repository':'legacy-frontend',
      'detected':{'framework':framework,'framework_version':str(version) if version else None,'router':router,'state':state,'build':build,'package_manager':package_manager(legacy)},
      'analysis':{'adapter':adapter,'manifest':str(manifest.relative_to(repo)).replace('\\','/') if manifest.exists() else None},
      'runtime_unknowns':[]
    }
    out=repo/'governance/current-system.yaml'; out.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return data
