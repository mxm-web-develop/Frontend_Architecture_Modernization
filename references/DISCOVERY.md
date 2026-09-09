# Current-System Discovery

Discovery answers **what exists now**, not what the target should be.

Required outputs include current framework/build/state/router indicators, raw route/API/
import/state facts, source evidence, runtime unknowns, capability inputs and code-health
signals.

`governance/current-system.yaml` must never imply a selected target framework.

Analyzer facts have evidence confidence. Dynamic behavior that cannot be statically
proved remains explicit `NEEDS_RUNTIME_EVIDENCE`/`UNKNOWN` rather than guessed.

## v1.5 discovery accuracy rules

- Relative route object paths such as `hall` are valid evidence when the containing
  object is route-shaped.
- Navigation calls such as `router.push({ path: '/' })` are not route definitions.
- Resolved and unresolved HTTP/API evidence are separate outputs.
- `api-signals.json` records request calls that cannot yet be resolved to concrete
  endpoints.
- If request signals exist but zero endpoints are resolved, Discovery completeness
  must fail.
- Workspace `packages/*` boundaries and route segments can become confirmable Domain
  Candidates.
- `src/config`, `src/data`, `src/lib`, `src/types`, `src/requests` and similar
  infrastructure folders are Structural Hints only.

## v1.5.1 closure rules

- Request wrapper discovery accepts optional TypeScript generic arguments and
  wrapper identifiers containing `Request`.
- Route-object markers are evaluated only at object-literal top level.
- Route-builder helper matches are HEURISTIC evidence, not confirmed route truth.
- Documentation files (`.md`, `.mdx`) are not business API endpoints.

## v1.6 Live runtime baseline (mandatory if production URL available)

如果 legacy 生产环境可访问（用户在 profile / `governance/project.yaml` 声明了
`live_runtime.url` 且 `live_runtime.required=true`），则：

- Discovery 阶段必须自动 / 半自动访问该 URL 列表（与 legacy route 一一对应），用
  浏览器快照（DOM + screenshot）落到 `migration/system/live-baseline/` 与
  `migration/domains/<domain>/live-runtime/`：
  - `live-baseline/routes.json`：每个 legacy 路由的
    `{url, dom_snapshot_path, screenshot_sha256, captured_at, scenario_id}`
  - `live-baseline/flows/<cap_id>/`：每个 capability 涉及的多步操作
    （点击 → 截图 → DOM）
- 这是后续 capability / visual / functional evidence 的 baseline，
  **不**再接受"legacy build 截图"作为唯一真相源
- 旧仓源码作为实现逻辑映射的源头，**不**作为 UI/UX 真相

### 执行契约

1. analyzer 跑完后，**先**问用户 live URL 与登录态（`live_runtime.auth`）；
2. 用户确认后跑 `modernize runtime capture --profile <id>` 一次性落 baseline；
3. baseline 是 immutable：diff 必须 trigger rediscovery，不能用"baseline 自动更新"绕过验证；
4. 如果 `live_runtime.required=false` 或 `live_runtime.url` 为空，必须在
   `decisions.md` 里明确写出"legacy repo 代码作为 UI 真相源的 fallback 决策"及原因。

### driver 与留证目录

- 推荐 driver：`playwright` (python-playwright) 或 Cursor 的 `browser_*` 工具；
- 不强制 driver；用 `browser_*` 手工留证与 playwright 等价；
- skill 自带真实可跑的 playwright driver：
  `engine.runtime_capture.capture_snapshot_playwright` /
  `engine.runtime_capture.capture_flow_playwright`；
- playwright 是**可选依赖**：`pip install playwright && playwright install chromium`；
  未安装时驱动函数给出明确 `RuntimeError` 而不是 `ImportError`；
- 真实 auth 凭证必须从环境变量 `LIVE_RUNTIME_AUTH_VALUE` 读，selector 只描述 key 名；
- 落地目录见 `engine/runtime_capture.py`：固定写死的契约，driver 只决定采集方式。

入口脚本：`scripts/runtime_capture.py`，直接根据 `governance/project.yaml` 跑一次
capture 并写 manifest；调用方负责把 `MigrationRecord` 落到 `migration/domains/<domain>/live-runtime/`。
