# Frontend Architecture Modernization

这是一个用于将**已有前端项目重构到新仓库**的 Skill。

它负责分析旧项目、恢复已有功能、建立现代化项目治理结构、协助迁移与验证，并最终产出可交接给其他 Agent 继续开发的新仓库。

> 本 Skill 不用于开发全新的产品需求。

## 1. 安装

### 1.1 前置要求

请确保本机已经安装：

```bash
git --version
node --version
python --version
```

建议：

- Git
- Node.js 20+
- Python 3.10+
- 可正常读写 Legacy 仓库和 Target 仓库

如果需要运行视觉对比，还需要安装 Playwright / Chromium。

### 1.2 安装目录

Skill 文件夹必须精确命名为：

```text
frontend-architecture-modernization
```

不要使用：

```text
frontend-architecture-modernization 2
frontend-architecture-modernization 7
frontend-architecture-modernization-copy
```

如果下载或解压后目录名带后缀，可以运行：

```bash
python <skill-path>/scripts/modernize.py doctor --fix-install-name
```

如果目标规范目录已经存在，Skill 不会自动覆盖，需要手工处理。

### 1.3 放到 Agent Skill 目录

将整个文件夹放到你的 Agent 支持的 Skill 目录中。

例如：

```text
<agent-skills-root>/
└── frontend-architecture-modernization/
```

具体 Skill 根目录由 Codex、Cursor 或你的 Agent Runtime 决定。

### 1.4 检查安装

执行：

```bash
python <skill-path>/scripts/modernize.py doctor
```

如果已经有 Target 仓库：

```bash
python <skill-path>/scripts/modernize.py doctor --repo <target-repo>
```

看到关键检查项为 `PASS` 后再开始使用。

### 1.5 安装分析 / 视觉依赖

安装 Analyzer 依赖：

```bash
python <skill-path>/scripts/modernize.py install-engine --analyzer
```

安装视觉工具：

```bash
python <skill-path>/scripts/modernize.py install-engine --visual
```

同时安装 Chromium：

```bash
python <skill-path>/scripts/modernize.py install-engine --visual --install-browser
```

---

## 2. 快速开始

假设：

```text
legacy-app/
target-app/
```

其中：

- `legacy-app`：旧项目，只作为迁移事实来源
- `target-app`：新仓库

### 2.1 初始化

```bash
python <skill-path>/scripts/modernize.py bootstrap \
  --legacy ../legacy-app \
  --target ../target-app \
  --human-language zh-CN
```

初始化完成后，Target 仓库会生成治理、迁移状态和文档目录。

### 2.2 分析旧项目

```bash
python <skill-path>/scripts/modernize.py analyze \
  --repo ../target-app
```

### 2.3 做架构评估

```bash
python <skill-path>/scripts/modernize.py assess \
  --repo ../target-app
```

### 2.4 生成当前项目报告

```bash
python <skill-path>/scripts/modernize.py report system \
  --repo ../target-app
```

### 2.5 查看状态

```bash
python <skill-path>/scripts/modernize.py status \
  --repo ../target-app
```

---

## 3. 日常使用

通常不需要手工记忆完整流程。

在支持 Skill 的 Agent 中，可以直接用自然语言描述你的目标，例如：

```text
分析这个旧前端项目，先不要写代码。
```

```text
继续这个项目的架构现代化工作。
```

```text
检查当前已经分析到什么程度，还有哪些 UNKNOWN。
```

```text
给出当前框架策略建议，但先不要确认。
```

```text
我确认保留 Vue3，继续下一步。
```

```text
分析 hall 这个业务模块应该包含哪些能力。
```

```text
开始迁移 hall 模块。
```

```text
检查 hall 的功能、视觉和架构是否已经通过。
```

```text
生成最新的系统报告。
```

Skill 会根据仓库中的治理文件和状态继续工作，而不是依赖聊天历史。

---

## 4. 常用命令

### 检查环境

```bash
python <skill-path>/scripts/modernize.py doctor --repo <target-repo>
```

### 查看状态

```bash
python <skill-path>/scripts/modernize.py status --repo <target-repo>
```

### 分析 Legacy

```bash
python <skill-path>/scripts/modernize.py analyze --repo <target-repo>
```

### 架构评估

```bash
python <skill-path>/scripts/modernize.py assess --repo <target-repo>
```

### 生成系统报告

```bash
python <skill-path>/scripts/modernize.py report system --repo <target-repo>
```

### 框架推荐

```bash
python <skill-path>/scripts/modernize.py framework recommend --repo <target-repo>
```

### 创建确认后的 Domain

