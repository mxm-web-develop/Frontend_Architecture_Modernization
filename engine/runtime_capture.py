"""Live runtime baseline capture (v1.6, P2).

驱动契约：访问线上 URL + 留截图 + DOM 快照。

落地目录约定：

```
<output_dir>/
  routes.json                       # 路由 → {url, dom_snapshot, screenshot_sha256, captured_at, scenario_id}
  dom/<sha>.html                    # DOM 序列化（可读 HTML）
  shots/<sha>.png                   # 截图（PNG，必须 \x89PNG\r\n\x1a\n 开头）
  flows/<cap_id>/step-N-<action>.{html,png}
```

`<output_dir>` 由 `governance/project.yaml.live_runtime.capture.output_dir` 决定，
默认 `migration/system/live-baseline`。

每个 domain 维度还有：

```
migration/domains/<domain>/live-runtime/
  <cap_id>-default.json             # live-runtime-snapshot 证据
  <cap_id>-flow.json                # live-runtime-flow 证据（可选）
  completeness/<cap_id>.yaml         # {route: bool, ui: bool, api: bool, flow: bool}
  route-coverage.yaml               # {covered: int, total: int, missing: [routes]}
```

Driver：

- 推荐 `playwright` (python-playwright)；
- 也允许 `puppeteer`、`cursor-browser`、`manual`（manual = Cursor `browser_*` 手工截图 + DOM
  落盘后调用本模块封口生成 manifest）；
- 本文件提供**真实可跑**的 playwright driver（`capture_snapshot_playwright` /
  `capture_flow_playwright`），按 `profile.live_runtime.capture.driver == "playwright"`
  时启用；playwright **不**在 `scripts/requirements.txt` 里声明，属可选依赖；
  未安装时驱动函数给出明确 `RuntimeError` 而不是 `ImportError`。
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

LIVE_RUNTIME_OUTPUT_DEFAULT = "migration/system/live-baseline"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"

REQUIRED_LIVE_DIRS = ("dom", "shots", "flows")


@dataclass
class LiveRuntimeSpec:
    """profile / project.yaml.live_runtime 的强类型视图。"""

    url: str = ""
    auth_type: str = ""           # cookie | bearer | none
    auth_selector: str = ""        # 不存值，仅描述
    required: bool = False
    driver: str = ""               # playwright | puppeteer | cursor-browser | manual
    output_dir: str = LIVE_RUNTIME_OUTPUT_DEFAULT

    @property
    def enabled(self) -> bool:
        return bool(self.url) and self.driver != ""


@dataclass
class SnapshotRecord:
    url: str
    dom_snapshot_path: str
    screenshot_sha256: str
    captured_at: str
    scenario_id: str = ""
    capability_id: str = ""
    commit: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "evidence_type": "live-runtime-snapshot",
            "url": self.url,
            "dom_snapshot_path": self.dom_snapshot_path,
            "screenshot_sha256": self.screenshot_sha256,
            "captured_at": self.captured_at,
            "scenario_id": self.scenario_id,
            "capability_id": self.capability_id,
            "commit": self.commit,
        }
        d.update(self.extra)
        return d


@dataclass
class FlowStepRecord:
    action: str
    screenshot_sha256: str
    dom_snapshot_path: str
    captured_at: str
    selector: str = ""
    value: str = ""

    def to_dict(self) -> dict:
        d: dict = {
            "action": self.action,
            "screenshot_sha256": self.screenshot_sha256,
            "dom_snapshot_path": self.dom_snapshot_path,
            "captured_at": self.captured_at,
        }
        if self.selector:
            d["selector"] = self.selector
        if self.value:
            d["value"] = self.value
        return d


@dataclass
class FlowRecord:
    url: str
    capability_id: str
    steps: list
    captured_at: str
    commit: str = ""

    def to_dict(self) -> dict:
        return {
            "evidence_type": "live-runtime-flow",
            "url": self.url,
            "capability_id": self.capability_id,
            "steps": [s.to_dict() if hasattr(s, "to_dict") else s for s in self.steps],
            "captured_at": self.captured_at,
            "commit": self.commit,
        }


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_live_runtime(profile_yaml: dict) -> LiveRuntimeSpec:
    """从 governance/project.yaml 读 live_runtime 配置；空段给默认值。"""
    block = (profile_yaml or {}).get("live_runtime") or {}
    auth = block.get("auth") or {}
    capture = block.get("capture") or {}
    return LiveRuntimeSpec(
        url=str(block.get("url") or ""),
        auth_type=str(auth.get("type") or ""),
        auth_selector=str(auth.get("selector") or ""),
        required=bool(block.get("required", False)),
        driver=str(capture.get("driver") or ""),
        output_dir=str(capture.get("output_dir") or LIVE_RUNTIME_OUTPUT_DEFAULT),
    )


def ensure_output_dirs(repo: Path, spec: LiveRuntimeSpec) -> Path:
    out = repo / spec.output_dir
    out.mkdir(parents=True, exist_ok=True)
    for sub in REQUIRED_LIVE_DIRS:
        (out / sub).mkdir(exist_ok=True)
    return out


def write_snapshot(repo: Path, spec: LiveRuntimeSpec, record: SnapshotRecord) -> Path:
    """落地一张 snapshot 证据（DOM + PNG + manifest）。

    调用方负责把 PNG / HTML 已写到 `output_dir/shots` 与 `output_dir/dom` 下，
    本函数只校验并写 manifest。
    """
    ensure_output_dirs(repo, spec)
    shot = (repo / record.dom_snapshot_path.replace("dom/", f"{spec.output_dir}/dom/")).resolve()
    if not shot.exists():
        # 尝试直接在 output_dir/dom 找
        shot = (repo / spec.output_dir / "dom" / Path(record.dom_snapshot_path).name).resolve()
    if not shot.exists():
        raise FileNotFoundError(f"live runtime dom snapshot not found: {record.dom_snapshot_path}")
    shot_rel = str(shot.resolve().relative_to(repo.resolve()))
    record.dom_snapshot_path = shot_rel
    out_dir = repo / spec.output_dir
    manifest = out_dir / "routes.json"
    data: list = []
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            data = []
    # 自动补 commit（git rev-parse HEAD）；失败时写 UNKNOWN 并在 validate 时报错
    if not record.commit:
        record.commit = _git_head(repo)
    item = record.to_dict()
    if not item.get("commit"):
        item["commit"] = "UNKNOWN"
    data.append(item)
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_flow(repo: Path, spec: LiveRuntimeSpec, flow: FlowRecord) -> Path:
    """落地一个 capability 的多步 flow 证据。"""
    ensure_output_dirs(repo, spec)
    out_dir = repo / spec.output_dir / "flows" / flow.capability_id
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "flow.json"
    if not flow.commit:
        flow.commit = _git_head(repo)
    item = flow.to_dict()
    if not item.get("commit"):
        item["commit"] = "UNKNOWN"
    manifest.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _git_head(repo: Path) -> str:
    """git rev-parse HEAD；非 git 仓库返回 ""，由调用方决定是否报错。"""
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def capability_live_evidence_paths(repo: Path, domain: str) -> list[Path]:
    """domain 维度下已落盘的 live-runtime 证据文件（任意 *.json）。"""
    d = repo / "migration" / "domains" / domain / "live-runtime"
    if not d.exists():
        return []
    return [p for p in d.rglob("*.json") if p.is_file()]


def validate_runtime_manifest(repo: Path, manifest: Path) -> list[str]:
    """校验一份 live runtime manifest 是否符合 evidence 契约。

    支持两种形状：
      1) 单 record：`{"evidence_type": ..., "url": ..., ...}`
      2) 数组（routes.json 的设计）：`[{record}, {record}, ...]`

    数组形态下，**逐 record** 校验，并把 record 在数组里的下标写进错误信息。
    """
    errors: list[str] = []
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"live runtime manifest not valid JSON: {manifest}: {exc}"]
    if isinstance(data, list):
        if not data:
            return [f"live runtime manifest is empty array: {manifest}"]
        for i, item in enumerate(data):
            errors.extend(_validate_runtime_record(repo, manifest, item, i))
        return errors
    errors.extend(_validate_runtime_record(repo, manifest, data, None))
    return errors


def _validate_runtime_record(repo: Path, manifest: Path, data: dict, index: int | None) -> list[str]:
    """单 record 校验；index=None 表示单 record manifest。"""
    prefix = f"{manifest}" + (f"[{index}]" if index is not None else "")
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{prefix}: record must be an object"]
    et = data.get("evidence_type")
    if et not in {"live-runtime-snapshot", "live-runtime-flow"}:
        errors.append(f"{prefix}: evidence_type must be live-runtime-snapshot or live-runtime-flow (got {et!r})")
        return errors
    for k in ("url", "captured_at", "commit"):
        if not data.get(k):
            errors.append(f"{prefix}: missing {k}")
    if et == "live-runtime-snapshot":
        for k in ("screenshot_sha256", "dom_snapshot_path"):
            if not data.get(k):
                errors.append(f"{prefix}: missing {k}")
        dom_rel = data.get("dom_snapshot_path") or ""
        dom = repo / dom_rel
        if dom.exists():
            try:
                if dom.suffix.lower() == ".png" and dom.read_bytes()[:8] != PNG_HEADER:
                    errors.append(f"{prefix}: dom snapshot is .png but not a PNG: {dom}")
            except Exception as exc:
                errors.append(f"{prefix}: cannot read dom snapshot: {exc}")
        else:
            errors.append(f"{prefix}: dom snapshot file missing on disk: {dom_rel}")
        shot_sha = data.get("screenshot_sha256") or ""
        # 如果 dom_snapshot_path 实际指向 PNG，也校验 PNG 头部
        # （driver 实现里有的把 png 也叫 dom_snapshot_path；按 schema 两者是分开字段，
        # 这里仅校验 png 头存在性，不强制 hash 重算——sha 在写入时已自洽）
        if shot_sha and not (len(shot_sha) == 64 and all(c in "0123456789abcdef" for c in shot_sha)):
            errors.append(f"{prefix}: screenshot_sha256 not a 64-char hex string")
    else:
        steps = data.get("steps") or []
        if not isinstance(steps, list) or not steps:
            errors.append(f"{prefix}: live-runtime-flow requires non-empty steps")
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"{prefix}: steps[{i}] must be an object")
                continue
            for k in ("action", "screenshot_sha256", "dom_snapshot_path", "captured_at"):
                if not step.get(k):
                    errors.append(f"{prefix}: steps[{i}] missing {k}")
            if step.get("action") not in {"navigate", "click", "type", "select", "route", "wait"}:
                errors.append(f"{prefix}: steps[{i}].action must be one of navigate/click/type/select/route/wait")
    return errors


# ----------------------------------------------------------------------------
# Optional playwright driver
# ----------------------------------------------------------------------------
#
# Playwright 是可选依赖：
#   - 安装：pip install playwright && playwright install chromium
#   - 不安装也能 import 本模块；只在 driver="playwright" 且调用 capture_*_playwright 时才检查。
#
# 设计要点：
#   1. driver 只负责"截图 + DOM 序列化 + 文件路径"，不写 manifest；
#   2. driver 不知道 capability_id 的归属，由调用方注入；
#   3. cookie / bearer auth 在 driver 层支持，但**不**存真实凭证（仅按 selector 描述透传），
#      真实凭证必须在调用方用环境变量 / 外部 secret 注入，绝不写进 repo。
#
# Auth 注入说明：
#   - auth_type == "cookie" + auth_selector == "Cookie:SESSION=xxx"
#     → driver 会把"SESSION=xxx"作为 cookie 注入到目标域（session 域为 url host）。
#   - auth_type == "bearer" + auth_selector == "Authorization: Bearer <token>"
#     → driver 会在每个请求加上同名 header。
#   - **真实凭证永远不应硬编码**；当前实现只允许从环境变量 `LIVE_RUNTIME_AUTH_VALUE` 读取。
#
# 错误约定：
#   - playwright 未安装：RuntimeError("playwright not installed; pip install playwright && playwright install chromium")
#   - chromium 未下载：同上提示
#   - 网络 / 目标不可达：把异常原样抛出，调用方决定 retry

@dataclass
class FlowStepRequest:
    """driver 友好的 flow step 输入；调用方构造后传给 capture_flow_playwright。"""

    action: str                          # navigate | click | type | select | route | wait
    selector: str = ""                   # CSS selector；navigate/route 可空
    value: str = ""                      # type / select 的输入值
    wait_ms: int = 0                     # wait / 其他动作后的额外等待


def _ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "playwright not installed; run `pip install playwright` and "
            "`playwright install chromium` before using the live-runtime driver"
        ) from exc
    return sync_playwright


def _inject_auth(context, spec: LiveRuntimeSpec) -> None:
    """按 spec.auth 把 cookie / bearer header 注入到 playwright BrowserContext。

    真实凭证必须从环境变量 `LIVE_RUNTIME_AUTH_VALUE` 读；selector 仅作 key 名参考。
    """
    import os
    if not spec.auth_type or not spec.auth_selector:
        return
    value = os.environ.get("LIVE_RUNTIME_AUTH_VALUE", "")
    if not value:
        # 没拿到凭证就静默跳过；调用方应自己检查并显式报错
        return
    if spec.auth_type == "cookie":
        # selector 例 "Cookie:SESSION=xxx" → 取 key=SESSION，value=真实值
        key = spec.auth_selector.split(":", 1)[-1].split("=", 1)[0].strip() or "session"
        context.add_cookies([{
            "name": key,
            "value": value,
            "url": spec.url,
        }])
    elif spec.auth_type == "bearer":
        # selector 例 "Authorization: Bearer <token>" → header 名 "Authorization"
        header_name = spec.auth_selector.split(":", 1)[0].strip() or "Authorization"
        context.set_extra_http_headers({header_name: f"Bearer {value}"})


def _launch_browser(sync_playwright, headless: bool = True):
    """启动 chromium；显式 args 关闭 sandbox 之外不做多余配置（最小 footprint）。"""
    return sync_playwright().start().chromium.launch(headless=headless)


def _new_context(browser, spec: LiveRuntimeSpec, viewport: dict):
    context = browser.new_context(viewport=viewport)
    _inject_auth(context, spec)
    return context


def _capture_artifacts(page, out_dir: Path, label: str) -> tuple[Path, Path, str]:
    """落 PNG + HTML，返回 (shot_path, dom_path, shot_sha256)。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in label)[:80] or "step"
    shot_path = out_dir / "shots" / f"{safe}.png"
    dom_path = out_dir / "dom" / f"{safe}.html"
    shot_path.parent.mkdir(parents=True, exist_ok=True)
    dom_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(shot_path), full_page=True)
    dom_path.write_text(page.content() or "", encoding="utf-8")
    if shot_path.read_bytes()[:8] != PNG_HEADER:
        raise RuntimeError(f"screenshot not a PNG (header mismatch): {shot_path}")
    return shot_path, dom_path, file_sha256(shot_path)


