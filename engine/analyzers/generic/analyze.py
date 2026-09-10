#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, re, posixpath

EXT={'.js','.jsx','.ts','.tsx','.vue','.mjs','.cjs'}
SKIP={
    'node_modules','dist','build','.git','coverage','.next','.nuxt',
    '.cursor','.codex','.agents','.agent','.claude','.idea','.vscode',
    'migration','governance','handoff'
}

IMPORT=re.compile(r"(?:from\s+|import\s*\(|require\s*\()\s*[\"']([^\"']+)[\"']")
FETCH_LITERAL=re.compile(r"\bfetch\s*\(\s*[\"']([^\"']+)[\"']")
FETCH_EXPRESSION=re.compile(r"\bfetch\s*\(\s*([^,\n\)]+(?:\([^)]*\))?|`[^`]+`)")
AXIOS_LITERAL=re.compile(r"\baxios\.(get|post|put|patch|delete|head|options)\s*\(\s*[\"']([^\"']+)[\"']", re.I)
HTTP_WRAPPER_NAME = (
    r"(?:"
    r"[A-Za-z_$][\w$]*(?:Request|REQUEST)[\w$]*"
    r"|[A-Za-z_$][\w$]*(?:Api|API|Client|CLIENT|Http|HTTP|Fetch|FETCH)"
    r")"
)
TS_GENERIC = r"(?:\s*<[^()\n]+>)?"
GENERIC_LITERAL_CALL=re.compile(
    rf"\b({HTTP_WRAPPER_NAME}){TS_GENERIC}\s*\(\s*[\"']([^\"']+)[\"']"
)
GENERIC_DYNAMIC_CALL=re.compile(
    rf"\b({HTTP_WRAPPER_NAME}){TS_GENERIC}\s*\(\s*(`[^`]+`|[A-Za-z_$][\w$]*(?:\([^)]*\))?)"
)
API_BASE_CONST=re.compile(
    r"\b([A-Z][A-Z0-9_]*(?:API|BASE|URL|ENDPOINT)[A-Z0-9_]*)\s*=\s*[\"']([^\"']+)[\"']"
)

OBJECT_PATH=re.compile(r"\bpath\s*:\s*[\"']([^\"']*)[\"']")
OBJECT_NAME=re.compile(r"\bname\s*:\s*[\"']([^\"']+)[\"']")
REDIRECT=re.compile(r"\bredirect\s*:\s*[\"']([^\"']+)[\"']")
JSX_ROUTE=re.compile(r"<Route\b[^>]*\bpath\s*=\s*[\"']([^\"']+)[\"']")
ROUTER_HINT=re.compile(
    r"createRouter|createWebHistory|createBrowserRouter|useRoutes|<Routes\b|"
    r"RouteRecordRaw|addRoute\s*\(|ROUTE_DEFS|ROUTES|routeManifest|"
    r"navigation\.manifest|platformNavigation|routes\s*[:=]",
    re.I
)
ROUTE_OBJECT_MARKER=re.compile(
    r"\b(?:component|children|redirect|meta|beforeEnter|loader|element|lazy|index|name)\s*:",
    re.I
)

ROUTE_HELPER_CALL=re.compile(
    r"\b(add|addRoute|redirect|addRedirect|registerRoute|route)"
    r"\s*\(\s*[\"']([^\"']+)[\"']"
    r"(?:\s*,\s*[\"']([^\"']+)[\"'])?",
    re.I
)
ROUTE_TOP_LEVEL_MARKERS={
    'component','children','redirect','meta','beforeEnter','loader',
    'element','lazy','index','name'
}

def should_skip(p:Path, root:Path):
    try: rel=p.relative_to(root)
    except Exception: return True
    return any(x in rel.parts for x in SKIP)

def walk(root:Path):
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in EXT and not should_skip(p,root):
            yield p

