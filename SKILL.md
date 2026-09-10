---
name: frontend-architecture-modernization
description: >-
  Modernize an existing brownfield frontend into a new, AI-native, modular, governed
  repository while reproducing legacy product functionality and approved user
  experience. Use for legacy frontend archaeology, current-system modeling, capability
  recovery, architecture diagnosis, framework strategy recommendations, module/domain
  decomposition, code-health remediation, Vue/React/Next.js or other framework
  transformation, functional/visual parity, AI/human documentation governance, Git
  traceability, legacy delta synchronization, cutover, and handoff. Do not use this
  skill to implement net-new product requirements; defer those to post-modernization
  development after HANDOFF_READY.
compatibility: >-
  Agent Skills open standard. Designed for Codex and Cursor. Requires repository
  filesystem access and Git. Node.js is used by AST and visual tooling.
metadata:
  version: "2.0.0"
  domain: "frontend-architecture-modernization-governance"
  lifecycle: "discover-assess-confirm-transform-verify-handoff"

changelog:
  pending-v2.1-feedback:
    - See `migration/feedback/SKILL_V2.1_FEEDBACK.md` for the post-v2.0
      execution feedback that drove the v2.1 upgrade.
  v2.0.0:
    - Add mandatory "Multi-Dimensional Parity": per-page acceptance contract
      (filter bar / table columns / operations / network), recursive capture
      (every state, every filter, every action), field-level mirror, mock-
      fidelity gate. v1.7 alone produced passing tests with fully wrong
      output (wrong URLs, invented charts, invented series, missing columns,
      excess columns, unwired actions); v2.0 closes those gaps.
  v1.7.0:
    - Add mandatory "Network-Alignment" section: per-page network-manifest.yaml
      before any api/*.ts is written; legacy source code is no longer
      sufficient evidence of an endpoint's existence or shape.
  v1.6.0:
    - Human Planning & Documentation Layer.
---

## v1.6 Human Planning & Documentation Layer

Machine facts and human documentation are separate products.

```text
Machine Truth
→ Semantic Synthesis
→ Human Documentation
```

`governance/**` and `migration/**` remain authoritative for stable IDs, enums,
confidence, raw routes/APIs/imports, evidence, hashes and lifecycle state.

`migration/system/semantic-synthesis.yaml` is a derived semantic layer that groups
those facts into business areas, natural-language architecture concerns, human state
labels, implementation priorities and unresolved questions.

Primary human documentation lives under:

```text
docs/modernization/
├── README.md
├── project-overview.md
├── architecture-modernization-plan.md
├── progress.md
├── technical-analysis.md
└── domains/
```

### Human-document invariant

Primary human documents explain:

- what the system is;
- what major business areas exist;
- what is wrong with the current architecture;
- why the target direction is recommended;
- what to implement first;
- what must be re-checked in Legacy before each Domain starts;
- what completion means;
- current progress and next action.

Do not render raw machine values such as `None`, `null`, candidate IDs,
remediation IDs, confidence enums or lifecycle enums as primary prose.

Stable IDs are citations/evidence and may appear only in technical appendices or the
technical-evidence section of a Domain guide.

### Reporting commands

```bash
modernize report system --repo .
```

generates both human documentation and the technical machine appendix. Human readers
start with `docs/modernization/project-overview.md`.

```bash
modernize report human --repo .
modernize report machine --repo .
```

can refresh the two projections independently.

The previous 18-section report is retained as
`migration/system/machine-analysis-report.md`. The historical
`migration/system/migration-master-report.md` path is only a compatibility bridge.

### Planning model

The human plan must describe **global discovery + rolling Domain implementation**:

```text
Global Legacy Discovery
→ stable architecture/framework direction
→ choose next business Domain
→ re-read local Legacy evidence
→ refine Capability/Target Contract
→ implement in new repository
→ parity/evidence
→ refresh docs
```

Do not present the initial Discovery output as a once-for-all frozen implementation
plan.


# Frontend Architecture Modernization & Governance

This is a **brownfield transformation skill**. Its job is to reconstruct an existing
frontend product in a **new repository** with modern architecture and governance while
preserving legacy product behavior. Its final deliverable is a `HANDOFF_READY`
repository that another Agent or development Skill can use for normal feature work.

## Scope boundary

### In scope

- Legacy product archaeology and current-system modeling.
- Capability recovery and module/domain boundary discovery.
- Architecture assessment and technical-debt diagnosis.
- Framework detection, recommendation and human-confirmed framework strategy.
- Rebuilding legacy capabilities in a new repository.
- Internal architecture/code refactoring while preserving external product behavior.
- AI-native repository governance and self-describing project structure.
- Module integration contracts, dependency boundaries and code-health remediation.
- Human/machine documentation governance.
- Functional, visual, architecture and traceability evidence.
- Legacy delta synchronization during a long-running modernization.
- Cutover and final handoff package.

### Out of scope

- Net-new product features that do not exist in the legacy production truth.
- Product redesign unless explicitly approved as a redesign decision.
- Silent removal of legacy functionality.
- Treating framework migration itself as the goal.
- Normal post-modernization feature development after `HANDOFF_READY`.

When a new requirement appears during modernization, classify it as `NEW_REQUIREMENT`,
record it in the handoff backlog and do not implement it under this Skill. A feature
added to the legacy production system during modernization is `LEGACY_DELTA` and must
be reproduced because it has become part of the legacy product truth.

## Core mental model

```text
Legacy Repository
  = what product behavior must be preserved

Modernization Constitution
  = how the new repository must be engineered

Framework Adapter
  = framework-specific implementation details
```

Never copy legacy folders as the target architecture merely because they exist.

## Unified modernization constitution

The target architecture direction is framework-independent. Every modernized project
must be evaluated against these principles:

1. **AI-native** — repository self-describes architecture, commands, modules, rules,
   current status and decisions without chat history.
2. **Capability-first** — business capability is the primary reproduction unit.
3. **Module-oriented** — explicit ownership, public integration contracts, dependency
   rules and independent verification boundaries.
4. **Integration-first** — modules expose documented integration surfaces rather than
   cross-importing internals.
5. **Code-health governed** — large mixed-responsibility code is decomposed; business
   logic, data access and UI concerns are separated where justified.
6. **Human + machine documentation** — machine truth and human explanation coexist and
   remain linked.
7. **Evidence-driven** — PASS is derived from verifiable runner evidence, not manual
   status fields.
8. **Behavior-preserving** — architecture may improve while legacy functionality and
   approved UI remain reproducible unless an explicit decision says otherwise.

Canonical machine policy: `governance/modernization-constitution.yaml`.

## Framework strategy

Do not select a target framework during bootstrap.

The lifecycle is:

```text
Discover current system
  -> Recover capabilities
  -> Assess architecture gaps
  -> Recommend framework strategies
  -> Human confirms framework strategy
  -> Apply framework adapter
  -> Define target implementation
```

Detecting Vue2 may justify recommending Vue3, but the recommendation is not selection.
The user may choose Vue3, React, Next.js, another supported adapter, or preserve the
current framework. The unified architecture constitution remains the same.

## Scope classifications

Every modernization work item/capability belongs to one of:

- `LEGACY_PARITY` — reproduce existing legacy behavior.
- `LEGACY_DELTA` — reproduce behavior added to legacy during modernization.
- `ARCHITECTURE_REMEDIATION` — improve implementation architecture without adding
  product behavior.
- `GOVERNANCE_ENABLEMENT` — add AI/docs/testing/evidence/governance infrastructure.
- `NEW_REQUIREMENT` — post-modernization backlog; do not implement here.

## Modernization state machines

Project-level discovery and architecture decisions use:

```text
DISCOVERED
-> CURRENT_SYSTEM_MODELED
-> ARCHITECTURE_ASSESSED
-> FRAMEWORK_STRATEGY_CONFIRMED
-> TARGET_FOUNDATION_READY
-> MODERNIZATION_ACTIVE
-> HANDOFF_READY
```

Confirmed Domains use:

```text
DISCOVERED
-> CAPABILITY_MODELED
-> RESPONSIBILITY_REVIEWED
-> TARGET_CONTRACT_DEFINED
-> REMEDIATION_PLANNED
-> IMPLEMENTING
-> FUNCTIONAL_PARITY_CHECK
-> VISUAL_PARITY_CHECK
-> ARCHITECTURE_CHECK
-> TRACEABILITY_CHECK
-> MODERNIZED
```

`MODERNIZED <-> SYNCING` is allowed for a Domain while Legacy continues to change.
Do not manually edit state. Use `modernize project transition` for Project state and
`modernize transition <domain>` for Domain state.

## Mandatory execution contract

### On activation

```bash
python <skill>/scripts/modernize.py doctor --repo <target>
python <skill>/scripts/modernize.py status --repo <target>
```

Resume durable state. Do not restart completed discovery without a legacy-delta reason.

### Network-Alignment (mandatory, v1.7)

**You cannot reproduce a legacy page's API integration by reading legacy source
code alone.** Legacy repositories drift from production: the bundled JS shipped
to `prod-url` often contains endpoints, parameters and response shapes that no
longer exist in the legacy source tree, and vice versa. Field names that look
"obvious" from source inspection are routinely wrong.

**Before writing any `api/*.ts` file for a Domain, you MUST produce a
`migration/<domain>/network-manifest.yaml`** that records **every** HTTP request
observed in the running production page:

```yaml
# migration/<domain>/network-manifest.yaml
page: /model/lcy-model/lcy-model-list
captured_at: 2026-09-10T15:55:00+08:00
captured_url: http://<legacy-prod-host>
capture_method: browser DevTools Network panel + curl reprobe
session:
  cookie_required: true
  groupId: <project id used when capturing>
requests:
  - method: GET
    url: /base/dict/getMulti
    params: { dictTypes: "LLMModelType,DL,ML,largeModelFramework,largeModelFormat,largeModelAlgorithm" }
    response_shape: { status: "200", data: { LLMModelType: [{key, desc, children}], ... } }
    purpose: "模型类型/大模型框架/格式/算法 批量字典"
    legacy_source_ref: src/store/modules/model.js::apiGetSysCodes
  - method: POST
    url: /lcy/model/queryModelList
    params: { current, pageSize, groupId, modelTypeCategory, modelName, learnMethod, startTime, endTime }
    response_shape: { status, data: [ModelRow], total }
    purpose: "模型列表"
    legacy_source_ref: src/api/lcy/lcy-model.js::getModelList
  ...
```

**Rules:**

1. **Source-only archaeology is forbidden.** You may not write an `api/*.ts`
   function whose path / params / response shape is not backed by a request in
   `network-manifest.yaml` for that page.
2. **One manifest per user-visible page.** Multi-tab pages (`ML` / `DL` tabs)
   may share a manifest if the URL set is identical; otherwise split.
3. **Capture method must be reproducible.** Either:
   - browser DevTools Network panel screenshot (record in
     `migration/<domain>/evidence/<page>.png`), OR
   - `curl` reprobe of the exact URL+params with the captured session cookie
     (record command + response in `migration/<domain>/evidence/<page>.txt`).
4. **Re-capture on legacy delta.** If `modernize sync scan` reports the legacy
   page changed, regenerate the manifest before touching the new repo's API.
5. **Response-shape fidelity is non-negotiable.** Do not rename keys
   (`statisticName` is `statisticName`, not `name`; `modelCountVO` is
   `modelCountVO`, not `modelStatistics`). If you cannot prove the shape from
   the captured response, your function is wrong even if your mock passes.
6. **Mock data must mirror real shape and real value space.** Mock `statisticName`
   strings must be drawn from the real set observed in production
   (`待上线模型数量/运行中模型数量/已下线模型数量`), not invented
   (`已导入/在线服务/离线预估`). Mock that diverges from real shapes hides
   integration bugs.
7. **Smoke check after `api/*.ts` lands:** start `dev:real` (proxy to
   `<legacy-prod-host>`), open the page in a real browser, and inspect each
   request in the Network panel — every URL+params must match the manifest
   within documented deviations. Record deviations in
   `migration/<domain>/network-manifest-deviations.yaml`.

**Failure mode this rule exists to prevent:** the agent reads `lcy-model.js`,
sees `url: 'lcy/model/queryModelList'`, writes the same path in the new repo,
and assumes the API integration is correct — when in fact the production page
also calls `getImageSceneTree`, `getMulti`, `LLMModelType?...`, `getCodesByType`
that the source grep never surfaced, and the new page silently drops them.
This rule makes the missing requests visible before the smoke check, not after.



### Discovery-first bootstrap

For a new project:

```bash
python <skill>/scripts/modernize.py bootstrap \
  --target <new-repo> \
  --legacy <legacy-repo> \
  --human-language zh-CN
```

Bootstrap must leave framework strategy `UNDECIDED`.

### Current-system discovery

```bash
python <skill>/scripts/modernize.py analyze --repo <target>
```

The engine detects an analyzer adapter and creates raw facts plus
`governance/current-system.yaml`. AI semantic reasoning consumes those facts; it does
not replace deterministic scanning.

### Architecture assessment

```bash
python <skill>/scripts/modernize.py assess --repo <target>
```

The engine generates code-health/current-architecture facts and an assessment scaffold.
The Agent enriches business/architecture reasoning without inventing evidence.

### Framework recommendation and confirmation

```bash
python <skill>/scripts/modernize.py framework recommend --repo <target>
python <skill>/scripts/modernize.py framework list --repo <target>
```

Only after explicit human confirmation:

```bash
python <skill>/scripts/modernize.py framework select <OPTION_ID> \
  --confirmed-by human \
  --decision ADR-TARGET-001 \
  --repo <target>
```

Do not set framework strategy to confirmed from an Agent recommendation alone.

### Scope boundary

Use:

```bash
python <skill>/scripts/modernize.py scope add \
  --id REQ-001 \
  --type NEW_REQUIREMENT \
  --title "..." \
  --repo <target>
```

`NEW_REQUIREMENT` remains deferred and is surfaced in the final handoff backlog.

### Transformation

Transform capabilities according to target contracts and remediation plans. Large or
mixed-responsibility legacy files should be decomposed where it improves architecture,
but behavior and visual policy remain governed.

Comments should explain **why/constraint/compatibility/decision**, not restate obvious
code. Migration compatibility code should reference relevant Capability/ADR where
useful.

### Gates

A gate cannot become `PASS` without verifiable evidence.

```bash
modernize run-check functional <domain> --command-key test
modernize run-check functional <domain> --command-key e2e
modernize gate <domain> functional PASS --evidence <...>
```

Visual PASS must point to Visual Harness `result.json`; required Legacy/Target/Diff PNG
files and hashes are re-checked by `modernize validate`.

### Delta sync

Legacy production changes remain in scope:

```bash
modernize sync scan <domain>
modernize sync advance <domain>
```

Changed legacy files are mapped to known `CAP-*` where possible. Unresolved files stay
explicitly unresolved.

### Handoff

After `MODERNIZED`, build the handoff package:

```bash
python <skill>/scripts/modernize.py handoff build --repo <target>
python <skill>/scripts/modernize.py project transition HANDOFF_READY --repo <target>
```

Handoff must include enough repository truth for another Agent/Skill to develop new
requirements without relying on modernization chat history.

## Handoff-ready requirements

- Legacy capability coverage is complete or explicitly decisioned.
- Required gates have verifiable evidence.
- Target modules have machine-readable manifests and human-readable documentation.
- Architecture/dependency/command/language governance exists.
- Known issues, unresolved evidence and deferred modernization are explicit.
- `NEW_REQUIREMENT` items are present only in the post-modernization backlog.
- Install/dev/build/lint/typecheck/test/e2e commands are discoverable.
- `handoff/agent-start-here.md` exists and points to canonical repository truth.

## Language governance

Conversational responses follow the user's language. Governed human-readable documents
must use `governance/project.yaml -> language.human_documentation`. Machine keys,
schema fields, enum values, stable IDs, Git trailers and code identifiers remain
English. Human descriptions, reports, tables and comments use the configured human
language.

## Progressive references

Read only what the current phase needs:

- `references/SCOPE-BOUNDARY.md`
- `references/DISCOVERY.md`
- `references/ARCHITECTURE-ASSESSMENT.md`
- `references/FRAMEWORK-STRATEGY.md`
- `references/UNIFIED-MODERNIZATION-ARCHITECTURE.md`
- `references/CODE-HEALTH-GOVERNANCE.md`
- `references/HANDOFF.md`
- `references/WORKFLOW.md`
- `references/SCHEMAS.md`
- `references/RESPONSIBILITY-GOVERNANCE.md`
- `references/VISUAL-PARITY.md`
- `references/EVIDENCE-GOVERNANCE.md`
- `references/LANGUAGE-GOVERNANCE.md`
- `references/GIT-GOVERNANCE.md`
- `references/DOCUMENTATION-GOVERNANCE.md`
- `references/REPORTING.md`

## Completion response

When reporting work, state:

- lifecycle/state reached;
- legacy baseline/last checked commit;
- capabilities reproduced/remaining;
- architecture remediation performed;
- framework strategy and its human decision reference;
- functional/visual/architecture/traceability evidence status;
- unresolved legacy deltas/unknowns;
- deferred `NEW_REQUIREMENT` items;
- whether the repository is `HANDOFF_READY`.

---

## v2.0 Multi-Dimensional Parity (mandatory, supersedes v1.7 for new work)

**v1.7 Network-Alignment was necessary but not sufficient.** The agent in
2026-09 produced a "model dashboard" that:
- used 3 entirely wrong URLs (`/lcy/model/modelDashboard`, `/lcy/model/getModelCount`)
  instead of the real `/lcy/model/trend/getStatusDistribution*` family;
- invented a 7-line chart with 7-series legend, 7 hand-picked colors, and a
  donut pie — none of which exists in production;
- shipped 4 table columns (`createBy/created/updateBy/updated`) that production
  doesn't show, while missing the production column the user explicitly cared
  about;
- all while typecheck and unit tests passed, and the dev:real page rendered
  without errors.

The root cause is that v1.7 only governs **API integration**. v2.0 extends
parity to four additional dimensions, all required to reach `MODERNIZED`:

1. **API parity** (Network-Alignment) — every URL/method/param/response backed
   by a captured manifest request.
2. **Field-level parity** — every legacy table column, form field, filter,
   label, breadcrumb, tab, and operation button must appear in the new view,
   in the same order, with the same data type, and the new view must not add
   fields production does not have.
3. **Visual parity** — chart types, chart colors, chart series names, layout
   structure, spacing, and control styles must match production screenshots
   pixel-for-pixel where reasonable. Inventing new chart kinds, new color
   palettes, or new series layouts is forbidden.
4. **Operation parity** — every clickable action in production (button, menu
   item, row operation, batch operation, modal action) must be wired to a real
   or explicit "later" handler. Skipping a button because it is "later work"
   is forbidden — if it is in production, it must be present and visibly
   wired even if the implementation is a placeholder that calls out to a TODO
   manifest.

### Per-page acceptance contract (mandatory)

For every user-visible page you migrate, produce
`migration/<domain>/pages/<page-slug>.yaml` before writing any view code:

```yaml
# migration/<domain>/pages/<page-slug>.yaml
page: <legacy-path>
captured_at: 2026-09-10T16:30:00+08:00
legacy_screenshot: migration/<domain>/evidence/<page-slug>.png
target_screenshot: migration/<domain>/evidence/<page-slug>.target.png   # after this work
# ---------------------------------------------------------------------
# 1. Layout regions
layout:
  regions: [header, toolbar, tabs, filter_bar, table, pager, footer]
  # legacy_screenshot.png must show each region; new view must render it.

# ---------------------------------------------------------------------
# 2. Filter bar — every visible control
filter_bar:
  controls:
    - { type: el-radio-group, items: [{label: 机器学习, value: ML}, {label: 深度学习, value: DL}], model: modelTypeCategory, default: ML }
    - { type: el-input, placeholder: 请输入模型名称, model: modelName }
    - { type: el-select, placeholder: 学习方式, model: learnMethod, options_from: dict_ML }
    - { type: el-date-picker, type: daterange, start_placeholder: 创建时间, end_placeholder: 结束时间, model: dateRange }
  # NOTHING may be invented. Each control must appear in the legacy screenshot.

# ---------------------------------------------------------------------
# 3. Table columns — every column, in order
table:
  columns:
    - { type: selection, width: 48 }
    - { prop: modelName, label: 模型名称, min_width: 160, show_overflow_tooltip: true }
    - { prop: modelType, label: 模型类型, min_width: 120 }
    - { prop: learnMethod, label: 学习方式, min_width: 120 }
    - { prop: versionCount, label: 版本数量, width: 90, align: center }
    - { prop: created, label: 创建时间, min_width: 160 }
    - { prop: createBy, label: 创建者, width: 100 }
    - { type: action, label: 操作, width: 120, fixed: right, items: [查看, 删除] }
  # Every column must be present. The order must match the legacy screenshot.
  # If a column is in target code but not in this list, it is FORBIDDEN.
  # If a column is in this list but not in target code, the work is INCOMPLETE.

# ---------------------------------------------------------------------
# 4. Operations — every clickable thing
operations:
  - { id: query,        trigger: filter.查询, action: "search()" }
  - { id: import,       trigger: toolbar.导入模型, action: "onImport()" }
  - { id: batch_delete, trigger: toolbar.批量删除, action: "onBatchDelete()" }
  - { id: row_delete,   trigger: row.操作.删除, action: "onDelete(row)" }
  - { id: row_detail,   trigger: row.操作.详情, action: "onDetail(row)" }

# ---------------------------------------------------------------------
# 5. Network — every request this page fires
network_ref: migration/<domain>/network-manifest.yaml#pages[name=模型列表].requests
```

**Rules:**

1. **No filter is added that production does not have.** If your view has a
   filter the legacy page doesn't, you invented it.
2. **No column is hidden or removed without a documented decision** in
   `migration/<domain>/delta-decisions.yaml`.
3. **No column is added that production doesn't have.** If your view renders
   `createBy/created/updateBy/updated` columns and the production screenshot
   does not show them, the columns must be removed.
4. **Every action button has a wired handler.** A button that does nothing on
   click is forbidden. Placeholder handlers must call out to
   `migration/<domain>/TODOs.yaml` with a real entry.
5. **No invented chart kinds.** If production shows 3 distinct filter blocks
   feeding 3 charts, you do not get to "simplify" them into 1 filter and 1
   chart. Replicate the structure.
6. **No invented colors.** Read the colors from the legacy screenshot (eyedrop
   or color pick), or copy from the legacy CSS file, or copy from the legacy
   ECharts option object. Never pick from a Tailwind default palette.
7. **No invented series names.** If production's pie legend says
   "总量/机器学习/深度学习/大模型", you do not get to rename it to
   "已导入/在线服务/离线预估".

### Per-page parity check (mandatory, runs before `MODERNIZED`)

After implementing a page, you MUST run:

```bash
# 1. Take a fresh screenshot of the new view in dev:real.
node tools/screenshot.mjs --url http://localhost:5173/<route> \
                          --out migration/<domain>/evidence/<page-slug>.target.png
# 2. Use pixel-diff vs legacy screenshot; record in evidence/<page-slug>.diff.png
node tools/diff.mjs --a migration/<domain>/evidence/<page-slug>.png \
                    --b migration/<domain>/evidence/<page-slug>.target.png \
                    --out migration/<domain>/evidence/<page-slug>.diff.png
# 3. Use LLM vision to enumerate visible elements in BOTH screenshots
#    and produce a 1:1 element list; flag every missing/excess/renamed element.
node tools/element-compare.mjs --a ... --b ... --out migration/<domain>/evidence/<page-slug>.elements.yaml
```

A page is **not** at `VISUAL_PARITY_CHECK = PASS` until:

- [ ] Filter bar has the same controls in the same order.
- [ ] Table has the same columns in the same order, no missing, no excess.
- [ ] Charts have the same kind, same series names, same legends, same colors.
- [ ] Operation buttons are all present and have wired handlers.
- [ ] Network requests match the manifest URL/params/responses.

### Recursive capture (mandatory, v2.0)

A page that "loads once and shows data" hides half of its API surface. Before
declaring a page's network manifest complete, you MUST trigger every state:

- **Every tab / radio / dropdown filter** — switch them, capture the new
  requests.
- **Every action button** — click it, capture the requests.
- **Every pagination state** — go to page 2, change page size.
- **Every form** — open it, fill required fields, save.
- **Every modal** — open it, close it, submit it.

For dashboards specifically:

- **Every filter combination** — change modelType select, change date range,
  change 24h/3d/7d/30d radio, capture the requests for each combination.
- **Every "view type" or sub-tab** — if the dashboard has 3 panels, each panel
  fires its own requests; capture each panel's requests, not just the first.

Record every captured combination in
`migration/<domain>/network-manifest.yaml` with `combinations:` keys.

### Field-level mirror (mandatory, v2.0)

For every table column, form field, filter, breadcrumb, menu item, and
operation button in the legacy page, the new view must have a 1:1
counterpart. Produce `migration/<domain>/pages/<page-slug>.yaml` with
`table.columns`, `form.fields`, `toolbar.items`, `filter_bar.controls` lists
that name every element by `prop` / `key` / `value` / `placeholder` and point
to the legacy screenshot.

A page's `MODERNIZED` transition is blocked until the element list is
exactly equal to the legacy page's element list. Excess elements are
forbidden; missing elements are blocking defects.

### Mock-fidelity gate (mandatory, v2.0)

Mock data is allowed only if it satisfies:

1. **Shape fidelity** — every field in the mock is also in the real captured
   response for at least one production record.
2. **Value-space fidelity** — every enum string in the mock is one of the
   values observed in the production response (not invented from "common
   sense").
3. **Variance fidelity** — the mock has at least one record per UI state
   (selected, paginated, filtered-empty, error, etc.).
4. **No false sense of completeness** — if the production API returns
   `descDatasetType` but the mock row has both `descDatasetType` and
   `datasetType`, the second field is a guess and must be removed.

A mock that "looks plausible" but diverges from the real shape is treated as
a defect, not a convenience.

### Failure mode v2.0 exists to prevent

The agent reads `lcy-model.js`, finds `url: 'lcy/model/modelDashboard'`,
writes the same path in the new repo, picks 7 line colors and 7 series names
that "look like a dashboard", ships the view, runs unit tests with mocked
data, sees green, declares done. v1.7 caught the URL part. v2.0 catches
the other six failure modes: missing fields, excess fields, invented charts,
invented colors, unwired operations, and un-rendered filter combinations.