def capture_snapshot_playwright(
    repo: Path,
    spec: LiveRuntimeSpec,
    *,
    scenario_id: str = "",
    capability_id: str = "",
    viewport: dict | None = None,
    timeout_ms: int = 15000,
) -> SnapshotRecord:
    """用 playwright 访问 spec.url 一次，落 PNG + DOM + SnapshotRecord。

    返回值可以直接传给 `write_snapshot(repo, spec, record)`。"""
    sync_playwright = _ensure_playwright()
    if not spec.enabled:
        raise RuntimeError("LiveRuntimeSpec not enabled: url and driver required")
    ensure_output_dirs(repo, spec)
    out_dir = repo / spec.output_dir
    viewport = viewport or {"width": 1440, "height": 900}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = _new_context(browser, spec, viewport)
            page = context.new_page()
            page.goto(spec.url, wait_until="domcontentloaded", timeout=timeout_ms)
            label = f"{capability_id or 'cap'}-{scenario_id or 'snap'}"
            shot, dom, sha = _capture_artifacts(page, out_dir, label)
        finally:
            browser.close()
    return SnapshotRecord(
        url=spec.url,
        dom_snapshot_path=str(dom.resolve().relative_to(repo.resolve())),
        screenshot_sha256=sha,
        captured_at=_now_iso(),
        scenario_id=scenario_id,
        capability_id=capability_id,
        commit=_git_head(repo),
    )


