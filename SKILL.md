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
  version: "1.6.0"
  domain: "frontend-architecture-modernization-governance"
  lifecycle: "discover-assess-confirm-transform-verify-handoff"
---

## v1.6 Live Runtime Truth + Module-Delivery Loop

v1.6 is a behavior-anchoring release. It does not remove any v1.5.1 capability. It
adds three hard rules that the Agent can no longer skip:

1. **Live runtime evidence is a first-class citizen.** When the legacy production
   URL is reachable, every UI/UX truth must come from a `live-runtime-snapshot` /
   `live-runtime-flow` evidence captured against that URL. Legacy repo source code
   may inform implementation mapping, but it is no longer treated as UI/UX truth.
2. **Modules are delivered atomically.** Each module walks the full lifecycle
   (route + UI + API + flow) before the next module starts. W2-Later, "deferred",
   "本切片仅 ..." and similar partial labels are no longer accepted.
3. **`STRICT_PRESERVE` must use a live baseline.** When `profile.live_runtime.required`
   is true, `visual-manifest.json` must declare `baseline_source: live_runtime` with
   a complete `live_runtime` sub-object. A legacy build baseline alone is rejected.

The full set of patches applied for v1.6 is documented in
`2026-09-08-live-runtime-evidence.patch.md` and rolled into the schema, engine and
reference files in this skill. Implementation guidance is in
`references/EVIDENCE-GOVERNANCE.md`, `references/DISCOVERY.md`,
`references/VISUAL-PARITY.md` and `references/WORKFLOW.md`.

### Delivery mode (default vs explicit)

- Default mode = **Module-Delivery-Loop**: each module walks the full lifecycle
  (see `references/WORKFLOW.md`). v1.6 enforces this for `profile.project_size`
  of `medium` or `large`.
- Explicit `legacy-phase-mode` is allowed only when `profile.project_size: small`
  or `profile.delivery.mode: legacy-phase` is set at initialization. Even then,
  any deferred capability must be backed by an explicit `decision: ADR-*`.

### Live runtime configuration

`governance/project.yaml` (and `assets/profiles/legacy/*.yaml` templates) declare:

```yaml
live_runtime:
  url: ""           # production entry; empty = disabled
  auth:
    type: ""        # cookie | bearer | none
    selector: ""    # description only; never store real credentials
  required: false   # when true, STRICT_PRESERVE / IMPLEMENTING enforce live baseline
  capture:
    driver: ""      # playwright | puppeteer | cursor-browser | manual
    output_dir: migration/system/live-baseline
```

When `live_runtime.required=true` but `live_runtime.url` is empty, the Agent MUST
stop and ask the user for the live URL. Default is `required=false`.

## v1.5.1 Discovery Closure

v1.5.1 is a patch-level closure release. It does not change the modernization
lifecycle or Skill scope.

Discovery hardening:

- TypeScript generic request wrappers are supported, including nested generics:
  `portalRequest<Model>('/x')` and
  `portalRequestPage<PageResult<Model>>('/x')`.
- Request wrapper families may contain `Request` in the identifier, so
  `portalRequestPage(...)` is treated as request evidence.
- Route-object qualification uses top-level object keys only. Nested
  `query.redirect` / `meta.redirect` fields do not turn navigation objects into
  route definitions.
- Common route-builder calls such as
  `add('/old', '/new')` are retained as HEURISTIC route evidence.
- When API discovery is PARTIAL, `api_data_flow.score` is `null`. An incomplete
  discovery surface must not receive an optimistic architecture-quality score.
- Markdown documentation endpoints such as `/api.md` are excluded from the API
  catalog.
- `modernize doctor --fix-install-name` can safely rename a suffixed installation
  folder when the canonical destination does not already exist.

## v1.5 Discovery Accuracy Hardening

v1.5 hardens Discovery so generated reports are less likely to present incomplete
static evidence as product truth.

Key rules:

