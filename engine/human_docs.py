from __future__ import annotations
from pathlib import Path
import json, re, yaml
from collections import defaultdict, Counter

STATE_ZH = {
    "DISCOVERED": "已发现，等待功能梳理",
    "CAPABILITY_MODELED": "功能范围已梳理",
    "RESPONSIBILITY_REVIEWED": "职责边界已评审",
    "TARGET_CONTRACT_DEFINED": "目标模块设计已确定",
    "REMEDIATION_PLANNED": "实施计划已确定",
    "IMPLEMENTING": "正在重构实现",
    "FUNCTIONAL_PARITY_CHECK": "正在验证功能一致性",
    "VISUAL_PARITY_CHECK": "正在验证视觉一致性",
    "ARCHITECTURE_CHECK": "正在验证架构约束",
    "TRACEABILITY_CHECK": "正在验证追踪与证据",
    "MODERNIZED": "已完成现代化重构",
    "SYNCING": "正在同步旧仓变化",
}
PROJECT_STATE_ZH = {
    "DISCOVERED": "已初始化，等待分析旧系统",
    "CURRENT_SYSTEM_MODELED": "旧系统结构已完成初步建模",
    "ARCHITECTURE_ASSESSED": "已完成架构评估",
    "FRAMEWORK_STRATEGY_CONFIRMED": "目标框架策略已确认",
    "TARGET_FOUNDATION_READY": "新仓基础架构已准备好",
    "MODERNIZATION_ACTIVE": "正在逐模块重构",
    "HANDOFF_READY": "已完成，可交接给后续开发",
}
FINDING_ZH = {
    "GOD_FILE": "单文件职责过多，需要拆分",
    "LARGE_FILE": "文件体积过大，需要按职责拆分",
    "MIXED_DATA_ACCESS_UI": "页面层混入较多数据访问逻辑",
    "AI_NATIVE_GOVERNANCE_GAP": "旧仓缺少面向 AI 长期开发所需的治理入口",
    "LEGACY_STRUCTURE_REQUIRES_CAPABILITY_REVIEW": "旧仓目录结构不能直接代表业务边界，需要按功能重新梳理",
    "IMPORT_GRAPH_REVIEW": "现有依赖关系需要重新检查边界和方向",
    "API_OWNERSHIP_REVIEW": "API 与业务模块的归属需要重新确认",
    "API_DISCOVERY_INCOMPLETE": "接口调用已被发现，但静态分析尚未恢复出可靠接口清单",
    "API_DISCOVERY_PARTIAL": "接口已经恢复一部分，但仍有动态调用需要继续确认",
    "API_DISCOVERY_NO_SIGNAL": "当前静态分析没有获得足够的接口调用证据",
    "DOCUMENTATION_GAP": "旧仓文档不足以支撑后续 Agent 无上下文接手",
    "PUBLIC_MODULE_CONTRACTS_REQUIRED": "业务模块需要明确对外暴露的集成契约",
    "FRAMEWORK_STRATEGY_REQUIRES_RECOMMENDATION": "需要基于当前系统确定目标框架实现策略",
    "REQUIRES_SEMANTIC_REVIEW": "仅靠静态分析无法判断，需要人工或 Agent 结合业务语义确认",
}
SEVERITY_ZH = {
    "critical": "最高",
    "high": "高",
    "medium": "中",
    "low": "低",
}
DISPOSITION_ZH = {
    "PRESERVE": "保持现有产品行为",
    "REPLACE": "以新实现替代旧实现，但保持目标功能",
    "REMOVE": "确认删除",
}
VISUAL_ZH = {
    "STRICT_PRESERVE": "严格保持现有视觉和交互",
    "STRUCTURE_PRESERVE": "保持页面结构和核心交互",
    "APPROVED_REDESIGN": "已批准重新设计",
    "NOT_VISUAL": "无视觉验证要求",
}

