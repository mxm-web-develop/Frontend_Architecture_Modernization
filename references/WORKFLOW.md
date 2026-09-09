# v1.3 Workflow

## Scope

This workflow reconstructs an existing frontend into a separate new repository. It does
not implement Target-only net-new product requirements.

## Lifecycle

```text
DISCOVERED
-> CURRENT_SYSTEM_MODELED
-> CAPABILITY_MODELED
-> ARCHITECTURE_ASSESSED
-> FRAMEWORK_STRATEGY_CONFIRMED
-> RESPONSIBILITY_REVIEWED
-> TARGET_CONTRACT_DEFINED
-> REMEDIATION_PLANNED
-> IMPLEMENTING
-> FUNCTIONAL_PARITY_CHECK
-> VISUAL_PARITY_CHECK
-> ARCHITECTURE_CHECK
-> TRACEABILITY_CHECK
-> MODERNIZED
-> HANDOFF_READY
```

### Discovery

Run bootstrap and analyze. Bootstrap leaves framework strategy `UNDECIDED`.

### Capability modeling

Recover product capabilities from Legacy behavior/evidence. Do not treat files/routes as
final module boundaries.

### Architecture assessment

Compare Legacy architecture against the unified modernization constitution. Produce
remediation findings and code-health evidence.

### Framework strategy

Generate recommendations, then require explicit human confirmation + ADR.

### Target definition and remediation planning

Define module manifests, integration contracts, target data/state/runtime boundaries and
source-to-target mappings. The selected framework adapter controls implementation details,
not the architecture principles.

### Implementation and parity

Reproduce Legacy capabilities while improving implementation architecture. New product
requirements remain deferred.

### Modernized

All required evidence gates pass and Legacy capability coverage is complete.

### Handoff ready

Generate the handoff package, verify module/docs/commands/governance, and transfer
Target-only new requirements to the post-modernization backlog.

## Legacy delta loop

While Legacy remains active:

```text
MODERNIZED -> SYNCING -> MODERNIZED
```

A newly shipped Legacy capability is `LEGACY_DELTA` and remains in scope.

## Module-Delivery Loop (v1.6 default)

当 `profile.project_size` 不是 `small` 或用户显式选择 `delivery.mode: module-loop` 时，
**禁止**沿用 W0/W1/W2/W3 串行分期。Module-Delivery Loop 是默认的施工节奏：

```text
module-baseline
  → live-runtime capture (snapshot + flow)         # P1/P2 留证
  → legacy evidence mapping (source code 映射)      # 仅作实现逻辑参照
  → target-contract (per module)
  → IMPLEMENTING (route + UI + API + flow 一次性做完)
  → FUNCTIONAL_PARITY_CHECK (用 live-runtime evidence 比对)
  → VISUAL_PARITY_CHECK (用 live baseline 比对，STRICT_PRESERVE 强制)
  → ARCHITECTURE_CHECK
  → TRACEABILITY_CHECK
  → module-MODERNIZED
  → next module
```

每个模块独立走完整 lifecycle，**不允许**：

- 在一个模块内做"先接口后 UI"（P3/P4 反对）；
- 在多个模块同时"先 X 后 Y"交错（P3 反对）；
- 写 `deferred / later / 本切片仅 ... / W2-Later` 等承认偷懒的标签（P4 反对）。

每个模块完成时**必须**具备：

- `migration/domains/<domain>/route-coverage.yaml`：covered == total；
- `migration/domains/<domain>/completeness/<cap_id>.yaml`：
  `{route: true, ui: true, api: true, flow: true}`；
- `migration/domains/<domain>/live-runtime/<cap_id>-default.json`：
  live-runtime-snapshot 证据；
- `migration/domains/<domain>/live-runtime/<cap_id>-flow.json`：
  live-runtime-flow 证据（跨页 / 表单 / 对话流 capability）。

### legacy-phase mode (opt-in only)

只有当 `profile.project_size: small` 或用户在初始化时显式设置
`delivery.mode: legacy-phase` 时，才允许走 v1.5 之前的串行分期（W0 / W1 / W2 / W3）。
任何 W2-Later / W3-pre 等"延后"标签都必须以独立 `decision: ADR-*` 落地，并被 `decisions.md`
显式引用，否则按 v1.6 P4 视为违规。