- Relative Vue/React route object paths such as `path: 'hall'` are valid route
  evidence when the containing object is route-shaped.
- Navigation objects such as `router.push({ path: '/' })` are not route definitions.
- Custom request wrappers ending in `Request`, `Api`, `Client`, `Http` or `Fetch`
  are scanned for literal endpoints.
- Dynamic request calls are recorded as unresolved API signals instead of being
  silently ignored.
- If request signals exist but zero concrete API endpoints are recovered,
  `modernize validate --completeness` MUST fail.
- `packages/*` workspace boundaries and route segments may produce confirmable
  Domain Candidates.
- infrastructure folders such as `src/config`, `src/data`, `src/lib`,
  `src/types` and `src/requests` are Structural Hints only and cannot be confirmed
  directly as Domains.
- Architecture remediation entries must preserve source file identity.
- The system report must include API discovery status, unresolved API signals,
  cross-area/package import summaries and remediation file paths.

## v1.4 Discovery & Documentation Engine

v1.4 closes the gap between the executable governance protocol and the factual,
human-readable project knowledge needed for long-running brownfield reconstruction.

### Project vs Domain lifecycle

Project lifecycle owns global discovery and architecture decisions:

```text
DISCOVERED
→ CURRENT_SYSTEM_MODELED
→ ARCHITECTURE_ASSESSED
→ FRAMEWORK_STRATEGY_CONFIRMED
→ TARGET_FOUNDATION_READY
→ MODERNIZATION_ACTIVE
→ HANDOFF_READY
```

A confirmed Domain owns only its reconstruction lifecycle:

```text
DISCOVERED
→ CAPABILITY_MODELED
→ RESPONSIBILITY_REVIEWED
→ TARGET_CONTRACT_DEFINED
→ REMEDIATION_PLANNED
→ IMPLEMENTING
→ FUNCTIONAL_PARITY_CHECK
→ VISUAL_PARITY_CHECK
→ ARCHITECTURE_CHECK
→ TRACEABILITY_CHECK
→ MODERNIZED
```

Do not create Domain ledgers during bootstrap. Discovery first produces candidate evidence.
Create a Domain only after semantic review:

```bash
modernize domain create users --candidate MOD-CAND-001 --repo .
```

### Discovery truth pipeline

```text
Framework-aware analyzer
→ raw-analysis/*
→ canonical normalizer
→ api-catalog / legacy-system-map / domain candidates /
  capability candidates / runtime unknowns
→ semantic Agent review
→ approved CAP-* / confirmed Domains
```

Candidate facts (`CAP-CAND-*`, `MOD-CAND-*`) are not approved product facts.
The Agent must review evidence before creating stable `CAP-*` or confirmed Domain ownership.

### Reporting is executable

Run:

```bash
modernize report system --repo .
```

The generated master report has 18 sections. Missing knowledge must be rendered as
`UNKNOWN` / incomplete evidence, never as an empty heading that looks complete.

### Validation is layered

```bash
modernize validate --structure --repo .
modernize validate --state --repo .
modernize validate --completeness --repo .
modernize validate --all --repo .
```

- `structure`: schema/files/language.
- `state`: lifecycle prerequisites and gate evidence.
- `completeness`: whether discovery facts are sufficient for the current state.
- `all`: all layers plus evidence verification.

A structure PASS does not mean the system has been fully understood.

### Framework-aware discovery

v1.4 detects Vue2, Vue3, React and Next.js. Vue2 keeps the AST adapter; Vue3/React/
Next.js use framework-aware static discovery for common route structures and Next.js
filesystem routes. Dynamic/custom routing must be recorded as runtime/custom-manifest
evidence rather than silently treated as zero routes.

### Scope remains unchanged

This Skill does not implement net-new product requirements. Its responsibility remains:
read-only Legacy → new Repository → architecture modernization + complete product
behavior reproduction → evidence → HANDOFF_READY.


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
