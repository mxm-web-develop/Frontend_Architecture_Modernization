from __future__ import annotations
from pathlib import Path
import json, yaml
from engine.state.machine import state_prerequisite_errors

def yload(p,default=None):
    if not p.exists(): return {} if default is None else default
    try: return yaml.safe_load(p.read_text(encoding='utf-8')) or ({} if default is None else default)
    except Exception: return {} if default is None else default

def jload(p,default=None):
    if not p.exists(): return {} if default is None else default
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {} if default is None else default

def md_front(lang): return f"---\nlanguage: {lang}\n---\n"

def build(repo:Path,skill_root:Path):
    registry=yload(repo/'migration/registry.yaml',{'domains':{}})
    project_status=yload(repo/'governance/project-status.yaml')
    if project_status.get('state') not in {'MODERNIZATION_ACTIVE','HANDOFF_READY'}:
        raise ValueError(f"project must be MODERNIZATION_ACTIVE before handoff build; current={project_status.get('state')}")
    candidates=yload(repo/'migration/system/capability-candidates.yaml',{'candidates':[]}).get('candidates') or []
    domain_candidates=yload(repo/'migration/system/domain-map.yaml',{'candidates':[]}).get('candidates') or []
    if (candidates or domain_candidates) and not (registry.get('domains') or {}):
        raise ValueError('discovery found capability/domain candidates but no confirmed Domain exists')
    states={}
    for name in (registry.get('domains') or {}):
        p=repo/'migration/domains'/name/'status.yaml'
        states[name]=yload(p).get('state') if p.exists() else None
    bad={k:v for k,v in states.items() if v!='MODERNIZED'}
    if bad: raise ValueError(f'all confirmed domains must be MODERNIZED before handoff: {bad}')
    for name in states:
        evidence_errors=state_prerequisite_errors(repo,name,'MODERNIZED')
        if evidence_errors: raise ValueError(f'domain {name} MODERNIZED evidence invalid: {evidence_errors}')

    fw=yload(repo/'governance/framework-strategy.yaml')
    if fw.get('status')!='CONFIRMED': raise ValueError('framework strategy must be CONFIRMED before handoff')
    project=yload(repo/'governance/project.yaml')
    lang=(project.get('language') or {}).get('human_documentation') or 'en'
    zh=str(lang).lower().startswith('zh')
    current=yload(repo/'governance/current-system.yaml')
    modules=yload(repo/'governance/modules.yaml',{'modules':{}})
    commands=yload(repo/'governance/commands.yaml',{'commands':{}})
    scope=yload(repo/'governance/scope-register.yaml',{'items':[]})
    remediation=yload(repo/'migration/system/architecture-remediation.yaml',{'items':[]})
    caps=yload(repo/'migration/system/capability-candidates.yaml',{'candidates':[]})
    apis=yload(repo/'migration/system/api-catalog.yaml',{'apis':[]})
    routes=jload(repo/'migration/system/raw-analysis/routes.json',{'routes':[]}).get('routes',[])
    unknowns=list(current.get('runtime_unknowns') or [])
    new_req=[x for x in scope.get('items',[]) if x.get('type')=='NEW_REQUIREMENT']
    deferred=[x for x in scope.get('items',[]) if x.get('status')=='DEFERRED']

    handoff=repo/'handoff'; handoff.mkdir(parents=True,exist_ok=True)
    module_rows=[{'id':k,**(v or {})} for k,v in (modules.get('modules') or {}).items()]
    (handoff/'module-index.yaml').write_text(yaml.safe_dump({'schema_version':'1','modules':module_rows},sort_keys=False,allow_unicode=True),encoding='utf-8')
    (handoff/'new-requirements.yaml').write_text(yaml.safe_dump({'schema_version':'1','items':new_req},sort_keys=False,allow_unicode=True),encoding='utf-8')
    (handoff/'deferred-work.yaml').write_text(yaml.safe_dump({'schema_version':'1','items':deferred},sort_keys=False,allow_unicode=True),encoding='utf-8')
    (handoff/'known-issues.yaml').write_text(yaml.safe_dump({'schema_version':'1','runtime_unknowns':unknowns,'open_remediation':[x for x in remediation.get('items',[]) if x.get('status')!='RESOLVED']},sort_keys=False,allow_unicode=True),encoding='utf-8')
    system_context={
      'schema_version':'1',
      'project_id':project.get('project_id'),
      'current_system':current.get('detected'),
      'framework_strategy':fw.get('selected'),
      'architecture_constitution':'governance/modernization-constitution.yaml',
      'dependency_rules':'governance/dependency-rules.yaml',
      'commands':'governance/commands.yaml',
      'modules':list((modules.get('modules') or {}).keys()),
      'domains':states,
      'route_count':len(routes),
      'api_count':len(apis.get('apis') or []),
      'capability_candidate_count':len(caps.get('candidates') or []),
      'runtime_unknowns':unknowns,
    }
    (handoff/'system-context.yaml').write_text(yaml.safe_dump(system_context,sort_keys=False,allow_unicode=True),encoding='utf-8')

    if zh:
        intro=f"""# 项目交接入口

该仓库已经完成 Frontend Architecture Modernization 生命周期，可以进入正常新需求开发。

## 项目是什么

- 项目：`{project.get('project_id')}`
- 当前识别框架：`{(current.get('detected') or {}).get('framework')}`
- 最终 Framework Strategy：`{(fw.get('selected') or {}).get('framework')}`
- 已确认 Domain：{len(states)}
- Module：{len(module_rows)}
- 已恢复 Route：{len(routes)}
- 已归一化 API：{len(apis.get('apis') or [])}
- 延期的新需求：{len(new_req)}

## 新 Agent 必须先读

1. `docs/modernization/project-overview.md`
2. `docs/modernization/architecture-modernization-plan.md`
3. `docs/modernization/progress.md`
4. 当前业务模块对应的 `docs/modernization/domains/<domain>.md`
5. 根目录 `AGENTS.md`
6. `handoff/system-context.yaml`
7. `governance/modernization-constitution.yaml`
8. `governance/dependency-rules.yaml`
9. `governance/commands.yaml`
10. `handoff/known-issues.yaml`

如果需要 Stable ID、Route/API 原始事实或 Evidence，再进入 `migration/**`。

## 开发边界

现代化 Skill 到此结束。之后新增产品需求属于正常 Product Development Workflow，不要重新执行 Legacy Reconstruction。
"""
        arch=f"""# 架构摘要

## 统一架构原则

目标仓遵循 `governance/modernization-constitution.yaml`，核心是：

- AI-Native Repository
- Capability-first 功能拆解
- Module 明确 Ownership / Public Integration Contract
- 禁止跨 Module 深层依赖
- 人读文档与机器事实双治理
- Code Health / 注释 / 大文件拆解治理
- Functional / Visual / Architecture / Traceability Evidence

## Framework

最终选定：`{(fw.get('selected') or {}).get('framework')}`。

Framework 只负责上述统一架构在当前技术栈中的实现细节，不改变总体治理目标。

## 模块

""" + ("\n".join(f"- `{x['id']}` → `{x.get('manifest')}`" for x in module_rows) or "- 暂无 Module 记录")
        dev="# 开发接手指南\n\n## Commands\n\n"+("\n".join(f"- `{k}`: `{v}`" for k,v in (commands.get('commands') or {}).items()) or "暂无命令配置")+"\n\n## 新需求开发\n\n新增需求先阅读对应 Module Manifest、Capability Ownership、依赖规则和 ADR，再进入正常需求/设计/编码/测试流程。\n"
        readme="# 架构现代化交接包\n\n这是现代化 Skill 的最终交付快照。机器事实以 `governance/**`、Domain Ledger 和 Evidence 为准；本目录用于让后续 Agent 无需聊天历史即可接手。\n"
    else:
        intro=f"""# Agent Start Here

Modernization is complete for `{project.get('project_id')}`. Continue with the normal product-development workflow.

Start with `docs/modernization/project-overview.md`, the modernization plan,
progress, and the relevant Domain guide. Use `governance/**`, `migration/**`, and
`handoff/system-context.yaml` when machine-level facts or evidence are needed.
"""
        arch="# Architecture Summary\n\nSee `governance/modernization-constitution.yaml`, dependency rules, module manifests and system context.\n"
        dev="# Development Handoff Guide\n\nUse `governance/commands.yaml` and module-level contracts. Net-new requirements now belong to normal product development.\n"
        readme="# Architecture Modernization Handoff\n\nFinal handoff snapshot for downstream development agents.\n"

    for name,body in {'README.md':readme,'agent-start-here.md':intro,'architecture-summary.md':arch,'development-guide.md':dev}.items():
        (handoff/name).write_text(md_front(lang)+body,encoding='utf-8')

    marker={'schema_version':'1','status':'READY_TO_TRANSITION','domains':states,'framework':fw.get('selected'),'new_requirements':len(new_req),'runtime_unknowns':len(unknowns)}
    (handoff/'handoff-status.yaml').write_text(yaml.safe_dump(marker,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return marker
