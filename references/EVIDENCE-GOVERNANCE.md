# Evidence Governance

A gate is not true because YAML says `PASS`.

## Evidence classification

A gate is not true because YAML says `PASS`. Three evidence types are recognized;
each has required fields enforced by `modernize validate` and `engine.evidence.verification`.

| Type | Source | Required fields |
|---|---|---|
| `command-run` | runner (vitest, playwright, eslint) | command, exit_code, stdout/stderr sha256, commit, started_at, ended_at, gate, status |
| `visual-harness` | visual harness run | result.json with environment + per-scenario legacy/target/diff sha256 |
| `live-runtime-snapshot` | live production runtime (`browser_*`) | url, screenshot_sha256, dom_snapshot_path, captured_at, commit |
| `live-runtime-flow` | live production runtime (`browser_*` step-by-step) | steps: array of `{action, screenshot_sha256, dom_snapshot, captured_at}`, captured_at, commit |

新增的两类用于**线上环境**作为 evidence 一等公民：

- `live-runtime-snapshot` — 一次性访问线上某 URL 留证（首页、列表详情、空状态等）
- `live-runtime-flow` — 多步操作（点击 / 输入 / 路由切换）的逐步留证（对话流、表单提交、跨页跳转）

## Live runtime evidence

如果 legacy 生产环境可访问（用户在 profile / `governance/project.yaml` 里声明 `live_runtime.url`）：

- **必须**用浏览器工具实际访问（curl / DOM dump / 截图 / step sequence），把页面证据落入仓库
- 旧仓源码作为实现逻辑映射的源头，**不**作为 UI/UX 真相
- `visual-manifest.json` 的 baseline_source **必须**为 `live_runtime`（STRICT_PRESERVE 强制）
- 每个 domain 开工时**必须**先在 `migration/domains/<domain>/live-runtime/` 落 baseline 与 flow 证据
- 进入 `MODERNIZED` 前必须校验：legacy 路由覆盖率 100%、每个 capability 的 route/ui/api/flow 完整度 100%

## Command evidence

Functional, architecture and traceability gates use runner-produced command evidence
with command, command-key, exit code, timestamps, Git commit, stdout/stderr and hashes.
`modernize validate` re-checks evidence artifacts.

## Visual evidence

Visual PASS references Visual Harness `result.json`. Validation checks required
scenarios, result status, Legacy/Target/Diff PNG existence, PNG signatures and hashes.
v1.6 起，每个 STRICT_PRESERVE scenario 必须额外提供 `live_runtime` 字段作为真相源。

## MODERNIZED

A Domain can reach `MODERNIZED` only when:

- required gates and capability parity have verifiable evidence;
- legacy route coverage is 100% (`route-coverage.yaml: covered == total`);
- each capability's `route/ui/api/flow` completeness is 100%
  (`completeness/<cap_id>.yaml` 全为 `true`);
- if `live_runtime.required=true`, all approved capabilities have matching
  `live-runtime/<cap_id>-*.json` evidence.

## HANDOFF_READY

Handoff additionally requires repository governance, discoverable commands, target
module manifests/docs and the generated handoff package. New product requirements must
remain deferred.