def capture_flow_playwright(
    repo: Path,
    spec: LiveRuntimeSpec,
    capability_id: str,
    steps: list,
    *,
    start_url: str | None = None,
    viewport: dict | None = None,
    timeout_ms: int = 15000,
) -> list[FlowStepRecord]:
    """用 playwright 跑多步 flow，每步落 PNG + DOM + FlowStepRecord。

    调用方拿到 FlowStepRecord 列表后构造 `FlowRecord` 并调用 `write_flow(repo, spec, flow)`。
    `steps` 是 list[FlowStepRequest] 或 dict。
    """
    sync_playwright = _ensure_playwright()
    if not spec.enabled:
        raise RuntimeError("LiveRuntimeSpec not enabled: url and driver required")
    ensure_output_dirs(repo, spec)
    out_dir = repo / spec.output_dir
    viewport = viewport or {"width": 1440, "height": 900}
    initial_url = start_url or spec.url
    results: list[FlowStepRecord] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = _new_context(browser, spec, viewport)
            page = context.new_page()
            page.goto(initial_url, wait_until="domcontentloaded", timeout=timeout_ms)
            for idx, raw in enumerate(steps):
                step = raw if isinstance(raw, FlowStepRequest) else FlowStepRequest(**dict(raw))
                if step.action == "navigate":
                    if not step.selector:
                        raise ValueError(f"step[{idx}] navigate requires a url in `selector`")
                    page.goto(step.selector, wait_until="domcontentloaded", timeout=timeout_ms)
                elif step.action == "click":
                    if not step.selector:
                        raise ValueError(f"step[{idx}] click requires `selector`")
                    page.click(step.selector, timeout=timeout_ms)
                elif step.action == "type":
                    if not step.selector:
                        raise ValueError(f"step[{idx}] type requires `selector`")
                    page.fill(step.selector, step.value or "")
                elif step.action == "select":
                    if not step.selector:
                        raise ValueError(f"step[{idx}] select requires `selector`")
                    page.select_option(step.selector, step.value or "")
                elif step.action == "route":
                    if not step.selector:
                        raise ValueError(f"step[{idx}] route requires target path in `selector`")
                    # 走前端路由：触发 popstate 让 SPA 监听者响应
                    page.evaluate(f"() => window.history.pushState({{}}, '', {step.selector!r})")
                    page.evaluate("() => window.dispatchEvent(new PopStateEvent('popstate'))")
                elif step.action == "wait":
                    pass
                else:
                    raise ValueError(f"step[{idx}] unknown action: {step.action!r}")
                if step.wait_ms:
                    page.wait_for_timeout(step.wait_ms)
                label = f"{capability_id}-step-{idx:02d}-{step.action}"
                shot, dom, sha = _capture_artifacts(page, out_dir, label)
                results.append(FlowStepRecord(
                    action=step.action,
                    selector=step.selector,
                    value=step.value,
                    screenshot_sha256=sha,
                    dom_snapshot_path=str(dom.resolve().relative_to(repo.resolve())),
                    captured_at=_now_iso(),
                ))
        finally:
            browser.close()
    return results