```bash
python <skill-path>/scripts/modernize.py domain create <domain-id> \
  --candidate <MOD-CAND-ID> \
  --repo <target-repo>
```

### 查看 Domain

```bash
python <skill-path>/scripts/modernize.py domain list --repo <target-repo>
```

### 校验文件结构

```bash
python <skill-path>/scripts/modernize.py validate \
  --structure \
  --repo <target-repo>
```

### 校验当前状态

```bash
python <skill-path>/scripts/modernize.py validate \
  --state \
  --repo <target-repo>
```

### 校验发现完整度

```bash
python <skill-path>/scripts/modernize.py validate \
  --completeness \
  --repo <target-repo>
```

### 完整校验

```bash
python <skill-path>/scripts/modernize.py validate \
  --all \
  --repo <target-repo>
```

### 运行质量检查并保存 Evidence

```bash
python <skill-path>/scripts/modernize.py run-check functional <domain> \
  --command-key test \
  --repo <target-repo>
```

### 查看 / 执行视觉验证

```bash
python <skill-path>/scripts/modernize.py visual --help
```

### 同步 Legacy 变化

```bash
python <skill-path>/scripts/modernize.py sync --help
```

### 构建交接包

```bash
python <skill-path>/scripts/modernize.py handoff build \
  --repo <target-repo>
```

---

## 5. 更新 Skill

更新 Skill 时，建议保留项目仓库中的：

```text
governance/
migration/
handoff/
AGENTS.md
.modernization.json
```

这些属于项目本身的持续状态，不应该因为更新 Skill 被删除。

### 5.1 更新前备份

建议先提交当前项目：

```bash
git status
git add .
git commit -m "chore: checkpoint modernization state"
```

### 5.2 替换 Skill 文件夹

删除或移走旧的 Skill 安装目录，然后把新版本完整解压到：

```text
frontend-architecture-modernization/
```

不要把新文件直接零散覆盖到旧 Skill 目录。

### 5.3 检查更新结果

```bash
python <skill-path>/scripts/modernize.py doctor \
  --repo <target-repo>
```

### 5.4 升级已有项目控制面

如果新版本要求升级项目治理结构，可以运行：

```bash
python <skill-path>/scripts/modernize.py upgrade-control-plane \
  --repo <target-repo>
```

执行后再次校验：

```bash
python <skill-path>/scripts/modernize.py validate \
  --structure \
  --repo <target-repo>
```

建议在升级后查看 Git Diff，再继续工作。

---

## 6. 卸载

卸载 Skill 不需要删除已经现代化的项目。

### 6.1 删除 Skill 安装目录

删除：

```text
frontend-architecture-modernization/
```

即可停止使用该 Skill。

### 6.2 不要删除项目治理文件

正常情况下请保留 Target 仓库中的：

```text
AGENTS.md
governance/
migration/
handoff/
.modernization.json
```

这些文件属于项目本身，是后续 Agent 和开发流程的重要上下文。

### 6.3 如果要彻底移除现代化治理

只有确定项目以后完全不需要这些治理信息时，才考虑手工删除：

```text
governance/
migration/
handoff/
.modernization.json
```

删除前建议先提交或备份。

---

## 7. 常见问题

### Doctor 提示 Skill 文件夹名错误

运行：

```bash
python <skill-path>/scripts/modernize.py doctor --fix-install-name
```

或者手工改成：

```text
frontend-architecture-modernization
```

### Legacy 仓库会被修改吗？

正常流程中 Legacy 仓库作为只读事实来源。

Target 新仓库才是现代化代码和治理文件的写入位置。

### 可以直接在这个 Skill 里开发新需求吗？

不建议。

这个 Skill 的职责是复现 Legacy 已有功能并完成架构现代化。

新需求应在项目进入 Handoff 后，由普通产品开发 Agent / Skill 接手。

### 为什么有些分析结果是 UNKNOWN？

UNKNOWN 表示当前静态分析或已有证据不足。

不要把 UNKNOWN 当成失败，也不要擅自猜测。需要补充静态分析、运行时证据或人工语义确认。

### 为什么有些 Domain Candidate 不能直接确认？

有些结果只是代码结构线索，例如：

```text
src/config
src/data
src/lib
src/types
src/requests
```

它们不一定是业务 Domain。

只有满足 Skill 规则的 Candidate 才可以进入 Domain 确认流程。

### 更新 Skill 会丢失迁移进度吗？

只要不删除 Target 仓库中的治理和迁移状态文件，正常不会。

Skill 本身是执行工具；项目事实保存在 Target Repository。
