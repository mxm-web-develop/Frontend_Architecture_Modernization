# Changelog

## 1.6.0

### Live runtime evidence as first-class citizen
- Added two new evidence types: `live-runtime-snapshot` (single URL visit) and
  `live-runtime-flow` (multi-step browser interaction). They are recognized by
  `gate-evidence.schema.json` and validated by
  `engine/evidence/verification.py` through `engine.runtime_capture`.
- Visual manifests for `STRICT_PRESERVE` scenarios now require
  `baseline_source: live_runtime` plus a complete `live_runtime` sub-object
  (`url`, `captured_at`, `commit`, `screenshot_sha256`). Legacy build alone is
  rejected as the only baseline.
- `validate_visual_evidence.py` enforces the new schema at the script level so
  CI/agents cannot bypass the gate via plain YAML.

### Module-Delivery Loop replaces W0/W1/W2/W3 partial staging
- Added `profile.delivery.mode` (`module-loop` default; `legacy-phase` opt-in)
  and `profile.project_size`. Medium and large projects must use Module-Delivery
  Loop (see `references/WORKFLOW.md`).
- Removed the implicit permission to ship "接口通 / UI 延后" splits across
  modules. Each module now requires 100% route + UI + API + flow completeness
  before transitioning to `MODERNIZED`.

### Tighter MODERNIZED prerequisites
- New domain-level files: `route-coverage.yaml` and `completeness/<cap_id>.yaml`.
- `engine/state/machine.py` now fails `MODERNIZED` if any of:
  - `route-coverage.covered < route-coverage.total`;
  - `completeness.<cap_id>.{route, ui, api, flow}` is not `true`;
  - `profile.live_runtime.required=true` and the capability has no
    `live-runtime/<cap_id>*.json`.
- `IMPLEMENTING` now requires `live-runtime/*.json` when
  `live_runtime.required=true`.

### Capability approval hardening
- `engine/capability_registry.approve` rejects approvals when
  `live_runtime.required=true` but no live baseline exists for that capability.
- Default `ui.baseline_source` is now `live_runtime` when
  `profile.live_runtime.url` is non-empty.

### New engine module
- `engine/runtime_capture.py` provides the Live Runtime contract: directory
  layout, evidence record types, `LiveRuntimeSpec`, validation helpers. Driver
  (playwright / puppeteer / cursor-browser / manual) is pluggable; the contract
  is the source of truth.

### References
- `references/EVIDENCE-GOVERNANCE.md`: classification table now lists all four
  evidence types and the live runtime baseline contract.
- `references/DISCOVERY.md`: added `Live runtime baseline` section describing
  the execution contract, immutability of baseline and fallback decision rule.
- `references/VISUAL-PARITY.md`: added explicit truth-source priority (live
  runtime > legacy build > legacy source) and the rule that legacy repo code
  is implementation-mapping only, never UI/UX truth.
- `references/WORKFLOW.md`: added Module-Delivery Loop and the `legacy-phase`
  opt-in carve-out.

### Profile / governance templates
- `assets/profiles/legacy/vue2-dashboard-to-vue3-domain-app.yaml`
- `assets/profiles/legacy/generic-frontend-modernization-v1.2.yaml`
- `assets/templates/governance/project.yaml`
all gained `live_runtime`, `delivery`, `project_size` blocks with safe defaults
(empty URL + `required: false` + `mode: module-loop`).

## 1.5.1

### Discovery closure
- Support TypeScript generic request wrappers, including nested generic types.
- Recognize wrapper names containing `Request`, including `portalRequestPage`.
- Qualify route objects using top-level keys only; nested `query.redirect` no longer causes route false positives.
- Record common route-builder redirects/calls as HEURISTIC route evidence.
- Set `api_data_flow.score` to null whenever API discovery remains PARTIAL.
- Exclude Markdown documentation paths such as `/api.md` and `.mdx` from business API discovery.
- Add `modernize doctor --fix-install-name` for safe installation-folder repair.

## 1.5.0

### Discovery accuracy
- Recover relative Vue/React route object paths such as `hall`, `application`, and `admin`.
- Reject route-like navigation objects that lack route-definition markers.
- Recognize literal endpoints passed through custom `*Request`, `*Api`, `*Client`, `*Http`, and `*Fetch` wrappers.
- Record unresolved dynamic fetch/request calls in `api-signals.json`.
- Fail completeness when HTTP/API call signals exist but zero concrete endpoints are resolved.
- Make API architecture score unknown/incomplete rather than optimistic when discovery is unresolved.
- Add `packages/*` workspace boundaries as confirmable Domain Candidate evidence.
- Downgrade infrastructure source folders to non-confirmable Structural Hints.
- Preserve source file paths in architecture remediation items.
- Add API discovery state, unresolved request tables, cross-package import summaries, and remediation file paths to reports.
- Improve AI-readiness evidence by distinguishing existing Legacy docs from modernization governance.
- Add a concrete doctor repair hint for incorrectly suffixed Skill install folders.

## 1.4.0