def yload(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or ({} if default is None else default)
    except Exception:
        return {} if default is None else default

def jload(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default

def dump_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

def frontmatter(lang: str, doc_type: str):
    return f"---\nlanguage: {lang}\ntype: {doc_type}\nstatus: generated\n---\n"

def humanize_slug(value: str | None):
    if not value:
        return ""
    raw=str(value)
    # Preserve meaningful product/camel-case names supplied by users or package metadata.
    if not re.search(r"[-_/.\s]", raw) and any(ch.isupper() for ch in raw[1:]):
        return raw
    words = re.split(r"[-_/.\s]+", raw)
    return " ".join(w.capitalize() for w in words if w)

def present(value, missing_zh="尚未确认", missing_en="Not confirmed", zh=True):
    if value is None or value == "" or value == [] or value == {}:
        return missing_zh if zh else missing_en
    if isinstance(value, bool):
        return ("是" if value else "否") if zh else ("Yes" if value else "No")
    if isinstance(value, dict):
        return ", ".join(f"{humanize_slug(k)}: {present(v, zh=zh)}" for k, v in value.items() if v not in (None, "", [], {})) or (missing_zh if zh else missing_en)
    if isinstance(value, list):
        vals = [present(v, zh=zh) for v in value if v not in (None, "", [], {})]
        return "、".join(vals) if zh else ", ".join(vals)
    return str(value)

def state_label(state: str | None, zh=True):
    if not state:
        return "尚未开始" if zh else "Not started"
    if zh:
        return STATE_ZH.get(state, PROJECT_STATE_ZH.get(state, humanize_slug(state)))
    return humanize_slug(state)

def finding_label(finding_type: str | None, zh=True):
    if not finding_type:
        return "需要进一步确认" if zh else "Needs further review"
    if zh:
        return FINDING_ZH.get(finding_type, humanize_slug(finding_type))
    return humanize_slug(finding_type)

def severity_label(value: str | None, zh=True):
    if not value:
        return "未分级" if zh else "Unrated"
    return SEVERITY_ZH.get(str(value).lower(), humanize_slug(value)) if zh else humanize_slug(value)

def unknown_label(value: str, zh=True):
    text=str(value or "").strip()
    if not zh:
        return text
    low=text.lower()
    if "static analysis does not prove runtime reachability" in low:
        return "静态分析无法证明所有路由和功能在运行时都真实可达；动态路由、远程配置和 Feature Flag 仍需要运行时证据。"
    if "http/api call signal" in low and "remain unresolved" in low:
        m=re.search(r"(\d+)\s+HTTP/API", text, re.I)
        count=m.group(1) if m else "部分"
        return f"仍有 {count} 个接口调用无法仅靠静态分析解析，需要在对应业务模块实施前继续确认。"
    if "router" in low and "no static routes recovered" in low:
        return "已识别路由框架，但尚未恢复出可靠的静态路由清单，需要补充自定义路由或运行时证据。"
    if "no concrete endpoint was recovered" in low:
        return "已经发现接口调用行为，但尚未恢复出可靠的接口地址，当前 API Discovery 不完整。"
    return text

def selected_framework(fw: dict, current: dict, zh=True):
    selected = fw.get("selected") or {}
    if fw.get("status") == "CONFIRMED" and selected:
        name = selected.get("resolved_framework") or selected.get("framework")
        return (
            f"已确认使用 {humanize_slug(name)} 作为新仓实现框架。"
            if zh else f"{humanize_slug(name)} is confirmed for the target repository."
        )
    recs = fw.get("recommendations") or []
    recommended = next((x for x in recs if x.get("status") == "RECOMMENDED"), None)
    if recommended:
        name = recommended.get("resolved_framework") or recommended.get("framework")
        if name == "preserve-current":
            name = (current.get("detected") or {}).get("framework") or "current framework"
        return (
            f"当前建议继续使用 {humanize_slug(name)}，但尚未由用户确认。"
            if zh else f"The current recommendation is {humanize_slug(name)}, pending user confirmation."
        )
    return "目标框架策略尚未形成。" if zh else "The target framework strategy has not been prepared yet."

def candidate_tokens(name: str):
    generic = {"model", "platform", "app", "application", "module", "package", "ui", "frontend"}
    return {x for x in re.split(r"[-_/.\s]+", (name or "").lower()) if x and x not in generic}

def candidate_area_key(item: dict):
    name = str(item.get("name") or "")
    tokens = candidate_tokens(name)
    route_evidence = (item.get("evidence") or {}).get("routes") or []
    if route_evidence:
        first = route_evidence[0].strip("/").split("/")[0] if route_evidence[0] else ""
        if first:
            return first.lower()
    if tokens:
        return sorted(tokens, key=len, reverse=True)[0]
    return name.lower() or "unclassified"

def area_label(key: str, items: list[dict], overrides: dict, zh=True):
    if key in overrides:
        return str(overrides[key])
    route_names = []
    for item in items:
        for route in (item.get("evidence") or {}).get("routes") or []:
            seg = route.strip("/").split("/")[0] if route else ""
            if seg:
                route_names.append(seg)
    if route_names:
        return humanize_slug(Counter(route_names).most_common(1)[0][0])
    names = [str(x.get("name") or "") for x in items if x.get("name")]
    if names:
        # Prefer a workspace package name over generic structural names.
        names.sort(key=lambda x: (0 if "-" in x else 1, len(x)))
        return humanize_slug(names[0])
    return "待确认业务区域" if zh else "Unconfirmed business area"

def source_matches_area(file_path: str, key: str, items: list[dict]):
    low = (file_path or "").lower()
    if key and key in low:
        return True
    for item in items:
        name = str(item.get("name") or "").lower()
        if name and name in low:
            return True
        for package in (item.get("evidence") or {}).get("packages") or []:
            if package.lower() in low:
                return True
    return False

def synthesize(repo: Path):
    project = yload(repo/"governance/project.yaml")
    config = yload(repo/"governance/human-documentation.yaml")
    current = yload(repo/"governance/current-system.yaml")
    fw = yload(repo/"governance/framework-strategy.yaml")
    assessment = yload(repo/"governance/architecture-assessment.yaml")
    domain_map = yload(repo/"migration/system/domain-map.yaml", {"candidates": [], "structural_hints": []})
    caps = yload(repo/"migration/system/capability-candidates.yaml", {"candidates": []})
    rem = yload(repo/"migration/system/architecture-remediation.yaml", {"items": []})
    apis = yload(repo/"migration/system/api-catalog.yaml", {"apis": []})
    registry = yload(repo/"migration/registry.yaml", {"domains": {}})
    project_status = yload(repo/"governance/project-status.yaml")
    raw = repo/"migration/system/raw-analysis"
    raw_project = jload(raw/"project.json", {})
    routes = jload(raw/"routes.json", {"routes": []}).get("routes", [])
    imports = jload(raw/"imports.json", {"edges": []}).get("edges", [])
    health = jload(raw/"code-health.json", {})
    lang = (project.get("language") or {}).get("human_documentation") or "en"
    zh = str(lang).lower().startswith("zh")

    label_overrides = config.get("business_area_labels") or {}
    candidates = domain_map.get("candidates") or []
    grouped = defaultdict(list)
    for item in candidates:
        grouped[candidate_area_key(item)].append(item)

    # Merge obvious route/package duplicates: hall + model-hall, news + platform-news, etc.
    keys = list(grouped.keys())
    for i, key in enumerate(keys):
        if key not in grouped:
            continue
        for other in keys[i+1:]:
            if other not in grouped or key == other:
                continue
            key_tokens = {key} | candidate_tokens(key)
            other_names = " ".join(str(x.get("name") or "") for x in grouped[other]).lower()
            key_names = " ".join(str(x.get("name") or "") for x in grouped[key]).lower()
            if key in other_names or other in key_names or (key_tokens & candidate_tokens(other)):
                grouped[key].extend(grouped.pop(other))

    capability_rows = caps.get("candidates") or []
    remediation = rem.get("items") or []
    areas = []
    for key, items in grouped.items():
        route_set = sorted({
            r for item in items for r in ((item.get("evidence") or {}).get("routes") or [])
        })
        package_set = sorted({
            p for item in items for p in ((item.get("evidence") or {}).get("packages") or [])
        })
        label = area_label(key, items, label_overrides, zh)
        candidate_types = {x.get("candidate_type") for x in items}
        platform_like = not route_set and (
            key in {"shared", "config", "common", "platform"} or
            any("shared" in str(x.get("name") or "").lower() for x in items)
        )
        area_type = "PLATFORM_SUPPORT" if platform_like else "BUSINESS_AREA"

        area_caps = []
        for cap in capability_rows:
            ev = cap.get("evidence") or {}
            cap_routes = ev.get("routes") or []
            cap_apis = ev.get("apis") or []
            match = any((r.strip("/").split("/")[0].lower() == key) for r in cap_routes if r)
            if not match:
                match = any(key and key.lower() in str(api).lower() for api in cap_apis)
            if match:
                area_caps.append({
                    "name": present(cap.get("inferred_intent"), "待进一步确认的功能", "Function requiring further review", zh),
                    "source": "route" if cap_routes else "api",
                    "evidence_ids": [cap.get("id")] if cap.get("id") else [],
                })

        area_issues = []
        for item in remediation:
            file_path = item.get("file") or (item.get("evidence") or {}).get("file") or ""
            if file_path and source_matches_area(file_path, key, items):
                area_issues.append({
                    "summary": finding_label(item.get("type"), zh),
                    "severity": severity_label(item.get("severity"), zh),
                    "file": file_path,
                    "evidence_ids": [item.get("id")] if item.get("id") else [],
                })

        if zh:
            if route_set and package_set:
                summary = f"旧系统中与 {label} 相关的页面入口和工作区代码包同时存在，说明该业务已经有一定拆分基础，但最终边界仍需按真实功能重新确认。"
            elif route_set:
                summary = f"旧系统已发现与 {label} 相关的页面和导航入口，实施前仍需要结合对应旧代码、接口和交互补齐完整功能范围。"
            elif package_set:
                summary = f"旧系统存在与 {label} 相关的独立代码包，但是否应该作为业务模块，需要结合它承担的产品能力再确认。"
            else:
                summary = f"当前仅获得 {label} 的局部结构证据，需要继续补充业务语义。"
        else:
            if route_set and package_set:
                summary = f"{label} appears in both navigation and workspace packages. This is useful boundary evidence, but final ownership still requires capability review."
            elif route_set:
                summary = f"Navigation evidence exists for {label}; implementation should still re-check related legacy code, APIs and runtime behavior."
            elif package_set:
                summary = f"A workspace package exists for {label}; whether it is a business domain still requires capability review."
            else:
                summary = f"Only partial structural evidence exists for {label}."

        areas.append({
            "key": key,
            "label": label,
            "area_type": area_type,
            "summary": summary,
            "routes": route_set,
            "packages": package_set,
            "capabilities": area_caps,
            "issues": area_issues,
            "evidence_ids": [x.get("id") for x in items if x.get("id")],
        })

    # Architecture concerns as natural-language statements.
    concerns = []
    for dimension, detail in (assessment.get("dimensions") or {}).items():
        for finding in (detail or {}).get("findings") or []:
            evidence = finding.get("evidence") or {}
            file_path = finding.get("file") or evidence.get("file")
            concerns.append({
                "topic": finding_label(finding.get("type"), zh),
                "severity": severity_label(finding.get("severity"), zh),
                "detail": (
                    f"主要证据位于 `{file_path}`。" if zh and file_path
                    else f"Primary evidence: `{file_path}`." if file_path
                    else "当前结论来自静态分析，需要在实施时继续核对。" if zh
                    else "This conclusion comes from static analysis and should be re-checked during implementation."
                ),
                "dimension": humanize_slug(dimension),
            })

    # Prioritization: business areas with severe code issues first, then route coverage, then platform support.
    severity_weight = {"最高": 100, "高": 60, "中": 30, "低": 10, "Critical": 100, "High": 60, "Medium": 30, "Low": 10}
    for area in areas:
        area["priority_score"] = sum(severity_weight.get(x.get("severity"), 15) for x in area["issues"]) + len(area["routes"]) * 4 + len(area["capabilities"]) * 2
        if area["area_type"] == "PLATFORM_SUPPORT":
            area["priority_score"] -= 20
    requested_order=[str(x).lower() for x in (config.get("migration_order") or [])]
    def order_key(area):
        candidates=[area.get("key","").lower(),area.get("label","").lower()]
        for idx,wanted in enumerate(requested_order):
            if wanted in candidates:
                return (0,idx,0,area["label"].lower())
        return (1,999,-area["priority_score"],area["label"].lower())
    areas.sort(key=order_key)

    confirmed_domains = []
    for domain, meta in (registry.get("domains") or {}).items():
        status = yload(repo/"migration/domains"/domain/"status.yaml")
        cap_map = yload(repo/"migration/domains"/domain/"capability-map.yaml", {"capabilities": []})
        confirmed_domains.append({
            "id": domain,
            "name": (meta or {}).get("name") or humanize_slug(domain),
            "state": status.get("state"),
            "state_label": state_label(status.get("state"), zh),
            "capability_count": len(cap_map.get("capabilities") or []),
        })

    detected = current.get("detected") or {}
    api_disc = apis.get("discovery") or {}
    unknowns = []
    for item in current.get("runtime_unknowns") or []:
        if item:
            shown=unknown_label(str(item), zh)
            if shown not in unknowns:
                unknowns.append(shown)

    project_name = (
        config.get("project_name")
        or raw_project.get("name")
        or project.get("project_id")
        or repo.name
    )
    project_summary_override = config.get("project_summary")
    if project_summary_override:
        project_summary = str(project_summary_override)
    elif zh:
        project_summary = (
            f"{humanize_slug(project_name)} 是本次需要从旧仓库重构到新仓库的前端系统。"
            f"当前已识别 {len(routes)} 个路由入口、{len(apis.get('apis') or [])} 个可解析接口，"
            f"并形成 {len(areas)} 个需要继续语义确认的业务/平台区域。"
        )
    else:
        project_summary = (
            f"{humanize_slug(project_name)} is the frontend system being reconstructed into the new repository. "
            f"Discovery currently contains {len(routes)} routes, {len(apis.get('apis') or [])} resolved APIs, "
            f"and {len(areas)} business/platform areas requiring semantic review."
        )

    synthesis = {
        "schema_version": "1",
        "language": lang,
        "project": {
            "name": humanize_slug(project_name),
            "summary": project_summary,
            "project_state": project_status.get("state"),
            "project_state_label": state_label(project_status.get("state"), zh),
        },
        "current_system": {
            "framework": detected.get("framework"),
            "framework_version": detected.get("framework_version"),
            "router": detected.get("router"),
            "state_management": detected.get("state"),
            "build": detected.get("build"),
            "package_manager": detected.get("package_manager"),
        },
        "framework_strategy": {
            "status": fw.get("status"),
            "human_summary": selected_framework(fw, current, zh),
        },
        "discovery": {
            "routes": len(routes),
            "resolved_apis": len(apis.get("apis") or []),
            "api_status": api_disc.get("status"),
            "unresolved_api_signals": api_disc.get("unresolved_signals") or 0,
            "imports": len(imports),
            "code_health_score": (health.get("summary") or {}).get("score"),
        },
        "business_areas": areas,
        "architecture_concerns": concerns,
        "confirmed_domains": confirmed_domains,
        "unknowns": unknowns,
        "human_notes": config.get("notes") or [],
        "evidence": {
            "domain_candidate_ids": [x.get("id") for x in candidates if x.get("id")],
            "capability_candidate_ids": [x.get("id") for x in capability_rows if x.get("id")],
            "remediation_ids": [x.get("id") for x in remediation if x.get("id")],
        },
    }
    dump_yaml(repo/"migration/system/semantic-synthesis.yaml", synthesis)
    return synthesis

def _tech_stack_lines(syn: dict, zh: bool):
    cur = syn.get("current_system") or {}
    rows = []
    values = [
        ("前端框架" if zh else "Framework", cur.get("framework"), cur.get("framework_version")),
        ("路由" if zh else "Router", cur.get("router"), None),
        ("状态管理" if zh else "State management", cur.get("state_management"), None),
        ("构建工具" if zh else "Build tool", cur.get("build"), None),
        ("包管理" if zh else "Package manager", cur.get("package_manager"), None),
    ]
    for label, value, version in values:
        if value:
            shown = humanize_slug(value)
            if version:
                shown += f" {version}"
        else:
            shown = "未发现明确方案" if zh else "No explicit solution detected"
        rows.append(f"- **{label}**：{shown}" if zh else f"- **{label}**: {shown}")
    return "\n".join(rows)

def _concern_block(concerns: list, zh: bool, limit=8):
    if not concerns:
        return "当前没有足够证据形成明确架构问题结论。" if zh else "There is not enough evidence yet to state specific architecture concerns."
    out = []
    for item in concerns[:limit]:
        if zh:
            out.append(f"- **{item['topic']}**（优先级：{item['severity']}）：{item['detail']}")
        else:
            out.append(f"- **{item['topic']}** ({item['severity']}): {item['detail']}")
    return "\n".join(out)

def _area_block(area: dict, zh: bool, include_evidence=False):
    label = area["label"]
    lines = [f"### {label}", "", area["summary"], ""]
    caps = area.get("capabilities") or []
    if zh:
        lines.append("**当前识别到的功能：**")
        if caps:
            for cap in caps[:12]:
                lines.append(f"- {cap['name']}")
        else:
            lines.append("- 目前只有结构证据，功能清单还需要在实施前结合 Legacy 代码补齐。")
        if area.get("issues"):
            lines += ["", "**需要优先处理的代码问题：**"]
            for issue in area["issues"][:6]:
                suffix = f"（`{issue['file']}`）" if issue.get("file") else ""
                lines.append(f"- {issue['summary']}，优先级 {issue['severity']}{suffix}")
        if include_evidence:
            lines += ["", "**技术证据：**"]
            if area.get("routes"):
                lines.append("- 相关路由：" + "、".join(f"`{x}`" for x in area["routes"]))
            if area.get("packages"):
                lines.append("- 相关代码包：" + "、".join(f"`{x}`" for x in area["packages"]))
    else:
        lines.append("**Currently identified capabilities:**")
        if caps:
            for cap in caps[:12]:
                lines.append(f"- {cap['name']}")
        else:
            lines.append("- Only structural evidence exists so far; re-check the related Legacy code before implementation.")
        if area.get("issues"):
            lines += ["", "**Priority code concerns:**"]
            for issue in area["issues"][:6]:
                suffix = f" (`{issue['file']}`)" if issue.get("file") else ""
                lines.append(f"- {issue['summary']} — {issue['severity']}{suffix}")
        if include_evidence:
            lines += ["", "**Technical evidence:**"]
            if area.get("routes"):
                lines.append("- Routes: " + ", ".join(f"`{x}`" for x in area["routes"]))
            if area.get("packages"):
                lines.append("- Packages: " + ", ".join(f"`{x}`" for x in area["packages"]))
    return "\n".join(lines)

def build_project_overview(repo: Path, synthesis: dict | None = None):
    syn = synthesis or synthesize(repo)
    lang = syn.get("language") or "en"
    zh = str(lang).lower().startswith("zh")
    out_dir = repo/"docs/modernization"
    out_dir.mkdir(parents=True, exist_ok=True)

    p = syn["project"]
    discovery = syn.get("discovery") or {}
    business = [x for x in syn.get("business_areas") or [] if x.get("area_type") == "BUSINESS_AREA"]
    support = [x for x in syn.get("business_areas") or [] if x.get("area_type") == "PLATFORM_SUPPORT"]

    if zh:
        body = frontmatter(lang, "modernization-overview") + f"""# {p['name']} 架构现代化项目总览

## 这个项目是什么

{p['summary']}

本次工作的目标不是给旧系统增加新功能，而是在新仓库中完整复现已有产品行为，同时把代码重新组织成适合长期维护、模块独立集成和 AI 持续开发的工程结构。

## 当前技术情况

{_tech_stack_lines(syn, True)}

当前项目进度：**{p['project_state_label']}**。

{syn.get('framework_strategy',{}).get('human_summary')}

## 我们已经理解到的主要业务区域

"""
        if business:
            for area in business:
                body += _area_block(area, True, include_evidence=False) + "\n\n"
        else:
            body += "当前还没有足够证据形成可靠的业务区域划分，需要继续分析旧仓库。\n\n"

        if support:
            body += "## 平台与公共支撑代码\n\n"
            body += "下面这些区域更像公共能力或平台支撑，不应该因为存在独立目录或 Package 就直接当成业务 Domain：\n\n"
            for area in support:
                body += f"- **{area['label']}**：{area['summary']}\n"
            body += "\n"

        body += f"""## 当前最需要解决的架构问题

{_concern_block(syn.get('architecture_concerns') or [], True)}

## Discovery 当前还有哪些不确定性

"""
        unknowns = syn.get("unknowns") or []
        if unknowns:
            for item in unknowns:
                body += f"- {item}\n"
        else:
            body += "- 当前没有登记新的运行时未知项；但每个业务模块真正实施前仍需要回看对应 Legacy 代码和实际产品行为。\n"
        notes=syn.get("human_notes") or []
        if notes:
            body += "## 人工补充说明\n\n"
            for note in notes:
                body += f"- {note}\n"
            body += "\n"

        body += """
## 接下来应该怎么读

- 想看整体怎么迁：阅读 `architecture-modernization-plan.md`
- 想看现在做到哪里：阅读 `progress.md`
- 想看某个已确认业务模块：阅读 `domains/`
- 想看 Route、API、Import、Stable ID 和完整静态证据：阅读 `technical-analysis.md` 或 `migration/system/machine-analysis-report.md`

人读文档只负责解释“这个系统是什么、为什么这样改、准备怎么做”。Stable ID、Enum、置信度和原始扫描结果继续保存在 Machine Truth 中。
"""
    else:
        body = frontmatter(lang, "modernization-overview") + f"""# {p['name']} Modernization Overview

## What this project is

{p['summary']}

The goal is not to add product features. The target repository reproduces existing product behavior while reorganizing the code for long-term maintenance, modular integration, and AI-assisted development.

## Current technology

{_tech_stack_lines(syn, False)}

Current project status: **{p['project_state_label']}**.

{syn.get('framework_strategy',{}).get('human_summary')}

## Main business areas understood so far

"""
        if business:
            for area in business:
                body += _area_block(area, False, include_evidence=False) + "\n\n"
        else:
            body += "There is not enough evidence yet to define reliable business areas.\n\n"
        body += f"""## Main architecture concerns

{_concern_block(syn.get('architecture_concerns') or [], False)}

## What to read next

- `architecture-modernization-plan.md` for the implementation plan
- `progress.md` for current progress
- `domains/` for confirmed business-domain documentation
- `technical-analysis.md` for machine-level evidence and references
"""
    out = out_dir/"project-overview.md"
    out.write_text(body, encoding="utf-8")
    return out

def build_modernization_plan(repo: Path, synthesis: dict | None = None):
    syn = synthesis or synthesize(repo)
    lang = syn.get("language") or "en"
    zh = str(lang).lower().startswith("zh")
    out_dir = repo/"docs/modernization"
    out_dir.mkdir(parents=True, exist_ok=True)
    areas = syn.get("business_areas") or []
    business = [x for x in areas if x.get("area_type") == "BUSINESS_AREA"]
    support = [x for x in areas if x.get("area_type") == "PLATFORM_SUPPORT"]

    if zh:
        body = frontmatter(lang, "modernization-plan") + """# 架构现代化实施计划

## 总体目标

在新仓库中重新实现旧系统已有能力，同时保持产品行为和已批准的用户体验。重构过程中允许更换内部组织方式、拆分大文件、调整依赖方向、重建数据访问层和补充治理能力，但不能把“架构重构”变成“顺便开发新需求”。

## 实施方式

本项目采用 **全局建图 + 局部滚动实施**：

1. 先通过 Discovery 建立旧系统的整体地图，确定技术栈、主要页面、接口、代码包、依赖和技术债。
2. 确认新仓统一架构原则和 Framework Strategy。
3. 再按业务模块逐个实施。
4. 每个模块真正开发前，重新读取该模块对应的 Legacy 页面、接口、状态和交互，补齐第一次扫描没有捕捉到的业务细节。
5. 在新仓按照统一架构重新实现，而不是逐行翻译旧代码。
6. 每完成一个模块，都必须通过功能一致性、视觉一致性、架构约束和追踪证据检查。

因此，总体架构相对稳定，但 Domain / Capability 的具体实施计划会随着 Legacy Evidence 不断细化。

## 阶段一：新仓基础能力

先确保新仓本身具备长期开发条件，包括：

- 基础构建、开发、测试和质量检查命令可运行；
- Module / Domain 有明确 Ownership 和对外集成入口；
- 数据访问、公共能力和依赖方向有统一规则；
- 人读文档和 Machine Truth 都有固定入口；
- Agent 可以只依赖仓库文件恢复上下文，不依赖聊天历史。

**完成标准：** 新仓能够独立运行和验证，后续业务模块可以按统一规则接入。

## 阶段二：按业务模块滚动重构

下面的顺序是基于当前静态证据生成的**实施初稿**。它不是一次性锁死的任务清单；每个模块开工前仍要重新核对 Legacy。

"""
        for idx, area in enumerate(business, 1):
            body += f"### {idx}. {area['label']}\n\n"
            body += area["summary"] + "\n\n"
            if area.get("issues"):
                body += "**为什么建议较早处理：**\n\n"
                for issue in area["issues"][:4]:
                    suffix = f"（`{issue['file']}`）" if issue.get("file") else ""
                    body += f"- {issue['summary']}，优先级 {issue['severity']}{suffix}\n"
                body += "\n"
            body += "**开工前需要重新核对：**\n\n"
            body += "- 对应 Legacy 页面和路由实际行为\n- 真实接口与数据变换\n- 权限、状态、异常和隐藏交互\n- 与其他模块的依赖方向\n- 现有视觉与产品行为基线\n\n"
            body += "**完成标准：**\n\n"
            body += "- 该模块已批准的旧功能全部在新仓可用\n- 新代码符合统一 Module / Dependency 规则\n- 大文件和混合职责问题得到拆解，而不是原样搬运\n- 功能与视觉 Evidence 可追踪\n- Source → Target Mapping 已更新\n\n"
        if not business:
            body += "当前还没有足够证据形成可靠的业务模块顺序。应先继续 Discovery，不要开始批量开发。\n\n"

        if support:
            body += "## 平台与公共支撑能力\n\n"
            body += "这些代码更适合在业务模块实施过程中按真实依赖逐步整理，不建议仅因为它们是独立 Package 就直接升级成业务 Domain：\n\n"
            for area in support:
                body += f"- **{area['label']}**：{area['summary']}\n"
            body += "\n"

        body += """## 每个业务模块的标准实施循环

每个 Domain 都按同一套节奏推进：

1. **局部回看 Legacy**：读取当前功能真正相关的旧页面、接口、状态、权限和交互。
2. **补齐 Capability**：把遗漏的行为补进功能账本。
3. **职责评审**：区分 UI、业务用例、数据访问和应交给 BFF / Backend 的责任。
4. **确定 Target Contract**：明确新仓模块入口、路由、数据访问、依赖和 Public API。
5. **实施重构**：在新仓重新实现。
6. **功能复现验证**：确认旧产品能力没有丢失。
7. **视觉验证**：对需要保持的页面做 Legacy / Target 对比。
8. **架构与追踪验证**：检查依赖规则、测试、Evidence、Source → Target Mapping。
9. **更新文档**：让下一个 Agent 能从仓库继续工作。

## 计划变更规则

以下内容可以随着证据补充而调整：

- 一个业务模块实际包含哪些 Capability；
- 某段旧代码应该归属哪个模块；
- Domain 之间的先后顺序；
- 某个兼容层是否临时保留。

以下内容不能因为局部迁移方便而随意改变：

- 旧产品必须完整复现；
- Legacy 仓库保持只读；
- 新需求不进入本次 Modernization Scope；
- Module Boundary、Dependency Governance、Evidence 和人机文档治理要求；
- 已经由用户确认的 Framework Strategy，除非重新形成明确决策。
"""
    else:
        body = frontmatter(lang, "modernization-plan") + """# Architecture Modernization Plan

## Goal

Rebuild the existing frontend in the new repository while preserving product behavior and approved UX. Internal architecture can change; net-new product requirements are out of scope.

## Delivery model

Use **global discovery + rolling domain implementation**. Global architecture is stable, while each Domain is re-checked against the relevant Legacy code before implementation.

## Phase 1 — Target foundation

Prepare build/test commands, module ownership, dependency rules, data-access conventions, human/machine documentation, and Agent entry points.

## Phase 2 — Rolling business-domain reconstruction

"""
        for idx, area in enumerate(business, 1):
            body += f"### {idx}. {area['label']}\n\n{area['summary']}\n\n"
            body += "Before implementation, re-check the Legacy pages, APIs, state, permissions, hidden behavior, visual baseline, and cross-domain dependencies.\n\n"
            body += "Completion requires functional parity, required visual parity, architecture compliance, evidence, and updated source-to-target mapping.\n\n"
        body += """## Standard Domain loop

1. Re-check local Legacy evidence.
2. Complete Capability modeling.
3. Review responsibility boundaries.
4. Define the Target Contract.
5. Rebuild in the new repository.
6. Verify functional parity.
7. Verify visual parity where required.
8. Verify architecture and traceability.
9. Refresh documentation.
"""
    out = out_dir/"architecture-modernization-plan.md"
    out.write_text(body, encoding="utf-8")
    return out

def build_progress(repo: Path, synthesis: dict | None = None):
    syn = synthesis or synthesize(repo)
    lang = syn.get("language") or "en"
    zh = str(lang).lower().startswith("zh")
    out_dir = repo/"docs/modernization"
    out_dir.mkdir(parents=True, exist_ok=True)
    domains = syn.get("confirmed_domains") or []
    project_state = syn.get("project", {}).get("project_state_label")

    if zh:
        body = frontmatter(lang, "modernization-progress") + f"""# 架构现代化进度

## 当前整体状态

**{project_state}**

"""
        if domains:
            body += "## 已确认业务模块\n\n"
            for d in domains:
                body += f"### {d['name']}\n\n"
                body += f"- 当前状态：**{d['state_label']}**\n"
                body += f"- 已登记功能：{d['capability_count']} 项\n"
                if d["state"] == "MODERNIZED":
                    body += "- 下一步：保持与 Legacy Delta 同步，等待全项目交接。\n"
                elif d["state"] == "DISCOVERED":
                    body += "- 下一步：结合 Legacy 代码确认完整功能范围。\n"
                else:
                    body += "- 下一步：继续完成当前阶段要求，再进入下一道验证门禁。\n"
                body += "\n"
        else:
            body += """## 已确认业务模块

当前还没有正式确认的业务 Domain。Discovery 中出现的 Route / Package 候选只是分析线索，在人工或 Agent 完成业务语义确认前，不应该当成实施任务。

## 当前下一步

1. 阅读 `project-overview.md` 理解系统现状。
2. 阅读 `architecture-modernization-plan.md` 确认总体顺序。
3. 对第一个业务区域做局部 Legacy 深挖。
4. 确认真正的 Domain 与 Capability 后再开始新仓实现。
"""
    else:
        body = frontmatter(lang, "modernization-progress") + f"# Modernization Progress\n\n## Overall status\n\n**{project_state}**\n\n"
        if domains:
            body += "## Confirmed domains\n\n"
            for d in domains:
                body += f"### {d['name']}\n\n- Status: **{d['state_label']}**\n- Approved capabilities: {d['capability_count']}\n\n"
        else:
            body += "No business Domain has been confirmed yet. Discovery candidates are evidence, not implementation tasks.\n"
    out = out_dir/"progress.md"
    out.write_text(body, encoding="utf-8")
    return out

def build_domain_doc(repo: Path, domain: str):
    project = yload(repo/"governance/project.yaml")
    lang = (project.get("language") or {}).get("human_documentation") or "en"
    zh = str(lang).lower().startswith("zh")
    registry = yload(repo/"migration/registry.yaml", {"domains": {}})
    meta = (registry.get("domains") or {}).get(domain) or {}
    droot = repo/"migration/domains"/domain
    status = yload(droot/"status.yaml")
    caps = yload(droot/"capability-map.yaml", {"capabilities": []})
    target = yload(droot/"target-contract.yaml")
    source_target = yload(droot/"source-target-map.yaml", {"mappings": []})
    responsibility = yload(droot/"responsibility-review.yaml")
    routes = yload(droot/"route-map.yaml", {"routes": []})
    config = yload(repo/"governance/human-documentation.yaml")
    name = meta.get("name") or humanize_slug(domain)
    domain_description=(config.get("domain_descriptions") or {}).get(domain)
    out_dir = repo/"docs/modernization/domains"
    out_dir.mkdir(parents=True, exist_ok=True)

    if zh:
        body = frontmatter(lang, "domain-guide") + f"""# {name}

## 业务职责

{domain_description or "这是已经正式确认进入现代化范围的业务模块。"} 当前状态：**{state_label(status.get('state'), True)}**。

如果业务职责仍不够清楚，实施前必须回到 Legacy 对应页面、接口、状态和用户操作中补齐，不允许只根据目录名开发。

## 已确认功能

"""
        cap_list = caps.get("capabilities") or []
        if cap_list:
            for cap in cap_list:
                disposition = DISPOSITION_ZH.get((cap.get("migration") or {}).get("disposition"), "保持现有产品行为")
                visual = VISUAL_ZH.get((cap.get("ui") or {}).get("visual_policy"), "按实际页面确认视觉要求")
                body += f"### {cap.get('name') or '未命名功能'}\n\n"
                body += f"- 产品处理方式：{disposition}\n"
                body += f"- 视觉要求：{visual}\n"
                strategy = (cap.get("migration") or {}).get("strategy")
                if strategy:
                    body += f"- 实施策略：{humanize_slug(strategy)}\n"
                body += "\n"
        else:
            body += "当前还没有批准的功能清单。下一步应该先从 Legacy Evidence 中恢复真实业务行为，而不是直接写 Target 代码。\n\n"

        body += "## 当前旧系统证据\n\n"
        mappings = source_target.get("mappings") or []
        legacy_sources = []
        for mapping in mappings:
            legacy_obj = mapping.get("legacy") or {}
            for key in ("sources", "files", "paths"):
                vals = legacy_obj.get(key) or []
                if isinstance(vals, str):
                    vals = [vals]
                for x in vals:
                    value = x if isinstance(x, str) else x.get("file") or x.get("path")
                    if value and value not in legacy_sources:
                        legacy_sources.append(value)
        if legacy_sources:
            body += "实施本模块时优先回看这些旧代码位置：\n\n"
            for src in legacy_sources[:40]:
                body += f"- `{src}`\n"
        else:
            body += "当前 Source → Target Mapping 还没有登记足够的 Legacy 源文件。实施前应先补齐。\n"
        body += "\n## 新仓目标设计\n\n"
        if target.get("status") in {"complete", "approved"}:
            body += "目标模块契约已经形成。实施时以 `target-contract.yaml` 为机器事实来源。\n\n"
            if target.get("routes"):
                body += "- 路由：已定义\n"
            if target.get("data_access"):
                body += "- 数据访问：已定义\n"
            if target.get("dependencies"):
                body += "- 依赖边界：已定义\n"
            if target.get("public_integration_contracts"):
                body += "- 对外集成契约：已定义\n"
        else:
            body += "目标模块契约尚未完成。需要先明确路由、数据访问、依赖边界和对外集成方式，再开始大规模实现。\n"

        body += "\n## 标准实施步骤\n\n"
        body += """1. 回看本模块对应的 Legacy 行为和边界条件。
2. 补齐遗漏 Capability。
3. 完成前端 / BFF / Backend 职责评审。
4. 确认 Target Contract。
5. 在新仓按统一架构重构实现。
6. 做功能一致性验证。
7. 对需要保持的页面做视觉一致性验证。
8. 通过架构和 Traceability Gate。
9. 更新本模块文档和 Handoff 信息。

## 技术证据

下面的信息用于 Agent 追踪，不是业务说明正文：

"""
        ids = [cap.get("id") for cap in cap_list if cap.get("id")]
        if ids:
            body += "- Capability IDs：" + "、".join(f"`{x}`" for x in ids) + "\n"
        body += f"- Domain 状态文件：`migration/domains/{domain}/status.yaml`\n"
        body += f"- Capability 账本：`migration/domains/{domain}/capability-map.yaml`\n"
        body += f"- Source → Target：`migration/domains/{domain}/source-target-map.yaml`\n"
        body += f"- Evidence：`migration/domains/{domain}/evidence/`\n"
    else:
        body = frontmatter(lang, "domain-guide") + f"""# {name}

## Responsibility

Current status: **{state_label(status.get('state'), False)}**.

## Approved capabilities

"""
        cap_list = caps.get("capabilities") or []
        if cap_list:
            for cap in cap_list:
                body += f"- {cap.get('name') or 'Unnamed capability'}\n"
        else:
            body += "No approved capability list exists yet. Re-check the relevant Legacy behavior before implementation.\n"
        body += f"\n## Technical evidence\n\n- `migration/domains/{domain}/`\n"
    out = out_dir/f"{domain}.md"
    out.write_text(body, encoding="utf-8")
    return out

def build_technical_analysis_entry(repo: Path, synthesis: dict | None = None):
    syn = synthesis or synthesize(repo)
    lang = syn.get("language") or "en"
    zh = str(lang).lower().startswith("zh")
    out_dir = repo/"docs/modernization"
    out_dir.mkdir(parents=True, exist_ok=True)
    if zh:
        body = frontmatter(lang, "technical-analysis-index") + """# 技术分析与机器证据

这个文件不是迁移计划，也不是给产品或架构负责人首先阅读的文档。

如果你需要追踪静态扫描、Stable ID、Route/API 原始事实、置信度、Remediation 编号和 Evidence，请从以下入口查看：

- `migration/system/machine-analysis-report.md`：技术分析附录
- `migration/system/semantic-synthesis.yaml`：Machine Truth 到人读文档之间的语义整理层
- `migration/system/api-catalog.yaml`：接口事实
- `migration/system/domain-map.yaml`：Domain Candidate / Structural Hint
- `migration/system/capability-candidates.yaml`：Capability 候选
- `migration/system/architecture-remediation.yaml`：架构问题账本
- `migration/system/raw-analysis/`：最原始静态扫描结果

正常规划和实施请优先阅读：

1. `project-overview.md`
2. `architecture-modernization-plan.md`
3. `progress.md`
4. `domains/<domain>.md`
"""
    else:
        body = frontmatter(lang, "technical-analysis-index") + """# Technical Analysis & Machine Evidence

This is a technical appendix, not the primary modernization plan.

Machine evidence lives under `migration/system/`. Human-facing work should start with `project-overview.md`, `architecture-modernization-plan.md`, `progress.md`, and confirmed Domain guides.
"""
    out = out_dir/"technical-analysis.md"
    out.write_text(body, encoding="utf-8")
    return out

def build_index(repo: Path, synthesis: dict | None = None):
    syn = synthesis or synthesize(repo)
    lang = syn.get("language") or "en"
    zh = str(lang).lower().startswith("zh")
    out_dir = repo/"docs/modernization"
    out_dir.mkdir(parents=True, exist_ok=True)
    if zh:
        body = frontmatter(lang, "modernization-index") + """# 架构现代化文档入口

第一次阅读请按这个顺序：

1. **`project-overview.md`**：这个旧系统是什么、当前有哪些主要业务区域、最大问题是什么。
2. **`architecture-modernization-plan.md`**：总体怎么迁、先做什么、每个模块如何滚动实施。
3. **`progress.md`**：当前已经做到哪里、下一步是什么。
4. **`domains/`**：已经确认的业务模块说明。
5. **`technical-analysis.md`**：需要追踪 Stable ID、API、Route、Import 和 Evidence 时再看。

> 人读文档不把 `None`、内部编号和状态机 Enum 当正文。机器治理信息仍完整保留在 `governance/` 和 `migration/` 中。
"""
    else:
        body = frontmatter(lang, "modernization-index") + """# Modernization Documentation

Read in this order:

1. `project-overview.md`
2. `architecture-modernization-plan.md`
3. `progress.md`
4. `domains/`
5. `technical-analysis.md` when machine-level evidence is needed.
"""
    out = out_dir/"README.md"
    out.write_text(body, encoding="utf-8")
    return out

def build_all(repo: Path):
    syn = synthesize(repo)
    outputs = [
        build_index(repo, syn),
        build_project_overview(repo, syn),
        build_modernization_plan(repo, syn),
        build_progress(repo, syn),
        build_technical_analysis_entry(repo, syn),
    ]
    registry = yload(repo/"migration/registry.yaml", {"domains": {}})
    for domain in (registry.get("domains") or {}):
        outputs.append(build_domain_doc(repo, domain))
    return outputs
