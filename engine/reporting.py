from __future__ import annotations
from pathlib import Path
import json, yaml

def yload(path,default=None):
    if not path.exists(): return {} if default is None else default
    try: return yaml.safe_load(path.read_text(encoding="utf-8")) or ({} if default is None else default)
    except Exception: return {} if default is None else default

def jload(path,default=None):
    if not path.exists(): return {} if default is None else default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {} if default is None else default

def table(headers,rows):
    if not rows: return "_UNKNOWN / 暂无可靠事实。_"
    return "| "+" | ".join(headers)+" |\n| "+" | ".join(["---"]*len(headers))+" |\n"+"\n".join("| "+" | ".join(str(c).replace("\n"," ") for c in row)+" |" for row in rows)

def _source_area(path:str):
    parts=(path or '').split('/')
    if len(parts)>=2 and parts[0]=='packages':
        return f"packages/{parts[1]}"
    if len(parts)>=2 and parts[0]=='src':
        return f"src/{parts[1]}"
    return parts[0] if parts else 'UNKNOWN'

def _target_area(source:str,specifier:str):
    if not specifier: return 'UNKNOWN'
    if specifier.startswith('.'):
        import posixpath
        base=posixpath.dirname(source)
        normalized=posixpath.normpath(posixpath.join(base,specifier))
        parts=normalized.split('/')
        if len(parts)>=2 and parts[0]=='packages': return f"packages/{parts[1]}"
        if len(parts)>=2 and parts[0]=='src': return f"src/{parts[1]}"
        return normalized
    if specifier.startswith('@'):
        parts=specifier.split('/')
        return '/'.join(parts[:2]) if len(parts)>=2 else specifier
    return specifier.split('/')[0]

def dependency_summary(imports:list):
    from collections import Counter
    counter=Counter()
    for edge in imports:
        src=_source_area(edge.get('source') or '')
        dst=_target_area(edge.get('source') or '',edge.get('specifier') or '')
        if src and dst and src!=dst:
            counter[(src,dst)] += 1
    return [[src,dst,count] for (src,dst),count in counter.most_common(50)]