### Discovery & documentation engine
- Added Project Lifecycle separate from Domain Lifecycle.
- Bootstrap no longer accepts or creates Domains before discovery.
- Added framework-aware Vue3/React/Next.js static route discovery; Vue2 AST remains.
- Added raw-analysis -> canonical facts normalization.
- Added Capability and Domain candidate queues requiring semantic review.
- API detection filters common schema/docs URLs and canonicalizes endpoints.
- Architecture findings now populate the remediation backlog.
- Code-health scanning excludes agent/tool/vendor/generated directories and scores SOURCE code.
- `package.json` scripts populate governed commands.
- Added `modernize report system` with an 18-section generated report and explicit UNKNOWN states.
- Split validation into structure/state/completeness/all layers.
- Added project/domain status visibility and rich handoff documents.
- Localized `AGENTS.md` and removed hard-coded `.codex/skills` command paths.

## 1.3.0

### Changed
- Reframed the Skill as brownfield architecture modernization into a **new repository**, not general feature development or framework conversion.
- Bootstrap is discovery-first and leaves target framework `UNDECIDED`.
- Replaced migration-centric terminal state with `MODERNIZED -> HANDOFF_READY`.
- Unified target architecture is framework-independent; Vue/React/Next/custom are implementation adapters.
- New product requirements are explicitly out of scope and deferred to post-modernization handoff.

### Added
- Unified `modernization-constitution.yaml` for AI-native, module-oriented, capability-first, integration-first, code-health, documentation and evidence governance.
- Current-system model and architecture assessment lifecycle.
- Framework recommendation + human-confirmed selection with ADR.
- Source adapter registry and executable generic analyzers for Vue3/React/Next/unknown projects, while retaining Vue2 AST analysis.
- Code-health assessment.
- Scope register with `LEGACY_PARITY`, `LEGACY_DELTA`, `ARCHITECTURE_REMEDIATION`, `GOVERNANCE_ENABLEMENT`, `NEW_REQUIREMENT`.
- Module registry, deterministic module scaffold and module manifest schema.
- Diagnostic domain-affinity engine.
- Handoff package and `HANDOFF_READY` boundary for downstream feature-development Agents/Skills.
- v1.2 control-plane upgrade command and compatibility state mapping.

### Removed from defaults
- Vue2 -> Vue3/Nx as a default target assumption. The old v1.2 profiles are retained only under `assets/profiles/legacy/`.
- In-place modernization as a supported v1.3 project mode; v1.3 is scoped to Legacy repo -> new Target repo reconstruction.

## 1.2.2

### Added
- Enforced project language governance for human-readable Markdown.
- Evidence-backed functional, visual, architecture and traceability gates.
- `modernize run-check` with governed command keys and hashed command evidence.
- Visual result/PNG SHA-256 verification.
- Automatic Legacy changed-file -> `CAP-*` mapping during sync scan.

### Fixed
- `modernize validate` can no longer accept Visual PASS without actual harness result and PNG evidence.
- Gate PASS can no longer be set without valid evidence.
- `IMPLEMENTING` requires an existing mapped Target source path.
- Bootstrap now persists `legacy-system-map.yaml.baseline_commit`.
- `.modernization.json.skill_version` is 1.2.2.
- `LEGACY_FROZEN` can explicitly transition to `ROLLED_BACK` with a reason.


## 1.2.1

### Added
- Full lifecycle trigger guide in both English and Chinese README files.
- Trigger matrix for bootstrap, analysis, capability modeling, domain discovery,
  responsibility review, architecture design, planning, migration, verification,
  delta sync, reporting, resume, cutover, rollout, rollback and legacy retirement.
- Recommended Cursor and Codex invocation patterns.
- Phase safety rules clarifying that lifecycle trigger semantics never bypass the
  state machine or mandatory CLI contract.

### Changed
- Documentation now standardizes on:
  `explicit skill + lifecycle phase + domain/capability scope + constraints`.

## 1.2.0

Execution-protocol release.

- Added a single canonical `scripts/modernize.py` CLI: doctor, install-engine,
  bootstrap, analyze, validate, transition, gate, visual, sync, cutover and status.
- Added Mandatory Execution Contract to `SKILL.md`; agents must use the deterministic
  engine instead of inventing initial ledgers or manually changing migration state.
- Replaced regex-first Vue2 route/API/state extraction with an AST-first TypeScript
  Compiler API adapter.
- Fixed adjacent Vue Router object field bleed; route `name/redirect` are now read
  from the same AST object as `path`.
- Added source line evidence and confidence levels to analyzer facts; dynamic routes
  become `NEEDS_RUNTIME_EVIDENCE` instead of fabricated static values.
- Added Analyzer Adapter Protocol and `generic-frontend-modernization` adapter contract.
- Added state-aware validation and CLI-controlled migration state transitions.
- Deprecated `validate_migration_state.py` in favor of unified governance validation.
- Added `target-contract.yaml`, `functional-scenarios.yaml`, cutover plan/status and
  executable schemas.
- Added production cutover lifecycle and rollback state.
- Added Core support for `cross-repository` and `in-place` modernization. In-place
  mode preserves Legacy via a detached Git baseline worktree.
- Upgraded Visual Harness with server orchestration, health checks, multiple auth
  strategies, font checks, deterministic mocks and visual environment evidence.
- Added install/folder doctor to catch Agent Skills directory-name mismatch early.

## 1.1.0

- Added deterministic Bootstrap CLI and canonical governance/migration templates.
- Added executable JSON Schemas and semantic governance validator.
- Added initial Vue2 legacy analyzers.
- Added dual-source visual screenshot harness.
- Added generic frontend modernization profile.

## 1.0.0

- Initial architecture-modernization governance skill.
- Capability-first migration, four gates, visual strict-preserve policy, Git and docs
  governance, delta tracking and human-readable migration reporting.