def object_slice(text:str,pos:int)->str:
    """Return innermost JS object literal containing pos, with basic string/comment awareness."""
    stack=[]; pairs=[]; i=0; quote=None; escaped=False; line_comment=False; block_comment=False
    while i < len(text):
        ch=text[i]; nxt=text[i+1] if i+1<len(text) else ''
        if line_comment:
            if ch=='\n': line_comment=False
            i+=1; continue
        if block_comment:
            if ch=='*' and nxt=='/': block_comment=False; i+=2; continue
            i+=1; continue
        if quote:
            if escaped: escaped=False
            elif ch=='\\': escaped=True
            elif ch==quote: quote=None
            i+=1; continue
        if ch=='/' and nxt=='/': line_comment=True; i+=2; continue
        if ch=='/' and nxt=='*': block_comment=True; i+=2; continue
        if ch in ("'",'"','`'): quote=ch; i+=1; continue
        if ch=='{': stack.append(i)
        elif ch=='}' and stack:
            start=stack.pop(); pairs.append((start,i+1))
        i+=1
    containing=[pair for pair in pairs if pair[0] <= pos < pair[1]]
    if not containing: return text[max(0,pos-400):min(len(text),pos+900)]
    start,end=min(containing,key=lambda x:x[1]-x[0])
    return text[start:end]

def top_level_object_keys(obj:str)->set[str]:
    """Collect only top-level object-literal keys; nested query/meta keys do not count."""
    keys=set()
    if not obj: return keys
    depth=0; i=0; quote=None; escaped=False; line_comment=False; block_comment=False
    while i < len(obj):
        ch=obj[i]; nxt=obj[i+1] if i+1<len(obj) else ''
        if line_comment:
            if ch=='\n': line_comment=False
            i+=1; continue
        if block_comment:
            if ch=='*' and nxt=='/': block_comment=False; i+=2; continue
            i+=1; continue
        if quote:
            if escaped: escaped=False
            elif ch=='\\': escaped=True
            elif ch==quote: quote=None
            i+=1; continue
        if ch=='/' and nxt=='/': line_comment=True; i+=2; continue
        if ch=='/' and nxt=='*': block_comment=True; i+=2; continue
        if ch in ("'",'"','`'): quote=ch; i+=1; continue
        if ch=='{':
            depth+=1; i+=1; continue
        if ch=='}':
            depth=max(0,depth-1); i+=1; continue
        if depth==1 and (ch.isalpha() or ch in '_$'):
            start=i; i+=1
            while i<len(obj) and (obj[i].isalnum() or obj[i] in '_$'): i+=1
            key=obj[start:i]
            j=i
            while j<len(obj) and obj[j].isspace(): j+=1
            if j<len(obj) and obj[j]==':':
                keys.add(key)
            continue
        i+=1
    return keys

def is_route_object(obj:str)->bool:
    keys=top_level_object_keys(obj)
    return 'path' in keys and bool(keys & ROUTE_TOP_LEVEL_MARKERS)

def top_level_string_value(obj:str,key:str)->str|None:
    """Read a simple quoted top-level property without matching nested objects."""
    keys=top_level_object_keys(obj)
    if key not in keys: return None
    # Walk the object again and only match at depth 1.
    depth=0; i=0; quote=None; escaped=False
    while i<len(obj):
        ch=obj[i]
        if quote:
            if escaped: escaped=False
            elif ch=='\\': escaped=True
            elif ch==quote: quote=None
            i+=1; continue
        if ch in ("'",'"','`'): quote=ch; i+=1; continue
        if ch=='{': depth+=1; i+=1; continue
        if ch=='}': depth=max(0,depth-1); i+=1; continue
        if depth==1 and obj.startswith(key,i):
            before=obj[i-1] if i>0 else ''
            after=obj[i+len(key)] if i+len(key)<len(obj) else ''
            if (before and (before.isalnum() or before in '_$')) or (after and (after.isalnum() or after in '_$')):
                i+=1; continue
            j=i+len(key)
            while j<len(obj) and obj[j].isspace(): j+=1
            if j>=len(obj) or obj[j] != ':': i+=1; continue
            j+=1
            while j<len(obj) and obj[j].isspace(): j+=1
            if j<len(obj) and obj[j] in ("'",'"'):
                q=obj[j]; j+=1; start=j; esc=False
                while j<len(obj):
                    if esc: esc=False
                    elif obj[j]=='\\': esc=True
                    elif obj[j]==q: return obj[start:j]
                    j+=1
            return None
        i+=1
    return None