def build_system(repo:Path):
    project=yload(repo/"governance/project.yaml")
    lang=(project.get("language") or {}).get("human_documentation") or "en"
    zh=str(lang).lower().startswith("zh")
    current=yload(repo/"governance/current-system.yaml")
    assess=yload(repo/"governance/architecture-assessment.yaml")
    fw=yload(repo/"governance/framework-strategy.yaml")
    legacy=yload(repo/"migration/system/legacy-system-map.yaml")
    domains=yload(repo/"migration/system/domain-map.yaml")
    apis=yload(repo/"migration/system/api-catalog.yaml")
    api_discovery=apis.get("discovery") or {}
    rem=yload(repo/"migration/system/architecture-remediation.yaml")
    caps=yload(repo/"migration/system/capability-candidates.yaml")
    commands=yload(repo/"governance/commands.yaml")
    raw=repo/"migration/system/raw-analysis"
    routes=jload(raw/"routes.json",{"routes":[]}).get("routes",[])
    imports=jload(raw/"imports.json",{"edges":[]}).get("edges",[])
    state=jload(raw/"state.json",{"uses":[]}).get("uses",[])
    health=jload(raw/"code-health.json",{})
    registry=yload(repo/"migration/registry.yaml",{"domains":{}})
    unknowns=[]
    for item in (current.get("runtime_unknowns") or []) + (legacy.get("unknowns") or []):
        if item not in unknowns:
            unknowns.append(item)

    if zh:
        title="前端架构现代化总报告"; generated="本报告由 v1.5 报告引擎从机器事实生成。空缺会显式标记为 UNKNOWN，不代表已完成。"
        sections=[
          ("1. 执行摘要",f"当前系统已识别为 **{(current.get('detected') or {}).get('framework','UNKNOWN')}**。已恢复 {len(routes)} 条路由、{len(apis.get('apis') or [])} 个 API、{len(caps.get('candidates') or [])} 个 Capability 候选。Framework Strategy 当前为 **{fw.get('status','UNKNOWN')}**。"),
          ("2. 当前系统概览",table(["字段","值"],[[k,v] for k,v in (current.get("detected") or {}).items()])),
          ("3. 技术栈",table(["项","检测结果"],[["Framework",(current.get('detected') or {}).get('framework')],["Version",(current.get('detected') or {}).get('framework_version')],["Router",(current.get('detected') or {}).get('router')],["State",(current.get('detected') or {}).get('state')],["Build",(current.get('detected') or {}).get('build')],["Package Manager",(current.get('detected') or {}).get('package_manager')]])),
          ("4. Legacy 模块 / Domain 候选",
             "下面只有 Route / Workspace Package 支撑的候选可以进入 `domain create`。"
             "`src/config|data|lib|types|requests` 等只作为 Structural Hint，不允许直接确认成 Domain。\n\n"
             + table(["候选","名称","类型","可确认","Route Evidence","Package Evidence"],
                [[x.get('id'),x.get('name'),x.get('candidate_type'),x.get('eligible_for_confirmation'),
                  ", ".join((x.get('evidence') or {}).get('routes') or []),
                  ", ".join((x.get('evidence') or {}).get('packages') or [])]
                 for x in (legacy.get('modules') or [])])
             + ("\n\n### Structural Hints（不可直接确认）\n\n"
                + table(["Hint","名称","Source Folders"],
                    [[x.get('id'),x.get('name'),", ".join((x.get('evidence') or {}).get('source_folders') or [])]
                     for x in (legacy.get('structural_hints') or [])])
                if legacy.get('structural_hints') else "")),
          ("5. Capability 候选",table(["候选","推断意图","状态","置信度"],[[x.get('id'),x.get('inferred_intent'),x.get('status'),x.get('confidence')] for x in caps.get('candidates') or []])),
          ("6. 路由分析",table(["Path","Name","Source","Confidence"],[[x.get('path'),x.get('name'),x.get('file'),(x.get('extraction') or {}).get('level')] for x in routes[:200]])),
          ("7. API 与数据流",
             (f"Discovery Status: **{api_discovery.get('status','UNKNOWN')}**；"
              f"Signals={api_discovery.get('signals',0)}，"
              f"Resolved={api_discovery.get('resolved_signals',0)}，"
              f"Unresolved={api_discovery.get('unresolved_signals',0)}。\n\n")
             + table(["ID","Method","Endpoint","Sources"],[[x.get('id'),x.get('method'),x.get('endpoint'),", ".join(x.get('sources') or [])] for x in (apis.get('apis') or [])])
             + ("\n\n### 未解析请求信号\n\n"
                + table(["File","Callee","Expression","Kind"],[[x.get('file'),x.get('callee'),x.get('expression'),x.get('kind')] for x in apis.get('unknowns') or []])
                if apis.get('unknowns') else "")),
          ("8. State 分析",table(["Library","Source"],[[x.get('library'),x.get('file')] for x in state])),
          ("9. 依赖与耦合",
             f"已恢复 **{len(imports)}** 条静态 Import Edge。下面列出跨区域 / 跨包的主要依赖摘要；"
             "这只是静态结构证据，不等于最终 Domain Boundary。\n\n"
             + table(["Source Area","Target Area / Package","Import Count"],dependency_summary(imports))
             + "\n\n详细事实见 `migration/system/raw-analysis/imports.json`。"),
          ("10. 前端 / BFF / Backend 职责", "当前只有静态前端证据；具体职责结论必须在各 Domain 的 `responsibility-review.yaml` 中完成。"),
          ("11. 架构评估",table(["维度","Score","Finding 数"],[[k,(v or {}).get('score'),len((v or {}).get('findings') or [])] for k,v in (assess.get('dimensions') or {}).items()])),
          ("12. Code Health",table(["指标","值"],[[k,v] for k,v in (health.get('summary') or {}).items()])),
          ("13. 统一目标架构","目标不由 Legacy 目录决定。统一遵循 `governance/modernization-constitution.yaml`：AI-Native、Capability-first、模块独立治理与集成、人机文档、依赖约束、真实 Evidence。"),
          ("14. Framework Strategy",table(["状态","Selected","推荐数量"],[[fw.get('status'),fw.get('selected'),len(fw.get('recommendations') or [])]])),
          ("15. Domain / Module 设计",table(["Domain","Name","Status File"],[[k,(v or {}).get('name'),(v or {}).get('status_file')] for k,v in (registry.get('domains') or {}).items()])),
          ("16. 现代化进度",table(["Domain","State"],[[k,yload(repo/'migration/domains'/k/'status.yaml').get('state','UNKNOWN')] for k in (registry.get('domains') or {})])),
          ("17. Parity / Evidence","Functional / Visual / Architecture / Traceability Evidence 以各 Domain `status.yaml` 与 `evidence/` 为准；未到门禁阶段不应宣称通过。"),
          ("18. 风险、UNKNOWN 与 Handoff",
             table(["类型","ID / 内容","File","Severity"],
               [["UNKNOWN",x,"",""] for x in unknowns]
               + [["Remediation",x.get('id')+" "+str(x.get('type')),x.get('file') or (x.get('evidence') or {}).get('file') or "",x.get('severity')] for x in rem.get('items') or []])),
        ]
    else:
        title="Frontend Architecture Modernization Master Report"; generated="Generated by the v1.5 reporting engine from machine facts. Missing facts are shown as UNKNOWN."
        sections=[("1. Executive Summary",f"Framework: {(current.get('detected') or {}).get('framework','UNKNOWN')}; routes={len(routes)}; APIs={len(apis.get('apis') or [])}; capability candidates={len(caps.get('candidates') or [])}.")]
        # Keep English report complete enough without duplicating all wording.
        sections += [
          ("2. Current System Overview",table(["Field","Value"],[[k,v] for k,v in (current.get("detected") or {}).items()])),
          ("3. Technology Stack",f"See section 2 and `governance/current-system.yaml`."),
          ("4. Legacy Module / Domain Candidates",
             "Only route/package-backed candidates are confirmable. Source-folder hints are structural evidence only.\n\n"
             + table(["Candidate","Name","Type","Confirmable"],
                [[x.get('id'),x.get('name'),x.get('candidate_type'),x.get('eligible_for_confirmation')] for x in (legacy.get('modules') or [])])),
          ("5. Capability Inventory",table(["Candidate","Intent","Status"],[[x.get('id'),x.get('inferred_intent'),x.get('status')] for x in caps.get('candidates') or []])),
          ("6. Route Analysis",table(["Path","Source"],[[x.get('path'),x.get('file')] for x in routes[:200]])),
          ("7. API & Data Flow",
             f"Discovery status: {api_discovery.get('status','UNKNOWN')}; signals={api_discovery.get('signals',0)}, unresolved={api_discovery.get('unresolved_signals',0)}.\n\n"
             + table(["Method","Endpoint","Sources"],[[x.get('method'),x.get('endpoint'),", ".join(x.get('sources') or [])] for x in apis.get('apis') or []])),
          ("8. State Architecture",table(["Library","Source"],[[x.get('library'),x.get('file')] for x in state])),
          ("9. Dependency & Coupling",
             f"Recovered {len(imports)} static import edges.\n\n"
             + table(["Source Area","Target Area / Package","Import Count"],dependency_summary(imports))),
          ("10. Responsibility Review","Domain-level semantic review required."),
          ("11. Architecture Assessment",table(["Dimension","Score"],[[k,(v or {}).get('score')] for k,v in (assess.get('dimensions') or {}).items()])),
          ("12. Code Health",table(["Metric","Value"],[[k,v] for k,v in (health.get('summary') or {}).items()])),
          ("13. Unified Target Architecture","See `governance/modernization-constitution.yaml`."),
          ("14. Framework Strategy",table(["Status","Selected"],[[fw.get('status'),fw.get('selected')]])),
          ("15. Domain / Module Design",table(["Domain","Name"],[[k,(v or {}).get('name')] for k,v in (registry.get('domains') or {}).items()])),
          ("16. Modernization Progress",table(["Domain","State"],[[k,yload(repo/'migration/domains'/k/'status.yaml').get('state','UNKNOWN')] for k in (registry.get('domains') or {})])),
          ("17. Parity / Evidence","See domain status/evidence artifacts."),
          ("18. Risks / Unknowns / Handoff",table(["Type","Content"],[["UNKNOWN",x] for x in unknowns])),
        ]
    body=f"---\nlanguage: {lang}\nid: MODERNIZATION-MASTER-REPORT\ntype: generated\nstatus: active\nschema_version: 1\n---\n# {title}\n\n> {generated}\n\n"
    for h,c in sections: body+=f"## {h}\n\n{c}\n\n"
    out=repo/"migration/system/migration-master-report.md"; out.write_text(body,encoding="utf-8")
    return out
