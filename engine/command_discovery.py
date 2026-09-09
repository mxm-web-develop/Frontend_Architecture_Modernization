from pathlib import Path
import json, yaml


def detect_package_manager(legacy: Path):
    if (legacy/'pnpm-lock.yaml').exists(): return 'pnpm'
    if (legacy/'yarn.lock').exists(): return 'yarn'
    if (legacy/'package-lock.json').exists(): return 'npm'
    if (legacy/'bun.lockb').exists(): return 'bun'
    return 'npm'


def discover(repo: Path, legacy: Path):
    pkg={}
    p=legacy/'package.json'
    if p.exists():
        try: pkg=json.loads(p.read_text(encoding='utf-8'))
        except Exception: pkg={}
    scripts=pkg.get('scripts') or {}
    pm=detect_package_manager(legacy)
    prefix='npm run' if pm=='npm' else pm
    aliases={
      'dev':['dev','start'],
      'build':['build'],
      'test':['test','test:unit','unit'],
      'e2e':['e2e','test:e2e','test:integration'],
      'lint':['lint'],
      'typecheck':['typecheck','type-check','check-types'],
    }
    commands={'install':f'{pm} install'}; mapped={}
    for key,names in aliases.items():
        selected=next((n for n in names if n in scripts),None)
        commands[key]=f'{prefix} {selected}' if selected else None
        mapped[key]=selected
    commands['governance_validate']='modernize validate --all --repo .'
    data={'schema_version':'1','commands':commands,'discovery':{'source':'legacy package.json','package_manager':pm,'script_keys':sorted(scripts.keys()),'mapped':mapped}}
    (repo/'governance/commands.yaml').write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return data