def normalize_route_path(raw:str)->str:
    raw=(raw or '').strip()
    if raw=='': return '/'
    if raw.startswith('/'): return raw
    if raw.startswith(':'): return '/'+raw
    if raw.startswith('*'): return '/'+raw
    return '/'+raw.lstrip('/')

def normalize_redirect(raw:str|None)->str|None:
    if not raw: return None
    if raw.startswith('/'): return raw
    return '/'+raw.lstrip('/')

def likely_api_url(url:str)->bool:
    if not url: return False
    lowered=url.lower()
    if any(lowered.endswith(ext) for ext in (
        '.svg','.png','.jpg','.jpeg','.gif','.webp','.css','.js','.mjs','.map',
        '.woff','.woff2','.ttf','.ico','.html','.md','.mdx'
    )):
        return False
    if url.startswith('/'): return True
    if url.startswith('http://') or url.startswith('https://'):
        if any(x in lowered for x in (
            'w3.org','mozilla.org','github.com','npmjs.com','vitejs.dev',
            'vuejs.org','react.dev','nextjs.org'
        )): return False
        if any(x in lowered for x in ('xmlns','schema','documentation')): return False
        return True
    return False

def add_api(apis:list,signals:list,file:str,endpoint:str,method:str,kind:str,confidence:float):
    signals.append({
        'file':file,'kind':kind,'resolved':True,'endpoint':endpoint,
        'method':method,'confidence':confidence
    })
    if likely_api_url(endpoint):
        apis.append({
            'file':file,'endpoint':endpoint,'method':method,
            'extraction':{'method':kind,'level':'STATIC_INFERRED','confidence':confidence}
        })

def add_dynamic_signal(signals:list,file:str,callee:str,expression:str,kind:str):
    expression=(expression or '').strip()
    signals.append({
        'file':file,'kind':kind,'callee':callee,'expression':expression,
        'resolved':False,'confidence':0.55
    })

