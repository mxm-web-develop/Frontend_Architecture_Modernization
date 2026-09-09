from pathlib import Path
import datetime, yaml


def load(path): return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
def save(path,data): path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')

def _zh(repo: Path):
    try: lang=(load(repo/'governance/project.yaml').get('language') or {}).get('human_documentation') or 'en'
    except Exception: lang='en'
    return str(lang).lower().startswith('zh')

def recommend(repo: Path):
    current=load(repo/'governance/current-system.yaml'); fw=(current.get('detected') or {}).get('framework') or 'unknown'; ver=(current.get('detected') or {}).get('framework_version'); zh=_zh(repo)
    opts=[]
    def text(cn,en): return cn if zh else en
    def add(id,framework,adapter,score,reasons,tradeoffs,recommended=False):
        opts.append({'id':id,'framework':framework,'adapter':adapter,'status':'RECOMMENDED' if recommended else 'OPTION','fit_score':score,'reasons':reasons,'tradeoffs':tradeoffs})
    low=str(fw).lower()
    if low=='vue' and str(ver or '').lstrip('^~').startswith('2'):
        add('FW-VUE3','vue3','assets/profiles/framework/vue3.yaml',0.92,[text('最小化组件语义迁移距离','Minimizes component semantic migration distance'),text('可使用现代 Vue/Vite 生态','Enables modern Vue/Vite ecosystem')],[text('仍需独立完成模块化和治理重构','Module/governance modernization is still required')],True)
        add('FW-PRESERVE-CURRENT','preserve-current','assets/profiles/framework/preserve-current.yaml',0.45,[text('可降低短期框架迁移风险','Reduces immediate framework migration risk')],[text('Vue2 生命周期风险仍然存在','Vue2 lifecycle risk remains')])
        add('FW-REACT','react','assets/profiles/framework/react.yaml',0.55,[text('适合团队战略转向 React','Fits a deliberate team move to React')],[text('跨框架重写成本更高','Higher cross-framework rewrite cost')])
        add('FW-NEXTJS','nextjs','assets/profiles/framework/nextjs.yaml',0.35,[text('当 SSR/SEO/服务端组件有明确收益时可选','Useful when SSR/SEO/server components have explicit value')],[text('纯 Dashboard SPA 未必获得足够收益','A dashboard SPA may not gain enough value')])
    elif low=='vue':
        add('FW-PRESERVE-CURRENT','preserve-current','assets/profiles/framework/preserve-current.yaml',0.88,[text('当前 Vue 可直接承载统一现代化架构','Current Vue can host the unified modernization architecture')],[text('仍需模块、代码和治理重构','Module/code/governance work is still required')],True)
        add('FW-REACT','react','assets/profiles/framework/react.yaml',0.45,[text('团队战略需要 React 时可选','Option when team strategy requires React')],[text('跨框架成本较高','Higher cross-framework cost')])
        add('FW-NEXTJS','nextjs','assets/profiles/framework/nextjs.yaml',0.4,[text('存在明确 Next 平台能力需求时评估','Evaluate when Next platform capabilities are explicitly needed')],[text('不应仅因“更现代”而迁移','Do not migrate merely because it seems newer')])
    elif low=='react':
        add('FW-PRESERVE-CURRENT','preserve-current','assets/profiles/framework/preserve-current.yaml',0.9,[text('React 可直接承载统一现代化架构','React can directly host the unified modernization architecture')],[text('仍需治理 Router/State/Module 边界','Router/state/module boundaries still require governance')],True)
        add('FW-NEXTJS','nextjs','assets/profiles/framework/nextjs.yaml',0.65,[text('产品明确需要 Next.js 平台能力时适合','Fits explicit Next.js platform needs')],[text('引入服务端和渲染边界复杂度','Adds server/rendering boundary complexity')])
    elif low=='nextjs':
        add('FW-PRESERVE-CURRENT','preserve-current','assets/profiles/framework/preserve-current.yaml',0.92,[text('当前 Next.js 可直接承载统一现代化架构','Current Next.js can host the unified modernization architecture')],[text('仍需治理模块和 Server/Client 边界','Module and server/client boundaries still require governance')],True)
        add('FW-REACT','react','assets/profiles/framework/react.yaml',0.4,[text('若希望回归纯 SPA 可评估','Consider for a deliberate return to a pure SPA')],[text('可能失去已使用的 Next 平台能力','May lose used Next platform capabilities')])
    else:
        add('FW-PRESERVE-CURRENT','preserve-current','assets/profiles/framework/preserve-current.yaml',0.6,[text('框架识别不完整时最保守','Safest when framework detection is incomplete')],[text('需人工确认当前技术栈','Current stack requires human confirmation')],True)
        add('FW-VUE3','vue3','assets/profiles/framework/vue3.yaml',0.4,[text('可作为团队选择','Available as a team choice')],[text('需要人工评估','Requires human assessment')])
        add('FW-REACT','react','assets/profiles/framework/react.yaml',0.4,[text('可作为团队选择','Available as a team choice')],[text('需要人工评估','Requires human assessment')])
        add('FW-NEXTJS','nextjs','assets/profiles/framework/nextjs.yaml',0.3,[text('仅在平台能力需求明确时选择','Choose only with explicit platform needs')],[text('需要人工评估','Requires human assessment')])
    add('FW-CUSTOM','custom','assets/profiles/framework/custom.yaml',0.2,[text('允许用户明确选择其他框架/技术栈','Allows an explicit user-selected alternative stack')],[text('必须提供项目级实现规则','Project-level implementation rules are required')])
    data={'schema_version':'1','status':'RECOMMENDED','current_framework':fw,'recommendations':opts,'selected':None,'confirmation':None}; save(repo/'governance/framework-strategy.yaml',data); return data

def select(repo: Path, option_id: str, confirmed_by: str, decision: str, custom_framework: str|None=None):
    if confirmed_by!='human': raise ValueError('framework selection requires --confirmed-by human')
    if not decision: raise ValueError('framework selection requires --decision ADR-*')
    p=repo/'governance/framework-strategy.yaml'; data=load(p); options={x.get('id'):x for x in data.get('recommendations',[])}
    if option_id not in options: raise ValueError(f'unknown framework option: {option_id}; run framework recommend/list')
    selected=dict(options[option_id]); selected['status']='SELECTED'
    if option_id=='FW-PRESERVE-CURRENT': selected['resolved_framework']=data.get('current_framework') or 'unknown'
    if option_id=='FW-CUSTOM':
        if not custom_framework: raise ValueError('FW-CUSTOM requires --framework <name>')
        selected['framework']=custom_framework
    data['status']='CONFIRMED'; data['selected']=selected; data['confirmation']={'confirmed_by':'human','decision':decision,'confirmed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}; save(p,data); return data
