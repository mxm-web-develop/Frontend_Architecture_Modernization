# AI Coding Governance

## Goal: a self-describing repository

A fresh AI agent should be able to operate without previous chat history.

It must discover:

- project purpose;
- current architecture;
- domain boundaries;
- allowed/forbidden dependencies;
- canonical commands;
- where new code belongs;
- required checks;
- migration state;
- baseline legacy commit;
- current unknowns/remediation backlog.

## Context hierarchy

Use:

1. short scoped `AGENTS.md`;
2. `governance/*` machine truth;
3. active architecture/ADR docs;
4. domain manifests;
5. migration facts/evidence;
6. generated human reports.

Do not encode all architecture details in one giant AGENTS.md.

## Canonical-source rule

Avoid manual duplication across:

- AGENTS.md;
- Cursor rules;
- README files;
- manifests;
- architecture docs.

Select one canonical source and reference or generate secondary tool adapters.

## Recommended governance files

```text
governance/
  project.yaml
  architecture.yaml
  domains.yaml
  dependency-rules.yaml
  quality-gates.yaml
  commands.yaml
  docs-index.yaml
```

## Domain manifest

Each Domain Application should expose machine-readable facts:

```yaml
id: users
type: domain-application

runtime:
  standalone: true
  embedded: true

dependencies:
  allowed:
    - design-system
    - platform-http
  forbidden:
    - domain-models
```

## AI Definition of Done

An agent change is incomplete if it updates code but leaves relevant:

- tests;
- migration ledger;
- architecture metadata;
- docs;
- evidence

stale.

## Tool-specific adapters

Cursor rules can provide path-scoped reminders. Codex AGENTS files can provide
scoped project instructions.

Neither should become a second architecture database.