def next_routes(root:Path):
    routes=[]
    for base_name in ('app','pages','src/app','src/pages'):
        base=root/base_name
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in {'.js','.jsx','.ts','.tsx'}: continue
            rel=p.relative_to(base)
            if 'app' in base_name and p.stem!='page': continue
            if 'pages' in base_name and p.stem.startswith('_'): continue
            parts=list(rel.parts)
            if p.stem in {'page','index'}: parts=parts[:-1]
            else: parts[-1]=p.stem
            clean=[]
            for part in parts:
                if part.startswith('(') and part.endswith(')'): continue
                if part.startswith('@'): continue
                if part.startswith('[[...') and part.endswith(']]'):
                    clean.append('*'+part[5:-2]); continue
                if part.startswith('[...') and part.endswith(']'):
                    clean.append('*'+part[4:-1]); continue
                if part.startswith('[') and part.endswith(']'):
                    clean.append(':'+part[1:-1]); continue
                clean.append(part)
            path='/'+'/'.join(clean)
            path=path.replace('//','/')
            routes.append({
                'path':path or '/','raw_path':str(rel),
                'file':str(p.relative_to(root)).replace('\\','/'),
                'extraction':{'method':'filesystem-routing','level':'STATIC_CONFIRMED','confidence':0.98}
            })
    return routes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--legacy',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--adapter',default='generic-static')
    a=ap.parse_args()

    root=Path(a.legacy).resolve()
    out=Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)

    pkg={}
    if (root/'package.json').exists():
        try: pkg=json.loads((root/'package.json').read_text(encoding='utf-8'))
        except Exception: pkg={}
    deps={**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})}

    framework='unknown'; version=None
    if 'next' in deps: framework='nextjs'; version=deps.get('next')
    elif 'vue' in deps: framework='vue'; version=deps.get('vue')
    elif 'react' in deps: framework='react'; version=deps.get('react')

    imports=[]; apis=[]; api_signals=[]; files=[]; routes=[]; state_uses=[]

    for p in walk(root):
        rel=str(p.relative_to(root)).replace('\\','/')
        text=p.read_text(encoding='utf-8',errors='replace')
        lines=text.count('\n')+1
        files.append({'file':rel,'lines':lines,'extension':p.suffix.lower(),'classification':'SOURCE'})

        for m in IMPORT.finditer(text):
            imports.append({
                'source':rel,'specifier':m.group(1),
                'extraction':{'method':'static-pattern','level':'STATIC_INFERRED','confidence':0.75}
            })

        # HTTP/API discovery: literal calls + custom wrappers + unresolved dynamic signals.
        for m in FETCH_LITERAL.finditer(text):
            add_api(apis,api_signals,rel,m.group(1),'GET_OR_DYNAMIC','fetch-literal',0.85)
        for m in AXIOS_LITERAL.finditer(text):
            add_api(apis,api_signals,rel,m.group(2),m.group(1).upper(),'axios-literal',0.92)
        for m in GENERIC_LITERAL_CALL.finditer(text):
            add_api(apis,api_signals,rel,m.group(2),'UNKNOWN',f'wrapper:{m.group(1)}',0.82)

        # Dynamic fetch/call signals are intentionally recorded even when endpoint cannot be resolved.
        literal_fetch_spans={m.span() for m in FETCH_LITERAL.finditer(text)}
        for m in FETCH_EXPRESSION.finditer(text):
            if any(a <= m.start() < b for a,b in literal_fetch_spans): continue
            expr=m.group(1)
            if expr and not expr.lstrip().startswith(("'",'"')):
                add_dynamic_signal(api_signals,rel,'fetch',expr,'fetch-dynamic')
        literal_wrapper_starts={m.start() for m in GENERIC_LITERAL_CALL.finditer(text)}
        for m in GENERIC_DYNAMIC_CALL.finditer(text):
            if m.start() in literal_wrapper_starts: continue
            expr=m.group(2)
            if expr and not expr.lstrip().startswith(("'",'"')):
                add_dynamic_signal(api_signals,rel,m.group(1),expr,'wrapper-dynamic')
        for m in API_BASE_CONST.finditer(text):
            value=m.group(2)
            if likely_api_url(value):
                api_signals.append({
                    'file':rel,'kind':'api-base-constant','symbol':m.group(1),
                    'endpoint':value,'resolved':False,'confidence':0.5
                })

        route_context=bool(ROUTER_HINT.search(text)) or any(
            x in rel.lower() for x in ('router','routes','routing','route-def','route_manifest','manifest','navigation')
        )
        if framework in {'vue','react'} and route_context:
            for m in OBJECT_PATH.finditer(text):
                raw_path=m.group(1)
                obj=object_slice(text,m.start())
                # v1.5: relative child paths are legal only inside a route-shaped object.
                if not is_route_object(obj): continue
                route_name=top_level_string_value(obj,'name')
                redirect_value=top_level_string_value(obj,'redirect')
                routes.append({
                    'path':normalize_route_path(raw_path),
                    'raw_path':raw_path,
                    'name':route_name,
                    'redirect':normalize_redirect(redirect_value),
                    'file':rel,
                    'extraction':{
                        'method':'route-object-static',
                        'level':'STATIC_INFERRED',
                        'confidence':0.86 if raw_path and not raw_path.startswith('/') else 0.84
                    }
                })

            # Route-builder/helper calls are heuristic evidence only.
            for m in ROUTE_HELPER_CALL.finditer(text):
                helper=m.group(1); raw_path=m.group(2); redirect_target=m.group(3)
                routes.append({
                    'path':normalize_route_path(raw_path),
                    'raw_path':raw_path,
                    'name':None,
                    'redirect':normalize_redirect(redirect_target),
                    'file':rel,
                    'extraction':{
                        'method':f'route-helper:{helper}',
                        'level':'HEURISTIC',
                        'confidence':0.62 if redirect_target else 0.52
                    }
                })
            if framework=='react':
                for m in JSX_ROUTE.finditer(text):
                    routes.append({
                        'path':normalize_route_path(m.group(1)),'raw_path':m.group(1),
                        'name':None,'redirect':None,'file':rel,
                        'extraction':{'method':'react-route-jsx','level':'STATIC_CONFIRMED','confidence':0.95}
                    })

        for state_pkg in ('pinia','vuex','redux','@reduxjs/toolkit','zustand','mobx'):
            if state_pkg in text:
                state_uses.append({
                    'file':rel,'library':state_pkg,
                    'extraction':{'method':'static-reference','level':'STATIC_INFERRED','confidence':0.7}
                })

    if framework=='nextjs':
        routes.extend(next_routes(root))

    # Deduplicate route redirects and APIs while retaining evidence.
    route_unique={}
    for r in routes:
        key=(r.get('path'),r.get('redirect'),r.get('file'))
        route_unique[key]=r
    routes=list(route_unique.values())

    api_unique={}
    for x in apis:
        key=(x.get('method'),x.get('endpoint'),x.get('file'))
        api_unique[key]=x
    apis=list(api_unique.values())

    router=next((k for k in ['vue-router','react-router-dom','react-router'] if k in deps),None)
    if framework=='nextjs': router='next-file-router'
    state=next((k for k in ['vuex','pinia','redux','@reduxjs/toolkit','zustand','mobx'] if k in deps),None)
    build=next((k for k in ['vite','webpack','@vue/cli-service','next'] if k in deps),None)

    project={
        'root':str(root),'name':pkg.get('name',root.name),
        'framework':{'name':framework,'version':version},
        'router':router,'state':state,'build':build,'scripts':pkg.get('scripts',{})
    }

    unknowns=[]
    if router and not routes:
        unknowns.append(f'Router {router} detected but no static routes recovered.')
    unresolved=[x for x in api_signals if not x.get('resolved')]
    if api_signals and not apis:
        unknowns.append(
            f'{len(api_signals)} HTTP/API call signal(s) detected but no concrete endpoint was recovered.'
        )
    elif unresolved:
        unknowns.append(
            f'{len(unresolved)} HTTP/API call signal(s) remain unresolved after static analysis.'
        )

    coverage={
        'files':len(files),'imports':len(imports),'apis':len(apis),'routes':len(routes),
        'state_uses':len(state_uses),
        'api_signals':len(api_signals),
        'api_unresolved':len(unresolved),
    }
    manifest={
        'schema_version':'1','adapter':a.adapter,'adapter_version':'1.6.0',
        'engine':'framework-aware-static',
        'parsed_files':len(files),
        'warnings':[
            'Static analysis does not prove runtime reachability; dynamic routes, remote config and feature flags may require runtime evidence.'
        ],
        'unknowns':unknowns,'coverage':coverage,
        'evidence_levels':['STATIC_CONFIRMED','STATIC_INFERRED','HEURISTIC','UNKNOWN']
    }

    outputs=[
        ('analysis-manifest.json',manifest),
        ('project.json',project),
        ('files.json',{'count':len(files),'files':files}),
        ('imports.json',{'count':len(imports),'edges':imports}),
        ('apis.json',{'count':len(apis),'apis':apis}),
        ('api-signals.json',{'count':len(api_signals),'resolved':len(api_signals)-len(unresolved),'unresolved':len(unresolved),'signals':api_signals}),
        ('routes.json',{'count':len(routes),'routes':routes}),
        ('state.json',{'count':len(state_uses),'uses':state_uses}),
        ('inventory.json',{
            'manifest':manifest,'project':project,'files':files,'imports':imports,
            'apis':apis,'api_signals':api_signals,'routes':routes,'state':state_uses
        })
    ]
    for name,data in outputs:
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    print(
        f'PASS {a.adapter}: files={len(files)} imports={len(imports)} '
        f'apis={len(apis)} api_signals={len(api_signals)} routes={len(routes)}'
    )

if __name__=='__main__':
    main()
