# Frontend Architecture Modernization

A Skill for reconstructing an **existing frontend product into a new repository** while preserving legacy behavior and producing a repository that downstream agents can continue developing.

> This Skill is not intended for implementing net-new product requirements.

## 1. Install

### Requirements

Check that Git, Node.js, and Python are available:

```bash
git --version
node --version
python --version
```

Recommended:

- Git
- Node.js 20+
- Python 3.10+
- read access to the Legacy repository
- write access to the Target repository

Visual comparison also requires Playwright / Chromium.

### Folder name

The Skill folder must be named exactly:

```text
frontend-architecture-modernization
```

If the extracted folder has a suffix, run:

```bash
python <skill-path>/scripts/modernize.py doctor --fix-install-name
```

### Install into your Agent Skill directory

Place the complete folder under the Skill directory used by your Agent runtime:

```text
<agent-skills-root>/
└── frontend-architecture-modernization/
```

### Verify

```bash
python <skill-path>/scripts/modernize.py doctor
```

For an existing Target repository:

```bash
python <skill-path>/scripts/modernize.py doctor --repo <target-repo>
```

### Optional engine dependencies

Analyzer:

```bash
python <skill-path>/scripts/modernize.py install-engine --analyzer
```

Visual tools:

```bash
python <skill-path>/scripts/modernize.py install-engine --visual
```

Visual tools plus Chromium:

```bash
python <skill-path>/scripts/modernize.py install-engine --visual --install-browser
```

---

## 2. Quick Start

Assume:

```text
legacy-app/
target-app/
```

Initialize:

```bash
python <skill-path>/scripts/modernize.py bootstrap \
  --legacy ../legacy-app \
  --target ../target-app
```

Analyze:

```bash
python <skill-path>/scripts/modernize.py analyze --repo ../target-app
```

Assess:

```bash
python <skill-path>/scripts/modernize.py assess --repo ../target-app
```

Generate human-facing modernization documentation:

```bash
python <skill-path>/scripts/modernize.py report system --repo ../target-app
```

Start with:

```text
docs/modernization/project-overview.md
docs/modernization/architecture-modernization-plan.md
docs/modernization/progress.md
```

Check status:

```bash
python <skill-path>/scripts/modernize.py status --repo ../target-app
```

---

## 3. Use

In an Agent that supports this Skill, normal natural-language requests are preferred:

```text
Analyze this legacy frontend first. Do not write code yet.
```

```text
Continue the modernization work from the repository state.
```

```text
Show the current UNKNOWNs and incomplete discovery areas.
```

```text
Recommend a framework strategy, but do not confirm it yet.
```

```text
I confirm the framework choice. Continue.
```

```text
Analyze the capabilities that belong to the hall domain.
```

```text
Start modernizing the hall domain.
```

```text
Verify functional, visual, architecture, and traceability evidence.
```

```text
Generate the latest system report.
```

The Skill resumes from repository facts rather than depending on chat history.

---

## 4. Common Commands

Doctor:

```bash
python <skill-path>/scripts/modernize.py doctor --repo <target-repo>
```

Status:

```bash
python <skill-path>/scripts/modernize.py status --repo <target-repo>
```

Improve human-facing project/business labels:

```bash
python <skill-path>/scripts/modernize.py docs label hall "Model Hall" --repo <target-repo>
python <skill-path>/scripts/modernize.py docs set-project --name "TokenHub" --repo <target-repo>
python <skill-path>/scripts/modernize.py docs build --repo <target-repo>
```

Analyze:

```bash
python <skill-path>/scripts/modernize.py analyze --repo <target-repo>
```

Assess:

```bash
python <skill-path>/scripts/modernize.py assess --repo <target-repo>
```

Human documentation and technical appendix:

```bash
python <skill-path>/scripts/modernize.py report system --repo <target-repo>
```

Human documentation only:

```bash
python <skill-path>/scripts/modernize.py report human --repo <target-repo>
```

Machine technical appendix only:

```bash
python <skill-path>/scripts/modernize.py report machine --repo <target-repo>
```

Framework recommendation:

```bash
python <skill-path>/scripts/modernize.py framework recommend --repo <target-repo>
```

Create a confirmed Domain:

```bash
python <skill-path>/scripts/modernize.py domain create <domain-id> \
  --candidate <MOD-CAND-ID> \
  --repo <target-repo>
```

Validation:

```bash
python <skill-path>/scripts/modernize.py validate --structure --repo <target-repo>
python <skill-path>/scripts/modernize.py validate --state --repo <target-repo>
python <skill-path>/scripts/modernize.py validate --completeness --repo <target-repo>
python <skill-path>/scripts/modernize.py validate --all --repo <target-repo>
```

Build handoff:

```bash
python <skill-path>/scripts/modernize.py handoff build --repo <target-repo>
```

For additional command options:

```bash
python <skill-path>/scripts/modernize.py --help
```

---

## 5. Update

Project state is stored in the Target repository. Keep:

```text
AGENTS.md
governance/
migration/
handoff/
.modernization.json
```

### Before updating

Commit or back up current project state:

```bash
git status
git add .
git commit -m "chore: checkpoint modernization state"
```

### Replace the installed Skill

Remove or move the old Skill installation and replace it with the complete new folder named:

```text
frontend-architecture-modernization/
```

Avoid mixing individual files from different Skill versions.

### Verify

```bash
python <skill-path>/scripts/modernize.py doctor --repo <target-repo>
```

### Upgrade an existing project control plane

When required:

```bash
python <skill-path>/scripts/modernize.py upgrade-control-plane --repo <target-repo>
```

Then verify:

```bash
python <skill-path>/scripts/modernize.py validate --structure --repo <target-repo>
```

Review the Git diff before continuing.

---

## 6. Uninstall

Delete the installed Skill folder:

```text
frontend-architecture-modernization/
```

This does not require deleting the modernized Target repository.

Normally keep:

```text
AGENTS.md
governance/
migration/
handoff/
.modernization.json
```

These are project knowledge and handoff artifacts.

Only delete them if you intentionally want to remove the modernization governance records from the project.

---

## 7. FAQ

### The Skill folder name is invalid

Run:

```bash
python <skill-path>/scripts/modernize.py doctor --fix-install-name
```

### Does the Skill modify the Legacy repository?

The normal workflow treats Legacy as the read-only product truth source. Writes happen in the Target repository.

### Can I use this Skill to implement a new feature?

No. Finish modernization and handoff first, then use a normal product-development Agent or Skill.

### Why are some findings UNKNOWN?

UNKNOWN means the available static/runtime evidence is insufficient. Add evidence or perform semantic review instead of guessing.

### Will updating the Skill lose project progress?

Normally no. Project state lives in the Target repository, not in the installed Skill folder.
