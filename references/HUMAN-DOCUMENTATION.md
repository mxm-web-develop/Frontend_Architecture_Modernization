# Human Documentation Standard

Human-readable modernization documents are a separate projection of Machine Truth.

## Three layers

```text
Machine Truth
→ Semantic Synthesis
→ Human Documentation
```

Machine Truth remains authoritative for stable IDs, enums, confidence levels, evidence,
source hashes, routes, APIs, dependency edges and gate state.

`migration/system/semantic-synthesis.yaml` groups and translates those facts into
business areas, architecture concerns, human state labels, implementation priorities,
and unresolved questions.

Human documentation lives under:

```text
docs/modernization/
├── README.md
├── project-overview.md
├── architecture-modernization-plan.md
├── progress.md
├── technical-analysis.md
└── domains/
```

## Primary human documents

### Project overview

Must answer:

- What system is this?
- What technology is currently in use?
- What major business areas are understood so far?
- What are the largest architecture/code problems?
- What remains uncertain?

### Architecture modernization plan

Must answer:

- What is the modernization goal?
- What is stable globally?
- What is refined incrementally per Domain?
- What should be implemented first and why?
- What must be re-checked in Legacy before each Domain starts?
- What is the completion standard?

### Domain guide

Must answer:

- What product responsibility does this Domain own?
- What approved capabilities exist?
- What Legacy evidence must be revisited?
- What is the target design status?
- What are the implementation and verification steps?

Stable IDs may appear only in the technical-evidence section.

### Progress

Must translate project/domain state into natural language and state the next action.

## Forbidden primary-text output

Primary human documents must not render raw values such as:

```text
None
null
CAP-CAND-001
MOD-CAND-009
REM-001
ARCHITECTURE_ASSESSED
STATIC_INFERRED
```

These belong in Machine Truth or technical appendices.

A missing value must be translated by field semantics, for example:

- no state library detected → “未发现明确全局状态管理方案”
- framework not selected → “目标框架尚未由用户确认”
- score unavailable → “当前证据不足，暂不评分”

## Technical appendix

The 18-section static report is retained as:

```text
migration/system/machine-analysis-report.md
```

It is a technical appendix, not the primary modernization plan.

The historical path `migration/system/migration-master-report.md` is a compatibility
bridge that points human readers to `docs/modernization/`.
